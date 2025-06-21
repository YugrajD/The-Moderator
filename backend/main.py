from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import httpx
import asyncio

# Load environment variables
load_dotenv()

app = FastAPI(
    title="The Moderator API",
    description="A FastAPI backend with OpenAI integration and map generation for a diplomatic simulation game.",
    version="1.1.0"
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

class WorldGenerationRequest(BaseModel):
    width: Optional[int] = 1000
    height: Optional[int] = 600
    regions: Optional[int] = 8
    seed: Optional[str] = None

class WorldGenerationResponse(BaseModel):
    success: bool
    map_data: Optional[dict] = None
    error: Optional[str] = None

class LeaderProfile(BaseModel):
    name: str
    personality: str
    ambition: str

class Nation(BaseModel):
    name: str
    government_type: str
    leader: LeaderProfile
    region_id: int
    region_name: str
    terrain: str
    climate: str

class GameState(BaseModel):
    map_data: dict
    nations: List[Nation]

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    llm_available = True
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")
    client = None
    llm_available = False

# Map service configuration
MAP_SERVICE_URL = "http://localhost:3001"

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

# --- Helper Functions ---

async def generate_nation_for_region(region: dict) -> Nation:
    """Generates a nation profile for a given map region using OpenAI."""
    if not client or not llm_available:
        # Fallback if AI is not available
        return Nation(
            name=f"The Republic of {region.get('name', 'Region' + str(region.get('id')))}",
            government_type="Republic",
            leader=LeaderProfile(name="Placeholder Leader", personality="Cautious", ambition="Survival"),
            region_id=region.get('id'),
            region_name=region.get('name'),
            terrain=region.get('terrain'),
            climate=region.get('climate')
        )

    terrain = region.get('terrain')
    climate = region.get('climate')
    neighbors_count = len(region.get('neighbors', []))

    prompt = f"""
    Based on the following geographical and strategic information for a fantasy region, create a unique nation.
    
    Region Name: {region.get('name')}
    Terrain: {terrain}
    Climate: {climate}
    Number of neighboring regions: {neighbors_count}

    Generate the following details for this nation in a JSON format:
    1.  "nation_name": A creative and fitting name for the nation.
    2.  "government_type": A plausible type of government (e.g., Monarchy, Republic, Theocracy, Magocracy, etc.).
    3.  "leader": An object with the following keys:
        - "name": A fitting name for the nation's leader.
        - "personality": A brief description (2-3 words) of the leader's personality (e.g., "Ambitious and Cunning", "Peaceful and Diplomatic", "Paranoid and Xenophobic").
        - "ambition": A short phrase describing the leader's primary ambition (e.g., "To conquer its neighbors", "To achieve economic prosperity", "To protect its people at all costs").

    Your response must be a valid JSON object only, with no other text before or after it.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a creative world-building assistant for a political simulation game. You only respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=250,
            response_format={"type": "json_object"}
        )
        
        nation_data = json.loads(response.choices[0].message.content)
        leader_data = nation_data.get("leader", {})

        return Nation(
            name=nation_data.get("nation_name"),
            government_type=nation_data.get("government_type"),
            leader=LeaderProfile(
                name=leader_data.get("name"),
                personality=leader_data.get("personality"),
                ambition=leader_data.get("ambition")
            ),
            region_id=region.get('id'),
            region_name=region.get('name'),
            terrain=region.get('terrain'),
            climate=region.get('climate')
        )
    except Exception as e:
        print(f"Error generating nation for region {region.get('id')}: {e}")
        # Return a fallback nation on error
        return Nation(
            name=f"The Lost Kingdom of {region.get('name', 'Region' + str(region.get('id')))}",
            government_type="Fallen Kingdom",
            leader=LeaderProfile(name="Nameless King", personality="Sorrowful", ambition="To be remembered"),
            region_id=region.get('id'),
            region_name=region.get('name'),
            terrain=region.get('terrain'),
            climate=region.get('climate')
        )

@app.get("/")
async def root():
    return {"message": "Welcome to The Moderator API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "openai_available": llm_available}

@app.post("/generate-world", response_model=WorldGenerationResponse)
async def generate_world(request: WorldGenerationRequest):
    """Generate a new world map using the map generation microservice"""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                f"{MAP_SERVICE_URL}/generate-world",
                json={
                    "width": request.width,
                    "height": request.height,
                    "regions": request.regions,
                    "seed": request.seed
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return WorldGenerationResponse(
                    success=True,
                    map_data=data.get("map")
                )
            else:
                return WorldGenerationResponse(
                    success=False,
                    error=f"Map service error: {response.status_code}"
                )
                
    except httpx.RequestError as e:
        return WorldGenerationResponse(
            success=False,
            error=f"Failed to connect to map service: {str(e)}"
        )
    except Exception as e:
        return WorldGenerationResponse(
            success=False,
            error=f"Error generating world: {str(e)}"
        )

@app.post("/initialize-game", response_model=GameState)
async def initialize_game(request: WorldGenerationRequest):
    """
    Initializes a new game by generating a world map and populating it with AI-generated nations.
    """
    # 1. Generate a world
    world_data_response = await generate_world(request)
    if not world_data_response.success:
        raise HTTPException(status_code=500, detail=world_data_response.error)
    
    map_data = world_data_response.map_data
    regions = map_data.get("regions", [])

    if not regions:
        raise HTTPException(status_code=500, detail="Failed to generate regions for the map.")

    # 2. For each region, generate a nation using AI concurrently
    tasks = [generate_nation_for_region(region) for region in regions]
    nations = await asyncio.gather(*tasks)

    # 3. Assemble and return the full game state
    return GameState(map_data=map_data, nations=nations)

@app.get("/map-service-health")
async def check_map_service_health():
    """Check if the map generation service is healthy"""
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(f"{MAP_SERVICE_URL}/health", timeout=5.0)
            return {
                "map_service_healthy": response.status_code == 200,
                "map_service_status": response.json() if response.status_code == 200 else None
            }
    except Exception as e:
        return {
            "map_service_healthy": False,
            "error": str(e)
        }

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