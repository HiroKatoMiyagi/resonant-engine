# Intent Bridge Daemon

Automated Intent processing daemon using PostgreSQL LISTEN/NOTIFY.

## Features

- Real-time Intent detection via LISTEN/NOTIFY
- Automatic status updates
- Claude API integration (optional)
- Notification generation
- Error handling and retry logic

## How It Works

1. User creates Intent via Dashboard
2. PostgreSQL trigger fires `intent_created` notification
3. Intent Bridge daemon receives notification instantly
4. Daemon processes Intent (calls Claude API if configured)
5. Results saved to database
6. Notification generated for user

## Quick Start

### Prerequisites

- PostgreSQL running (with triggers)
- Python 3.11+
- Optional: Anthropic API key

### Setup

```bash
cd intent_bridge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=resonant
POSTGRES_PASSWORD=your_password
POSTGRES_DB=resonant_dashboard
ANTHROPIC_API_KEY=optional_api_key
EOF
```

### Apply Database Triggers

```bash
cd docker
docker-compose exec postgres psql -U resonant -d resonant_dashboard \
  -f /docker-entrypoint-initdb.d/002_intent_notify.sql
```

### Run Daemon

```bash
python main.py
```

## Docker Integration

The daemon runs as a separate container:

```bash
cd docker
docker-compose up --build -d
```

## Configuration

Environment variables:
- `POSTGRES_HOST` - Database host
- `POSTGRES_PORT` - Database port
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DB` - Database name
- `ANTHROPIC_API_KEY` - Optional Claude API key

## Testing

```bash
# Create an Intent via API
curl -X POST http://localhost:8000/api/intents \
  -H "Content-Type: application/json" \
  -d '{"description": "Test intent processing", "priority": 5}'

# Check daemon logs
docker-compose logs -f intent_bridge
```

---

**Sprint 4 of PostgreSQL Dashboard System**
