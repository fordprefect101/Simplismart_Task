# Deployment Consumer Service

This service listens to deployment messages from RabbitMQ and provides an API to access the received deployments.

## Features

- Listens to deployment messages from RabbitMQ
- Stores received deployments in memory
- Provides REST API endpoints to access deployments
- Health check endpoint
- Docker and Docker Compose support

## API Endpoints

- `GET /deployments/` - List all received deployments
- `GET /deployments/{deployment_id}` - Get a specific deployment
- `GET /health` - Health check endpoint

## Running the Service

### Using Docker Compose

1. Build and start the services:
   ```bash
   docker-compose up --build
   ```

2. Access the services:
   - Consumer API: http://localhost:8001
   - RabbitMQ Management UI: http://localhost:15672 (credentials: guest/guest)

### Manual Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the service:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## Environment Variables

- `RABBITMQ_HOST` - RabbitMQ host (default: localhost)
- `RABBITMQ_PORT` - RabbitMQ port (default: 5672)

## Testing

1. Start the service
2. Create a deployment in the main application
3. Check the consumer API to see the received deployment:
   ```bash
   curl http://localhost:8001/deployments/
   ```

## Notes

- The service stores deployments in memory and will lose data on restart
- Make sure RabbitMQ is running before starting the service
- The service automatically reconnects to RabbitMQ if the connection is lost 