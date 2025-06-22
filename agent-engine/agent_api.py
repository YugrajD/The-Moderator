from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
from main import init_world, Moderator, WorldState

app = FastAPI(title="Agent Engine API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper state management)
current_moderator: Optional[Moderator] = None
current_world: Optional[WorldState] = None

class InitRequest(BaseModel):
    num_countries: int = 3

class PlayerInputRequest(BaseModel):
    message: str

class MeetingResponse(BaseModel):
    event_title: str
    event_description: str
    leader_responses: List[Dict[str, str]]
    transcript: List[str]
    meeting_complete: bool

@app.post("/init")
async def initialize_world(request: InitRequest):
    """Initialize a new agent world"""
    global current_moderator, current_world
    
    try:
        current_world = init_world(request.num_countries)
        current_moderator = Moderator(current_world)
        
        # Get initial leader info
        leaders_info = []
        for code, country in current_world.countries.items():
            leader = country.leader
            leaders_info.append({
                "code": code,
                "name": leader.name,
                "age": leader.age,
                "traits": leader.traits,
                "econ_power": leader.econ_power,
                "war_power": leader.war_power,
                "population": leader.population,
                "backstory": leader.backstory
            })
        
        return {
            "success": True,
            "leaders": leaders_info,
            "relationships": {code: country.relationships for code, country in current_world.countries.items()}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize world: {str(e)}")

@app.post("/start-meeting")
async def start_meeting():
    """Start a new diplomatic meeting"""
    global current_moderator
    
    if not current_moderator:
        raise HTTPException(status_code=400, detail="World not initialized")
    
    try:
        # Ensure there's an active event
        current_moderator._maybe_spawn()
        
        if not current_world.events:
            raise HTTPException(status_code=400, detail="No events to discuss")
        
        focus_event = current_world.events[0]
        
        # Get initial leader responses
        leader_responses = []
        transcript = []
        
        for code, agent in current_moderator.leaders.items():
            speech = agent.speak(focus_event, 1)
            leader_responses.append({
                "leader_code": code,
                "leader_name": current_world.countries[code].leader.name,
                "response": speech
            })
            transcript.append(f"{code}: {speech}")
            
            # Update other agents' memory
            for oc, ag in current_moderator.leaders.items():
                if oc != code:
                    ag.memory.append(("user", f"{code} said: {speech}"))
        
        return MeetingResponse(
            event_title=focus_event.title,
            event_description=focus_event.description,
            leader_responses=leader_responses,
            transcript=transcript,
            meeting_complete=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start meeting: {str(e)}")

@app.post("/player-input")
async def player_input(request: PlayerInputRequest):
    """Handle player input during a meeting"""
    global current_moderator
    
    if not current_moderator:
        raise HTTPException(status_code=400, detail="World not initialized")
    
    try:
        # Add player input to all agents' memory
        for agent in current_moderator.leaders.values():
            agent.memory.append(("user", request.message))
        
        # Get leader responses to player input
        focus_event = current_world.events[0] if current_world.events else None
        if not focus_event:
            raise HTTPException(status_code=400, detail="No active event")
        
        leader_responses = []
        transcript = [f"PLAYER: {request.message}"]
        
        for code, agent in current_moderator.leaders.items():
            speech = agent.speak(focus_event, len(agent.memory) // len(current_moderator.leaders) + 1)
            leader_responses.append({
                "leader_code": code,
                "leader_name": current_world.countries[code].leader.name,
                "response": speech
            })
            transcript.append(f"{code}: {speech}")
            
            # Update other agents' memory
            for oc, ag in current_moderator.leaders.items():
                if oc != code:
                    ag.memory.append(("user", f"{code} said: {speech}"))
        
        return MeetingResponse(
            event_title=focus_event.title,
            event_description=focus_event.description,
            leader_responses=leader_responses,
            transcript=transcript,
            meeting_complete=False
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process player input: {str(e)}")

@app.post("/end-meeting")
async def end_meeting():
    """End the current meeting and apply consequences"""
    global current_moderator, current_world
    
    if not current_moderator:
        raise HTTPException(status_code=400, detail="World not initialized")
    
    try:
        # Create transcript from all agent memories
        transcript = []
        for code, agent in current_moderator.leaders.items():
            for role, message in agent.memory:
                if role == "assistant":
                    transcript.append(f"{code}: {message}")
                else:
                    transcript.append(f"PLAYER: {message}")
        
        current_moderator._log = "\n".join(transcript)
        
        # Check for event resolution
        for evt in list(current_world.events):
            if current_moderator.resolution.decide(evt, current_moderator._log) and evt.cycles_alive > 0:
                evt.resolved = True
                current_moderator.resolved += 1
        
        current_moderator.world.meeting_number += 1
        
        return {
            "success": True,
            "transcript": transcript,
            "events_resolved": [e.title for e in current_world.events if e.resolved]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end meeting: {str(e)}")

@app.post("/advance-time")
async def advance_time():
    """Advance time by 6 months and apply consequences"""
    global current_moderator, current_world
    
    if not current_moderator:
        raise HTTPException(status_code=400, detail="World not initialized")
    
    try:
        # Evolve current events
        for evt in list(current_world.events):
            evt.cycles_alive += 1
            current_moderator.event_agent.evolve(evt, current_world)
            if evt.resolved:
                current_world.events.remove(evt)
        
        # Spawn new crisis if none active
        current_moderator._maybe_spawn()
        
        # Get current world state
        world_state = {
            "countries": {},
            "events": []
        }
        
        for code, country in current_world.countries.items():
            leader = country.leader
            world_state["countries"][code] = {
                "econ_power": leader.econ_power,
                "war_power": leader.war_power,
                "population": leader.population,
                "relationships": country.relationships
            }
        
        for event in current_world.events:
            world_state["events"].append({
                "title": event.title,
                "description": event.description,
                "type": event.e_type,
                "cycles_alive": event.cycles_alive
            })
        
        return {
            "success": True,
            "world_state": world_state
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to advance time: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
