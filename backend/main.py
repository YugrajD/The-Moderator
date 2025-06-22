from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import httpx
import asyncio
import random
from itertools import groupby

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

# Agent Engine configuration
AGENT_ENGINE_URL = "http://localhost:8001"

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
    age: int

class Nation(BaseModel):
    name: str
    government_type: str
    leader: LeaderProfile
    id: int
    capital_province_name: str
    provinces: List[dict]
    military_strength: int
    population: int

class GameState(BaseModel):
    map_data: dict
    nations: List[Nation]
    diplomatic_relations: dict
    event_log: List[str]
    agent_world_initialized: bool = False
    current_meeting: Optional[dict] = None

# New models for agent integration
class AgentMeetingRequest(BaseModel):
    player_input: Optional[str] = None

class AgentMeetingResponse(BaseModel):
    event_title: str
    event_description: str
    leader_responses: List[Dict[str, str]]
    transcript: List[str]
    meeting_complete: bool

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

# --- Fallback Data ---
GOVERNMENT_TYPES = [
    "Presidential Republic", "Parliamentary Republic", "Federal Republic", "Democratic Republic",
    "Constitutional Monarchy", "Federation", "Confederation", "Unitary State",
    "One-Party State", "Military Junta", "Provisional Government", "Technocracy"
]

LEADER_PERSONALITIES = [
    "Ambitious and Cunning", "Honorable and Just", "Peaceful and Diplomatic",
    "Paranoid and Xenophobic", "Scholarly and Reclusive", "Greedy and Materialistic",
    "Brave and Reckless", "Pious and Dogmatic", "Pragmatic and Ruthless"
]

LEADER_AMBITIONS = [
    "to conquer its rivals", "to achieve economic mastery", "to protect its ancient culture",
    "to spread its faith", "to build legendary wonders", "to forge a lasting peace",

    "to survive the coming winter", "to reclaim lost lands", "to master forbidden magic"
]

# New, culturally diverse name lists
FIRST_NAMES = [
    # European
    "Erik", "Anya", "Ivan", "Luisa", "William", "Elara", "Gareth", "Isolde",
    # East Asian
    "Kenji", "Mei", "Jin", "Hana", "Shin", "Yuna",
    # South Asian
    "Rohan", "Priya", "Vikram", "Anjali",
    # Middle Eastern / North African
    "Khalid", "Fatima", "Amir", "Layla",
    # Sub-Saharan African
    "Kwame", "Abeba", "Bayo", "Chiamaka",
    # Latin American
    "Mateo", "Sofia", "Javier", "Camila"
]
LAST_NAMES = [
    # European
    "Volkov", "Ivanova", "Schmidt", "Rossi", "Williams", "O'Connell", "Chevalier",
    # East Asian
    "Kim", "Tanaka", "Li", "Watanabe", "Park",
    # South Asian
    "Singh", "Patel", "Khan", "Gupta",
    # Middle Eastern / North African
    "Al-Farsi", "Hassan", "Kadiri", "Said",
    # Sub-Saharan African
    "Nkosi", "Okoro", "Getachew", "Diallo",
    # Latin American
    "Garcia", "Rodriguez", "Martinez", "Silva"
]

# --- Helper Functions ---

async def generate_nation_profile(nation_id: int, provinces: List[dict]) -> Nation:
    """Generates a single nation profile for a group of provinces."""
    # Find the capital (or largest province as a fallback)
    capital = next((p for p in provinces if p.get('cityType') == 'capital'), None)
    if not capital:
        capital = max(provinces, key=lambda p: p.get('area', 0))

    # For the name generation, we can use the capital's name
    capital_name = capital.get('name', f"Territory {nation_id}")

    # Generate a random, culturally diverse leader name
    leader_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    leader_age = random.randint(35, 75)

    # Calculate military strength based on number of provinces and total area
    base_strength_per_province = 500
    area_modifier = sum(p.get('area', 0) for p in provinces) / 10000
    military_strength = int((len(provinces) * base_strength_per_province) + area_modifier)

    # Calculate population from the sum of its provinces
    population = sum(p.get('population', 0) for p in provinces)

    if not client or not llm_available:
        # Fallback logic
        return Nation(
            id=nation_id,
            name=capital_name,
            government_type=random.choice(GOVERNMENT_TYPES),
            leader=LeaderProfile(name=leader_name, personality="Pragmatic", ambition="To unite the lands", age=leader_age),
            capital_province_name=capital_name,
            provinces=provinces,
            military_strength=military_strength,
            population=population
        )

    # ... (AI generation logic can be adapted here, using info from the capital or all provinces) ...
    # For now, the fallback is robust enough to demonstrate the new structure.
    # The AI prompt would need to be re-worked to understand a nation with multiple provinces.
    # To keep this change focused, I will simplify and rely on the fallback for now.
    return Nation(
        id=nation_id,
        name=capital_name,
        government_type=random.choice(GOVERNMENT_TYPES),
        leader=LeaderProfile(name=leader_name, personality="Pragmatic", ambition="To unite the lands", age=leader_age),
        capital_province_name=capital_name,
        provinces=provinces,
        military_strength=military_strength,
        population=population
    )

