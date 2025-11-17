# Resonant Dashboard Backend API

FastAPI backend for the Resonant Dashboard system.

## Features

- RESTful API for Messages, Specifications, Intents, and Notifications
- PostgreSQL database with asyncpg
- Swagger UI auto-documentation
- CORS support for frontend integration
- Logging middleware

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (via Docker Compose from Sprint 1)

### Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment file
cp ../docker/.env .env
# Edit .env if needed (e.g., POSTGRES_HOST=localhost)
```

### Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

### API Documentation

Open http://localhost:8000/docs for Swagger UI

## API Endpoints

### Messages
- `GET /api/messages` - List messages
- `GET /api/messages/{id}` - Get message
- `POST /api/messages` - Create message
- `PUT /api/messages/{id}` - Update message
- `DELETE /api/messages/{id}` - Delete message

### Specifications
- `GET /api/specifications` - List specifications
- `GET /api/specifications/{id}` - Get specification
- `POST /api/specifications` - Create specification
- `PUT /api/specifications/{id}` - Update specification
- `DELETE /api/specifications/{id}` - Delete specification

### Intents
- `GET /api/intents` - List intents
- `GET /api/intents/{id}` - Get intent
- `POST /api/intents` - Create intent
- `PUT /api/intents/{id}` - Update intent
- `PATCH /api/intents/{id}/status` - Update intent status
- `DELETE /api/intents/{id}` - Delete intent

### Notifications
- `GET /api/notifications` - List notifications
- `GET /api/notifications/{id}` - Get notification
- `POST /api/notifications` - Create notification
- `POST /api/notifications/mark-read` - Mark as read
- `DELETE /api/notifications/{id}` - Delete notification

## Docker Integration

The backend is integrated into the Docker Compose setup:

```bash
cd docker
docker-compose up --build -d
```

## Testing

```bash
cd backend
source venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

---

**Sprint 2 of PostgreSQL Dashboard System**
