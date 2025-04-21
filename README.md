# SimpliSmart Task Management System

A distributed system for managing task deployments across clusters, consisting of a Django backend and a FastAPI consumer service.

## System Architecture

The system consists of three main components:

1. **Django Backend (Port 8000)**
   - REST API for cluster and deployment management
   - User authentication and authorization
   - Resource allocation tracking

2. **FastAPI Consumer (Port 8001)**
   - Processes deployment requests from the queue
   - Manages resource allocation
   - Provides deployment status updates

3. **RabbitMQ Message Broker (Port 5672)**
   - Handles message queueing between services
   - Management UI available at port 15672

## Prerequisites

- Docker and Docker Compose
- Python 3.11 (for local development)
- Git

## Directory Structure

```
project/
├── simplismart_task/          # Django backend
│   ├── core/                  # Core application
│   ├── simplismart_task/      # Project settings
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
└── consumer/                  # FastAPI consumer
    ├── app/                   # Application code
    ├── Dockerfile
    └── requirements.txt
```

## Setup and Installation

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Build and start the containers:
   ```bash
   cd simplismart_task
   docker-compose up --build
   ```

3. Run migrations (in a new terminal):
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Local Development Setup

1. Set up the Django backend:
   ```bash
   cd simplismart_task
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsuperuser
   ```

2. Set up the consumer service:
   ```bash
   cd ../consumer
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the Services

### Using Docker

The services will be available at:
- Django API: http://localhost:8000
- Consumer API: http://localhost:8001
- RabbitMQ Management: http://localhost:15672 (credentials: guest/guest)

### Local Development

1. Start the Django backend:
   ```bash
   cd simplismart_task
   source venv/bin/activate
   python manage.py runserver
   ```

2. Start the consumer service:
   ```bash
   cd ../consumer
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8001
   ```

3. Start RabbitMQ (using Docker):
   ```bash
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
   ```

## API Documentation

### Django Backend (http://localhost:8000)

- API Root: http://localhost:8000/api/
- API Documentation: http://localhost:8000/api/docs/
- Available endpoints:
  - `/api/users/` - User management
  - `/api/token/` - JWT token authentication
  - `/api/clusters/` - Cluster management
  - `/api/clusters/{id}/use_resources/` - Resource allocation
  - `/api/clusters/{id}/resources/` - Resource status

### Consumer Service (http://localhost:8001)

- API Documentation: http://localhost:8001/docs
- Available endpoints:
  - `/deployments/` - List all deployments
  - `/deployments/{id}` - Get specific deployment
  - `/health` - Health check

## Testing

### Django Backend Tests

```bash
cd simplismart_task
python manage.py test core.tests
```

### Consumer Service Tests

```bash
cd consumer
python -m pytest
```

## Environment Variables

### Django Backend
- `DJANGO_SETTINGS_MODULE=simplismart_task.settings`
- `RABBITMQ_HOST=rabbitmq`
- `RABBITMQ_PORT=5672`
- `RABBITMQ_USER=guest`
- `RABBITMQ_PASSWORD=guest`

### Consumer Service
- `RABBITMQ_HOST=rabbitmq`
- `RABBITMQ_PORT=5672`
- `RABBITMQ_USER=guest`
- `RABBITMQ_PASSWORD=guest`

## Troubleshooting

1. **RabbitMQ Connection Issues**
   - Check if RabbitMQ container is running
   - Verify credentials in environment variables
   - Check network connectivity between services

2. **Database Migration Issues**
   - Delete existing migrations and database
   - Run `python manage.py makemigrations`
   - Run `python manage.py migrate`

3. **Service Communication Issues**
   - Verify all services are running
   - Check port mappings
   - Verify environment variables

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

## UML Diagram

![]{simplismart_task.png}