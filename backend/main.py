from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables
load_dotenv()

app = FastAPI(
    title="The Moderator API",
    description="A FastAPI backend with OpenAI integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: Optional[str] = None

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    llm_available = True
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")
    client = None
    llm_available = False

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Welcome to The Moderator API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "openai_available": llm_available}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(chat_message: ChatMessage):
    if not client or not llm_available:
        raise HTTPException(status_code=500, detail="AI model not available")
    
    try:
        # Create chat completion with OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."},
                {"role": "user", "content": chat_message.message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return ChatResponse(
            response=response.choices[0].message.content,
            user_id=chat_message.user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message with OpenAI if available
            if client and llm_available:
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."},
                            {"role": "user", "content": message_data.get("message", "")}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    response_data = {
                        "type": "ai_response",
                        "message": response.choices[0].message.content,
                        "user_id": client_id
                    }
                    await manager.send_personal_message(json.dumps(response_data), websocket)
                except Exception as e:
                    error_data = {
                        "type": "error",
                        "message": f"Error processing message: {str(e)}",
                        "user_id": client_id
                    }
                    await manager.send_personal_message(json.dumps(error_data), websocket)
            else:
                error_data = {
                    "type": "error",
                    "message": "AI model not available",
                    "user_id": client_id
                }
                await manager.send_personal_message(json.dumps(error_data), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 