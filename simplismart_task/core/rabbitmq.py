import pika
import json
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.setup_connection()

    def setup_connection(self):
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
            
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host='localhost',
                    port=5672,
                    virtual_host='/',
                    credentials=pika.PlainCredentials('guest', 'guest'),
                    connection_attempts=5,
                    retry_delay=1,
                    socket_timeout=5,
                    heartbeat=60,
                    blocked_connection_timeout=30
                )
            )
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(
                exchange='deployments',
                exchange_type='direct',
                durable=True
            )
            
            self.channel.queue_declare(
                queue='deployments',
                durable=True,
                arguments={
                    'x-message-ttl': 60000,
                    'x-dead-letter-exchange': 'deployments.dlx'
                }
            )
            
            self.channel.queue_bind(
                exchange='deployments',
                queue='deployments',
                routing_key='deployment'
            )
            
            logger.info("RabbitMQ connection established successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ connection: {str(e)}")
            return False

    def ensure_connection(self):
        if not self.connection or not self.connection.is_open:
            logger.warning("RabbitMQ connection lost. Attempting to reconnect...")
            return self.setup_connection()
        return True

    def publish_deployment(self, deployment_data):
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return False
                
                self.channel.basic_publish(
                    exchange='deployments',
                    routing_key='deployment',
                    body=json.dumps(deployment_data),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                    )
                )
                logger.info(f"Successfully published deployment: {deployment_data.get('id')}")
                return True
            except pika.exceptions.AMQPChannelError as e:
                logger.error(f"Channel error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Connection error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False
            except Exception as e:
                logger.error(f"Error publishing to RabbitMQ: {str(e)}")
                return False

    def close(self):
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")

rabbitmq_publisher = RabbitMQPublisher() 