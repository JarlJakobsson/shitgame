# Gladiator Arena

Web-based gladiator game with a React frontend and FastAPI backend.

## Tech Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Deployment/runtime: Docker Compose (Nginx + API + DB)

## Main Features

- Create and manage gladiators
- Arena PvE battles
- Equipment and shop system
- Training and stat allocation
- Persistent progression (gold, XP, wins/losses)
- Basic multiplayer identity per browser tab/window
- Random battle queue (match 2 queued players and notify both when finished)

## Project Structure

```text
.
|-- backend/
|   |-- main.py
|   |-- combat.py
|   |-- gladiator.py
|   |-- enemies.py
|   |-- equipment.py
|   |-- schemas.py
|   |-- models_db.py
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |-- Dockerfile
|   |-- nginx.conf
|   `-- vite.config.ts
|-- docker-compose.yml
`-- README.md
```

## Quick Start (Docker, recommended)

From repo root:

```bash
docker compose up --build
```

Services:

- Frontend (Nginx): `http://localhost:8080`
- Backend API: `http://localhost:5000`
- API docs: `http://localhost:5000/docs`
- PostgreSQL: `localhost:5432`

Stop:

```bash
docker compose down
```

## Local Development (without Docker)

### 1) Start PostgreSQL

Backend expects PostgreSQL. By default it reads:

- `POSTGRES_HOST` (default `localhost`)
- `POSTGRES_PORT` (default `5432`)
- `POSTGRES_DB` (default `gladiator`)
- `POSTGRES_USER` (default `gladiator`)
- `POSTGRES_PASSWORD` (default `gladiator`)

You can also set `DATABASE_URL` directly.

### 2) Backend

```bash
cd backend
python -m venv venv
```

Activate venv:

- PowerShell: `./venv/Scripts/Activate.ps1`
- Git Bash: `source venv/Scripts/activate`

Install + run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 5000
```

Backend: `http://localhost:5000`

### 3) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

In local dev, `.env.development` points frontend API calls to `http://localhost:5000`.

## Multiplayer Notes

- The frontend sends an `X-Player-ID` header automatically (generated per browser tab via `sessionStorage`).
- Opening a second browser window/tab (or incognito) creates a different player identity.
- Each player can create their own gladiator without overwriting the other.
- Random matchmaking flow:
  - Player A clicks `Random Battle` -> queued.
  - Player B clicks `Random Battle` -> they are matched.
  - Battle resolves server-side.
  - Both players receive a completion notification and updated win/loss stats.

## Important API Endpoints

- `GET /health`
- `GET /races`
- `GET /enemies`
- `POST /gladiator`
- `GET /gladiator`
- `POST /gladiator/train`
- `POST /gladiator/allocate`
- `POST /combat/start`
- `POST /combat/round`
- `POST /combat/finish`
- `GET /equipment`
- `GET /equipment/shop`
- `POST /equipment/purchase/{equipment_id}`
- `POST /pvp/random-battle/join`
- `GET /notifications`

## Testing

Backend tests:

```bash
backend\\venv\\Scripts\\python -m pytest backend/tests -q
```
