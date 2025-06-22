# Agent Engine

This is the multimodal AI agent system for The Moderator diplomatic simulation game.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

3. Run the agent engine:
```bash
python agent_api.py
```

The agent engine will run on `http://localhost:8001`

## API Endpoints

- `POST /init` - Initialize a new agent world
- `POST /start-meeting` - Start a diplomatic meeting
- `POST /player-input` - Send player input during meeting
- `POST /end-meeting` - End the meeting and apply consequences
- `POST /advance-time` - Advance time by 6 months
- `GET /health` - Health check

## Integration

This agent engine is designed to work with the main game backend. The main game will call these endpoints to integrate the AI agents into the diplomatic simulation. 