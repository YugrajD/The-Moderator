# The Moderator

A full-stack application with a React frontend and FastAPI + LangChain backend.

## Project Structure

```
The-Moderator/
├── frontend/          # React frontend (Vite)
├── backend/           # FastAPI + LangChain backend
├── README.md         # This file
└── .gitignore        # Git ignore file
```

## Features

- **Frontend**: Modern React application with Vite
- **Backend**: FastAPI server with LangChain integration
- **Real-time communication**: WebSocket support for live updates
- **Modern UI**: Beautiful and responsive design

## Quick Start

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the backend server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

## API Documentation

Once the backend is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Development

- Backend API runs on port 8000
- Frontend development server runs on port 5173
- CORS is configured to allow frontend-backend communication

## Environment Variables

Create a `.env` file in the backend directory with:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Technologies Used

### Backend
- FastAPI
- LangChain
- Python 3.8+
- Uvicorn

### Frontend
- React 18
- Vite
- TypeScript
- Tailwind CSS
- Axios 