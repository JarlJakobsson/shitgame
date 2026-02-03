# Gladiator Arena

A text-based gladiator game converted to a web-based application.

## Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + FastAPI

## Project Structure

```
jarlworld/
├── backend/           # Python FastAPI server
│   ├── main.py       # FastAPI app
│   ├── gladiator.py  # Gladiator class
│   ├── combat.py     # Combat system
│   ├── races.py      # Race definitions
│   ├── constants.py  # Game constants
│   ├── models.py     # Pydantic models
│   └── requirements.txt
├── frontend/         # React TypeScript app
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── services/    # API service
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend folder (in a new terminal):
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

## How to Play

1. Start both the backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Create your gladiator and choose a race
4. Train to improve your stats (costs gold)
5. Fight in the arena to earn experience and gold
6. Compete and become a champion!

## Features

- Create a gladiator with different races (Human, Orc)
- Real-time turn-based combat system
- Training system to improve stats
- Gold and experience rewards
- Win/loss tracking
- Beautiful UI with animations

## API Endpoints

- `GET /` - Health check
- `GET /races` - Get all races
- `POST /gladiator` - Create a gladiator
- `GET /gladiator` - Get current gladiator stats
- `POST /gladiator/train` - Train the gladiator
- `POST /combat/start` - Start a combat
- `POST /combat/round` - Execute a combat round
- `POST /combat/finish` - Finish combat and get rewards
