from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pika
import json
import asyncio
from typing import Dict, Any
import logging
import signal
import sys
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Deployment Consumer API")

class Deployment(BaseModel):
    id: int
    name: str
    cluster: int
    docker_image: str
    required_cpu: float
    required_ram: float
    required_gpu: float
    status: str
    created_at: str
    updated_at: str


received_deployments: Dict[int, Deployment] = {}

connection = None
channel = None
is_consuming = False

def process_deployment(ch, method, properties, body):
    try:
        deployment_data = json.loads(body)
        deployment = Deployment(**deployment_data)
        received_deployments[deployment.id] = deployment
        logger.info(f"Processed deployment: {deployment.name}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error(f"Error processing deployment: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag)

def setup_rabbitmq():
    global connection, channel, is_consuming
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            if connection and connection.is_open:
                connection.close()
            
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(
                host='localhost',
                port=5672,
                virtual_host='/',
                credentials=credentials,
                connection_attempts=5,
                retry_delay=1,
                socket_timeout=5,
                heartbeat=60,
                blocked_connection_timeout=30
            )
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            try:
                channel.exchange_delete(exchange='deployments')
                logger.info("Deleted existing exchange 'deployments'")
            except pika.exceptions.ChannelClosedByBroker:
                logger.info("Exchange 'deployments' does not exist or could not be deleted")
            
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange='deployments',
                exchange_type='direct',
                durable=True
            )
            
            try:
                channel.queue_delete(queue='deployments')
                logger.info("Deleted existing queue 'deployments'")
            except pika.exceptions.ChannelClosedByBroker:
                logger.info("Queue 'deployments' does not exist or could not be deleted")
            
            channel = connection.channel()
            
            channel.queue_declare(
                queue='deployments',
                durable=True,
                arguments={
                    'x-message-ttl': 60000,
                    'x-dead-letter-exchange': 'deployments.dlx'
                }
            )
            
            channel.exchange_declare(
                exchange='deployments.dlx',
                exchange_type='direct',
                durable=True
            )
            
            channel.queue_declare(
                queue='deployments.dlq',
                durable=True
            )
            
            channel.queue_bind(
                exchange='deployments.dlx',
                queue='deployments.dlq',
                routing_key='deployment'
            )
            
            channel.queue_bind(
                exchange='deployments',
                queue='deployments',
                routing_key='deployment'
            )
            
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue='deployments',
                on_message_callback=process_deployment,
                auto_ack=False
            )
            
            is_consuming = True
            logger.info("RabbitMQ connection established successfully")
            return True
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Could not establish RabbitMQ connection.")
                return False
        except Exception as e:
            logger.error(f"Unexpected error during RabbitMQ setup: {str(e)}")
            return False

def close_rabbitmq():
    global connection, channel, is_consuming
    try:
        is_consuming = False
        if channel and channel.is_open:
            try:
                channel.close()
            except pika.exceptions.ConnectionWrongStateError:
                logger.warning("Channel was already closed")
            except Exception as e:
                logger.error(f"Error closing channel: {str(e)}")
        
        if connection and connection.is_open:
            try:
                connection.close()
            except pika.exceptions.ConnectionWrongStateError:
                logger.warning("Connection was already closed")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
        
        connection = None
        channel = None
        logger.info("RabbitMQ connection closed")
    except Exception as e:
        logger.error(f"Error in close_rabbitmq: {str(e)}")

def signal_handler(sig, frame):
    logger.info("Shutting down...")
    try:
        close_rabbitmq()
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
    finally:
        sys.exit(0)

@app.on_event("startup")
async def startup_event():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if setup_rabbitmq():
        asyncio.create_task(run_consumer())
    else:
        logger.error("Failed to start RabbitMQ consumer")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        close_rabbitmq()
    except Exception as e:
        logger.error(f"Error during shutdown event: {str(e)}")

async def run_consumer():
    global is_consuming, connection, channel
    while is_consuming:
        try:
            if not connection or not connection.is_open:
                logger.warning("RabbitMQ connection lost. Attempting to reconnect...")
                if not setup_rabbitmq():
                    logger.error("Failed to reconnect to RabbitMQ")
                    break
            
            try:
                channel.start_consuming()
            except pika.exceptions.ConnectionClosedByBroker:
                logger.error("Connection closed by broker. Attempting to reconnect...")
                time.sleep(2)
                continue
            except pika.exceptions.AMQPChannelError as err:
                logger.error(f"Channel error: {str(err)}. Attempting to reconnect...")
                time.sleep(2)
                continue
            except pika.exceptions.AMQPConnectionError:
                logger.error("Connection error. Attempting to reconnect...")
                time.sleep(2)
                continue
            except pika.exceptions.ConnectionWrongStateError:
                logger.warning("Connection in wrong state. Attempting to reconnect...")
                close_rabbitmq()
                time.sleep(2)
                continue
        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")
            break

@app.get("/deployments/", response_model=list[Deployment])
async def get_deployments():
    return list(received_deployments.values())

@app.get("/deployments/{deployment_id}", response_model=Deployment)
async def get_deployment(deployment_id: int):
    if deployment_id not in received_deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return received_deployments[deployment_id]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "rabbitmq_connected": connection.is_open if connection else False
    } 