# --- Agent Engine Integration Functions ---

async def initialize_agent_world(num_countries: int) -> bool:
    """Initialize the agent engine world"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_ENGINE_URL}/init",
                json={"num_countries": num_countries},
                timeout=30.0
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Failed to initialize agent world: {e}")
        return False

async def start_agent_meeting() -> Optional[dict]:
    """Start a new diplomatic meeting in the agent engine"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_ENGINE_URL}/start-meeting",
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Failed to start agent meeting: {e}")
        return None

async def send_player_input_to_agents(player_input: str) -> Optional[dict]:
    """Send player input to the agent engine"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_ENGINE_URL}/player-input",
                json={"message": player_input},
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Failed to send player input: {e}")
        return None

async def end_agent_meeting() -> Optional[dict]:
    """End the current meeting and get consequences"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_ENGINE_URL}/end-meeting",
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Failed to end agent meeting: {e}")
        return None

async def advance_agent_time() -> Optional[dict]:
    """Advance time in the agent engine"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AGENT_ENGINE_URL}/advance-time",
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        print(f"Failed to advance agent time: {e}")
        return None

@app.post("/advance-time", response_model=GameState)
async def advance_time(payload: dict = Body(...)):
    """
    Advances the game time by one turn (6 months), processing AI-driven diplomatic meetings and their consequences.
    """
    try:
        current_state = GameState.parse_obj(payload)
    except ValidationError as e:
        # This will return the detailed validation error to the frontend console
        raise HTTPException(status_code=422, detail=e.errors())

    # --- Clear all markers from the previous turn ---
    for p in current_state.map_data['regions']:
        if 'marker' in p:
            p['marker'] = None

    # Initialize event log for this turn
    current_state.event_log = []
    
    # Initialize agent world if not already done
    if not current_state.agent_world_initialized:
        success = await initialize_agent_world(len(current_state.nations))
        if success:
            current_state.agent_world_initialized = True
            current_state.event_log.append("The diplomatic council has been convened. World leaders are ready to discuss pressing matters.")
        else:
            current_state.event_log.append("Failed to initialize diplomatic council. Falling back to traditional diplomacy.")
            return current_state
    
    # Start a new diplomatic meeting
    meeting_data = await start_agent_meeting()
    if meeting_data:
        current_state.current_meeting = meeting_data
        current_state.event_log.append(f"Diplomatic meeting convened to discuss: {meeting_data['event_title']}")
        current_state.event_log.append(f"Event: {meeting_data['event_description']}")
        
        # Add initial leader responses to event log
        for response in meeting_data['leader_responses']:
            current_state.event_log.append(f"{response['leader_name']} ({response['leader_code']}): {response['response']}")
    else:
        current_state.event_log.append("Failed to start diplomatic meeting. The world continues without major developments.")
    
    return current_state

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
    Initializes a new game by generating a world map with provinces and grouping them into nations.
    """
    # 1. Generate a world with provinces, now called 'regions' in the response for compatibility
    world_data_response = await generate_world(request)
    if not world_data_response.success:
        raise HTTPException(status_code=500, detail=world_data_response.error)
    
    map_data = world_data_response.map_data
    provinces = map_data.get("regions", [])

    if not provinces:
        raise HTTPException(status_code=500, detail="Failed to generate provinces for the map.")

    # Add population to each province before grouping
    for province in provinces:
        province['population'] = int(province.get('area', 0) * random.uniform(1.2, 1.8)) # Each province gets population based on area
        province['cityType'] = None # Clear any previous city types

    # 2. Group provinces by their assigned nationId
    provinces.sort(key=lambda p: p['nationId'])
    nation_groups = {k: list(v) for k, v in groupby(provinces, key=lambda p: p['nationId']) if k is not None}
    
    # --- Assign capitals and major cities for each new nation ---
    for nation_id, nation_provinces in nation_groups.items():
        # Sort by area to find largest provinces
        nation_provinces.sort(key=lambda p: p.get('area', 0), reverse=True)
        
        # Assign capital (the largest)
        if len(nation_provinces) > 0:
            nation_provinces[0]['cityType'] = 'capital'
            
        # Assign up to two major cities (the next largest)
        if len(nation_provinces) > 1:
            nation_provinces[1]['cityType'] = 'major'
        if len(nation_provinces) > 2:
            nation_provinces[2]['cityType'] = 'major'

    # 3. For each group, generate a single nation profile concurrently
    tasks = [generate_nation_profile(nation_id, group) for nation_id, group in nation_groups.items()]
    nations = await asyncio.gather(*tasks)

    # 4. Initialize diplomatic relations
    nation_ids = [n.id for n in nations]
    diplomatic_relations = {}
    for n_id1 in nation_ids:
        diplomatic_relations[str(n_id1)] = {}
        for n_id2 in nation_ids:
            if n_id1 != n_id2:
                diplomatic_relations[str(n_id1)][str(n_id2)] = "Neutral"

    # 5. Initialize agent world and start first event
    event_log = []
    current_meeting = None
    agent_world_initialized = False
    
    try:
        # Initialize agent world
        success = await initialize_agent_world(len(nations))
        if success:
            agent_world_initialized = True
            event_log.append("The diplomatic council has been convened. World leaders are ready to discuss pressing matters.")
            
            # Start first diplomatic meeting
            meeting_data = await start_agent_meeting()
            if meeting_data:
                current_meeting = meeting_data
                event_log.append(f"Diplomatic meeting convened to discuss: {meeting_data['event_title']}")
                event_log.append(f"Event: {meeting_data['event_description']}")
                
                # Add initial leader responses to event log
                for response in meeting_data['leader_responses']:
                    event_log.append(f"{response['leader_name']} ({response['leader_code']}): {response['response']}")
            else:
                event_log.append("Failed to start diplomatic meeting. The world continues without major developments.")
        else:
            event_log.append("Failed to initialize diplomatic council. The world begins in relative peace.")
    except Exception as e:
        print(f"Error initializing agent world: {e}")
        event_log.append("The world begins in relative peace.")

    # 6. Assemble and return the full game state
    return GameState(
        map_data=map_data, 
        nations=nations,
        diplomatic_relations=diplomatic_relations,
        event_log=event_log,
        agent_world_initialized=agent_world_initialized,
        current_meeting=current_meeting
    )

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

