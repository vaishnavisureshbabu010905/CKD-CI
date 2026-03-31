# CKD-CI Frontend (Next.js + Tailwind)

A clinical command center UI for CKD-CI with chat, alerts, predictions, timeline, and governance panels.

## Prereqs
- Node 20+
- Backend API running (see root README)
- Copy `.env.example` to `.env.local` and set API endpoints

## Scripts
- `npm install`
- `npm run dev` (localhost:3000)
- `npm run build && npm start`

## Docker
```
docker build -t ckdci-frontend ./frontend
docker run -p 3000:3000 --env NEXT_PUBLIC_API_BASE=http://localhost:8000 --env NEXT_PUBLIC_WS_BASE=ws://localhost:8000 ckdci-frontend
```

## Compose (API + DB + Frontend)
```
docker compose -f docker-compose.frontend.yml up --build
```

## Pages
- `/login` – JWT login
- `/command-center` – summary, alerts, tasks
- `/patients` & `/patients/[id]` – list + detail
- `/prediction` – run predictions
- `/alerts` – alert panel
- `/chat` – WhatsApp-style care-team chat
- `/timeline` – patient events
- `/admin` – model governance
- `/monitoring` – health/metrics

## Deployment notes
- Set `NEXT_PUBLIC_API_BASE` to the public API URL
- Set `NEXT_PUBLIC_WS_BASE` for WebSocket chat
- Behind reverse proxy, route `/` to frontend and `/api` to FastAPI

## Migrations
Run backend migrations before using the app:
```
alembic upgrade head
python scripts/create_admin.py
```
