# Resonant Dashboard Frontend

React + TypeScript + Vite frontend for the Resonant Dashboard system.

## Features

- Slack-style message UI with real-time updates
- Specification management with Markdown support
- Intent management and status tracking
- Notification system with bell icon
- Tailwind CSS styling

## Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn

### Development

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Build for Production

```bash
npm run build
```

## Components

### Messages (`/messages`)
- View message history
- Send new messages
- Color-coded by type (user/yuno/kana/system)
- Auto-refresh every 5 seconds

### Specifications (`/specifications`)
- CRUD operations
- Markdown editor with preview
- Tag support
- Status tracking (draft/review/approved)

### Intents (`/intents`)
- Create new intents
- Priority slider
- Status monitoring
- View processing results

### Notifications
- Bell icon with badge
- Real-time unread count
- Mark as read functionality

## Docker Integration

The frontend is containerized with Nginx:

```bash
cd docker
docker-compose up --build -d
```

Access at http://localhost:3000

## API Configuration

Set `VITE_API_URL` environment variable or use the default proxy configuration in development.

---

**Sprint 3 of PostgreSQL Dashboard System**
