# EY-AY Chatbot

## Project Structure
```
ey-ay/
├── backend/          # FastAPI server (port 8000)
├── chatbot/         # PyTorch ML model & intents
├── shared/          # Shared database module
├── frontend/        # React + Vite + TailwindCSS
├── .env             # Environment variables
├── AGENTS.md        # This file
└── requirements.txt
```

## Commands
- Backend: `uvicorn backend.main:app --port 8000` (from project root)
- Frontend: `cd frontend && npm run dev`
- Train: `cd chatbot && python train.py`

## Architecture
- **Backend**: FastAPI + uvicorn + aiomysql
- **Chatbot**: PyTorch intent classifier
- **Database**: MySQL via aiomysql (async)
- **Frontend**: React 19 + Vite + TailwindCSS v4

## Key Files
- Model: `chatbot/data/processed/chatbot_model.pth`
- Intents: `chatbot/data/intents.json`
- Database: `shared/database.py`

## Notes
- Run migration to populate DB: `python scripts/migrate_json_to_db.py`
- Confidence threshold: 75% (configurable via .env: CONFIDENCE_THRESHOLD)
- LLM fallback: Uses Groq/OpenRouter when confidence is low