@app.post("/agent/player-input", response_model=AgentMeetingResponse)
async def handle_player_input(request: AgentMeetingRequest):
    """Handle player input during an active diplomatic meeting"""
    if not request.player_input:
        raise HTTPException(status_code=400, detail="Player input is required")
    
    try:
        # Send player input to agent engine
        response_data = await send_player_input_to_agents(request.player_input)
        if not response_data:
            raise HTTPException(status_code=500, detail="Failed to process player input")
        
        return AgentMeetingResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing player input: {str(e)}")

@app.post("/agent/end-meeting")
async def end_current_meeting():
    """End the current diplomatic meeting and apply consequences"""
    try:
        # End meeting in agent engine
        result = await end_agent_meeting()
        if not result:
            raise HTTPException(status_code=500, detail="Failed to end meeting")
        
        # Advance time to apply consequences
        time_result = await advance_agent_time()
        if not time_result:
            raise HTTPException(status_code=500, detail="Failed to advance time")
        
        return {
            "success": True,
            "meeting_result": result,
            "time_advancement": time_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending meeting: {str(e)}")

@app.get("/agent/health")
async def check_agent_engine_health():
    """Check if the agent engine is running"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AGENT_ENGINE_URL}/health", timeout=5.0)
            return {
                "agent_engine_status": "healthy" if response.status_code == 200 else "unhealthy",
                "agent_engine_url": AGENT_ENGINE_URL
            }
    except Exception as e:
        return {
            "agent_engine_status": "unreachable",
            "agent_engine_url": AGENT_ENGINE_URL,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 