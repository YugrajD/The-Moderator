import os
import random
import json
import copy
import textwrap
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from google.cloud import texttospeech
import base64

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='.')
CORS(app)

# ───── 0. LLM setup ─────
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise RuntimeError("Put ANTHROPIC_API_KEY in a .env file")

llm = ChatAnthropic(
    anthropic_api_key=API_KEY,
    model="claude-sonnet-4-20250514",
    temperature=0.7,
)

# ───── TTS setup ─────
tts_client = None
try:
    # Initialize Google Cloud TTS client
    credentials_path = "directed-optics-463710-f9-8f48037d3fa8.json"
    if os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        tts_client = texttospeech.TextToSpeechClient()
        print("✅ TTS service initialized successfully")
    else:
        print("⚠️ TTS credentials file not found, TTS will be disabled")
except Exception as e:
    print(f"⚠️ Failed to initialize TTS service: {e}")

# Voice mapping for different speakers
VOICE_MAPPING = {
    "world_agent": "en-US-Neural2-D",  # Deep, authoritative voice for world agent
    "leader_A": "en-US-Neural2-A",     # Male voice for Leader A
    "leader_B": "en-US-Neural2-F",     # Female voice for Leader B  
    "leader_C": "en-US-Neural2-E",     # Elderly voice for Leader C (for variety)
    "default": "en-US-Neural2-F"       # Default voice
}

# ───── Helpers ─────
TRAIT_NAMES = ["honest", "ambitious", "empathetic", "diplomatic", "ruthless"]
rand01 = lambda: round(random.uniform(0.1, 1.0), 1)

def extract_json(blob: str) -> dict:
    match = re.search(r"\{.*\}", blob, re.S)
    if not match:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(match.group(0))

def synthesize_tts(text: str, speaker: str = "default", voice_name: str = None) -> Optional[str]:
    """Generate TTS audio for text and return base64 encoded audio"""
    if not tts_client:
        return None
    
    # Use voice mapping if no specific voice is provided
    if voice_name is None:
        voice_name = VOICE_MAPPING.get(speaker, VOICE_MAPPING["default"])
    
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        return base64.b64encode(response.audio_content).decode('utf-8')
    except Exception as e:
        print(f"TTS synthesis failed for {speaker}: {e}")
        return None

# ───── 2. Data classes ─────
@dataclass
class Leader:
    code: str
    name: str
    age: int
    traits: Dict[str, float]
    econ_power: float
    war_power: float
    population: int
    backstory: str

@dataclass
class Country:
    code: str
    leader: Leader
    relationships: Dict[str, float]

@dataclass
class Event:
    eid: str
    title: str
    description: str
    e_type: str
    cycles_alive: int = 0
    resolved: bool = False
    addressed: bool = False
    audio_base64: Optional[str] = None

@dataclass
class WorldState:
    countries: Dict[str, Country] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    meeting_number: int = 0

# ───── 3. World generation ─────
def generate_leader(code: str) -> Leader:
    traits = {t: rand01() for t in TRAIT_NAMES}
    name = f"Leader_{code}"
    age = random.randint(40, 65)
    econ = rand01()
    war = rand01()
    pop = random.randint(5, 300) * 1_000_000

    traits_str = ", ".join(f"{k}={v}" for k, v in traits.items())
    bio_prompt = [
        SystemMessage(content="Write a 3-sentence bio for a fictional head of state. Try to make a unique response."),
        HumanMessage(content=f"Bio for {name}, age {age}, country {code}. Traits: {traits_str}"),
    ]
    try:
        bio = llm.invoke(bio_prompt).content.strip()
    except Exception:
        bio = f"Leader of country {code}, known for their {max(traits.items(), key=lambda x: x[1])[0]} approach to governance."
    
    return Leader(code, name, age, traits, econ, war, pop, bio)

def init_world(n: int = 3) -> WorldState:
    world = WorldState()
    codes = [chr(ord("A") + i) for i in range(n)]
    for c in codes:
        world.countries[c] = Country(c, generate_leader(c), {})
    for i, ci in enumerate(codes):
        for cj in codes[i + 1:]:
            w = rand01()
            world.countries[ci].relationships[cj] = w
            world.countries[cj].relationships[ci] = w
    return world

# ───── 4. Leader agent ─────
class LeaderAgent:
    def __init__(self, country: Country):
        self.country = country
        self.memory: List[Tuple[str, str]] = []

    def _system(self) -> SystemMessage:
        l = self.country.leader
        rels = ", ".join(f"country {k}:{v:.1f}" for k, v in self.country.relationships.items()) or "none"
        traits = ", ".join(f"{k}={v}" for k, v in l.traits.items())
        return SystemMessage(
            content=(
                "This is a fictional simulation between world leaders. Peaceful resolutions and threats of violence are equally allowed.\n"
                f"You are {l.name}, leader of country {self.country.code}.\n"
                f"Traits: {traits}. Relationships: {rels}.\n"
                "Speak first-person, ≤3 sentences. Never mention being an AI. When referring to other leaders, use 'leader A', 'leader B', etc. When referring to other countries, use 'country A', 'country B', etc."
            )
        )

    def _history(self):
        return [
            HumanMessage(content=t) if r == "user" else AIMessage(content=t)
            for r, t in self.memory[-6:]
        ]

    def speak(self, focus_events: List[Event], rnd: int) -> str:
        event_titles = "; ".join(e.title for e in focus_events)
        prompt = [
            self._system(),
            *self._history(),
            HumanMessage(
                content=f"Round {rnd}: Headlines → {event_titles}. Respond in ≤3 sentences."
            ),
        ]
        try:
            reply = llm.invoke(prompt).content.strip()
            self.memory.append(("assistant", reply))
            return reply
        except Exception as e:
            # Fallback response
            dominant_trait = max(self.country.leader.traits.items(), key=lambda x: x[1])[0]
            fallback_responses = {
                "honest": "We must address these issues with complete transparency.",
                "ambitious": "This is an opportunity for decisive action.",
                "empathetic": "We must consider all those affected by these crises.",
                "diplomatic": "I believe we can find common ground through dialogue.",
                "ruthless": "We will do whatever is necessary to protect our interests."
            }
            return fallback_responses.get(dominant_trait, "We must work together on these challenges.")

# ───── 5. Event agent ─────
class EventAgent:
    MAX_EVENTS = 3

    def generate_multiple(self, w: WorldState) -> List[Event]:
        events = []
        exist = {e.title.lower() for e in w.events}
        
        for attempt in range(5):
            if len(events) >= self.MAX_EVENTS:
                break
                
            ctx = {
                "countries": {
                    k: {
                        "econ": w.countries[k].leader.econ_power,
                        "war": w.countries[k].leader.war_power,
                        "relations": w.countries[k].relationships,
                    }
                    for k in w.countries
                },
                "active_events": list(exist),
                "existing_titles": [e.title for e in events],
            }
            sys = SystemMessage(
                content=textwrap.dedent(
                    "You are WORLD-AI. Create diverse events: conflicts, disasters, economic issues. Some wild examples include: assassinations, coups, or stock market crash."
                    "No duplicate titles. Respond only JSON {eid,title,description,e_type}."
                )
            )
            try:
                raw = llm.invoke([sys, HumanMessage(content=json.dumps(ctx))]).content
                d = extract_json(raw)
                if d["title"].lower() not in exist and d["title"] not in [e.title for e in events]:
                    events.append(Event(d["eid"], d["title"], d["description"], d["e_type"]))
                    exist.add(d["title"].lower())
            except Exception:
                pass
        
        # Fallback events if AI generation fails
        # FIX THIS
        #

        while len(events) < self.MAX_EVENTS:
            fid = f"E{len(w.events)+len(events)+1}"
            c = random.choice(list(w.countries))
            event_types = ["Minor Incident", "Economic Concern", "Diplomatic Issue"]
            event_type = random.choice(event_types)
            events.append(Event(fid, f"{event_type} in Country {c}", f"Low-impact {event_type.lower()}.", "misc"))
        
        return events

    def evolve(self, e: Event, w: WorldState):
        ctx = {
            "event": asdict(e),
            "relations": {k: c.relationships for k, c in w.countries.items()},
            "cycles": e.cycles_alive,
        }
        sys = SystemMessage(content="Advance 6 months; JSON {title,description,resolved}.")
        try:
            raw = llm.invoke([sys, HumanMessage(content=json.dumps(ctx))]).content
            d = extract_json(raw)
            e.title = d.get("title", e.title)
            e.description = d.get("description", e.description)
            e.resolved = bool(d.get("resolved", e.resolved))
        except Exception:
            # Random evolution fallback
            if e.cycles_alive > 2 and random.random() < 0.3:
                e.resolved = True

# ───── 6. Resolution & Summary agents ─────
class ResolutionAgent:
    @staticmethod
    def decide(evt: Event, log: str) -> bool:
        try:
            raw = llm.invoke([
                SystemMessage(content='Return JSON {"resolved":true/false}'),
                HumanMessage(content=log[-8000:]),
            ]).content
            return extract_json(raw).get("resolved", False)
        except Exception:
            return random.random() < 0.4  # 40% chance fallback

class MeetingOutcomeAnalyzer:
    @staticmethod
    def analyze_meeting_outcomes(world: WorldState, transcript: str) -> Dict:
        countries = list(world.countries.keys())
        
        context = {
            "countries": {k: {
                "name": world.countries[k].leader.name,
                "traits": world.countries[k].leader.traits,
                "econ": world.countries[k].leader.econ_power,
                "war": world.countries[k].leader.war_power,
                "relationships": world.countries[k].relationships
            } for k in countries},
            "transcript": transcript,
            "active_events": [e.title for e in world.events]
        }
        
        sys = SystemMessage(content=textwrap.dedent("""
            Analyze the diplomatic meeting transcript and determine immediate consequences.
            Consider:
            - Alliances formed or broken
            - Threats made or received
            - Economic cooperation or sanctions
            - Military posturing
            - Diplomatic wins or losses
            
            Return JSON with immediate stat changes:
            {
                "stat_changes": {
                    "A": {"econ": 0.05, "war": -0.02, "pop": 0},
                    "B": {"econ": 0.03, "war": 0.01, "pop": 0},
                    "C": {"econ": -0.08, "war": 0.05, "pop": -1000000}
                },
                "relationship_changes": [
                    ["A", "B", 0.1],
                    ["A", "C", -0.15],
                    ["B", "C", -0.1]
                ],
                "summary": "Brief explanation of key outcomes"
            }
            
            Use small values (0.01 to 0.15 for econ/war, 0 to ±5M for population).
            Positive values = benefits, negative = penalties.
        """))
        
        try:
            raw = llm.invoke([sys, HumanMessage(content=json.dumps(context))]).content
            result = extract_json(raw)
            return result
        except Exception:
            # Fallback: minimal random changes
            return {
                "stat_changes": {k: {
                    "econ": (random.random() - 0.5) * 0.1, 
                    "war": (random.random() - 0.5) * 0.1, 
                    "pop": int((random.random() - 0.5) * 1000000)
                } for k in countries},
                "relationship_changes": [],
                "summary": "Mixed diplomatic outcomes with some progress on key issues."
            }

# ───── 7. Game Session Management ─────
class GameSession:
    def __init__(self):
        self.world = init_world(3)
        self.leaders = {k: LeaderAgent(c) for k, c in self.world.countries.items()}
        self.event_agent = EventAgent()
        self.resolution = ResolutionAgent()
        self.outcome_analyzer = MeetingOutcomeAnalyzer()
        self.spawned = 0
        self.resolved = 0
        self.transcript = []
        self._generate_initial_events()

    def _generate_initial_events(self):
        new_events = self.event_agent.generate_multiple(self.world)
        for event in new_events:
            if event.title not in [e.title for e in self.world.events]:
                # Generate TTS audio for new events with world agent voice
                event_text = f"Breaking news: {event.title}. {event.description}"
                event.audio_base64 = synthesize_tts(event_text, speaker="world_agent")
                self.world.events.append(event)
                self.spawned += 1

    def get_world_state(self):
        return {
            "countries": {k: {
                "code": c.code,
                "leader": asdict(c.leader),
                "relationships": c.relationships
            } for k, c in self.world.countries.items()},
            "events": [asdict(e) for e in self.world.events],
            "meeting_number": self.world.meeting_number
        }

    def conduct_round(self, selected_event_ids: List[str], round_num: int, player_message: str = None):
        selected_events = [e for e in self.world.events if e.eid in selected_event_ids]
        
        responses = []
        
        # Leaders speak
        for code, agent in self.leaders.items():
            speech = agent.speak(selected_events, round_num)
            leader = self.world.countries[code].leader
            dominant_trait = max(leader.traits.items(), key=lambda x: x[1])[0]
            
            # Generate TTS audio for leader response with country-specific voice
            speaker_key = f"leader_{code}"
            audio_base64 = synthesize_tts(speech, speaker=speaker_key)
            
            response = {
                "speaker": f"{leader.name} ({dominant_trait})",
                "content": speech,
                "type": "leader",
                "country": code,
                "audio_base64": audio_base64
            }
            responses.append(response)
            
            # Add to other leaders' memory
            for other_code, other_agent in self.leaders.items():
                if other_code != code:
                    other_agent.memory.append(("user", f"{leader.name} said: {speech}"))
            
            self.transcript.append(f"{leader.name}: {speech}")

        # Player message
        if player_message:
            responses.append({
                "speaker": "UN Secretary-General",
                "content": player_message,
                "type": "player"
            })
            
            # Add to all leaders' memory
            for agent in self.leaders.values():
                agent.memory.append(("user", player_message))
                
            self.transcript.append(f"PLAYER: {player_message}")

        return responses

    def end_meeting(self, selected_event_ids: List[str]):
        # Mark selected events as addressed
        for event in self.world.events:
            if event.eid in selected_event_ids:
                event.addressed = True

        # Analyze meeting outcomes
        transcript_text = "\n".join(self.transcript)
        outcomes = self.outcome_analyzer.analyze_meeting_outcomes(self.world, transcript_text)
        
        # Generate TTS audio for meeting outcomes with world agent voice
        summary = outcomes.get("summary", "Meeting concluded with mixed outcomes.")
        audio_base64 = synthesize_tts(summary, speaker="world_agent")
        outcomes["audio_base64"] = audio_base64
        
        # Apply stat changes
        stat_changes = outcomes.get("stat_changes", {})
        for country_code, changes in stat_changes.items():
            if country_code in self.world.countries:
                leader = self.world.countries[country_code].leader
                leader.econ_power = max(0.1, min(1.0, leader.econ_power + changes.get("econ", 0)))
                leader.war_power = max(0.1, min(1.0, leader.war_power + changes.get("war", 0)))
                leader.population = max(1, leader.population + int(changes.get("pop", 0)))

        # Apply relationship changes
        rel_changes = outcomes.get("relationship_changes", [])
        for a, b, delta in rel_changes:
            if a in self.world.countries and b in self.world.countries[a].relationships:
                new_rel = max(0.0, min(1.0, self.world.countries[a].relationships[b] + delta))
                self.world.countries[a].relationships[b] = new_rel
                self.world.countries[b].relationships[a] = new_rel

        # Check for event resolution
        selected_events = [e for e in self.world.events if e.eid in selected_event_ids]
        for evt in selected_events:
            if self.resolution.decide(evt, transcript_text) and evt.cycles_alive > 0:
                evt.resolved = True
                self.resolved += 1

        self.world.meeting_number += 1
        self.transcript = []  # Reset for next meeting
        
        return outcomes

    def time_skip(self):
        # Evolve events
        for evt in list(self.world.events):
            evt.cycles_alive += 1
            self.event_agent.evolve(evt, self.world)
            if evt.resolved:
                self.world.events.remove(evt)

        # Generate new events if needed
        if len(self.world.events) < 3:
            new_events = self.event_agent.generate_multiple(self.world)
            for event in new_events:
                if event.title not in [e.title for e in self.world.events]:
                    # Generate TTS audio for new events with world agent voice
                    event_text = f"Breaking news: {event.title}. {event.description}"
                    event.audio_base64 = synthesize_tts(event_text, speaker="world_agent")
                    self.world.events.append(event)
                    self.spawned += 1

        # Reset addressed status
        for event in self.world.events:
            event.addressed = False

# Global game sessions storage (in production, use proper session management)
game_sessions = {}

# ───── API Routes ─────

# ───── TTS API Routes ─────
@app.route('/api/tts/status', methods=['GET'])
def tts_status():
    """Check if TTS service is available"""
    return jsonify({
        "available": tts_client is not None,
        "service_type": "Google Cloud Text-to-Speech"
    })

@app.route('/api/tts/voices', methods=['GET'])
def tts_voices():
    """Get available voices for a language"""
    if not tts_client:
        return jsonify({"error": "TTS service not available"}), 503
    
    language_code = request.args.get('language_code', 'en-US')
    
    try:
        request_voices = texttospeech.ListVoicesRequest(language_code=language_code)
        response = tts_client.list_voices(request=request_voices)
        
        voices = []
        for voice in response.voices:
            voices.append({
                "name": voice.name,
                "language_codes": list(voice.language_codes),
                "ssml_gender": voice.ssml_gender.name,
                "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
            })
        
        return jsonify({
            "voices": voices,
            "language_code": language_code
        })
    except Exception as e:
        return jsonify({"error": f"Failed to get voices: {str(e)}"}), 500

@app.route('/api/tts/synthesize', methods=['POST'])
def tts_synthesize():
    """Convert text to speech"""
    if not tts_client:
        return jsonify({"error": "TTS service not available"}), 503
    
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Missing text parameter"}), 400
    
    text = data.get('text', '')
    voice_name = data.get('voice_name', 'en-US-Neural2-F')
    language_code = data.get('language_code', 'en-US')
    speaking_rate = data.get('speaking_rate', 0.9)
    speaker = data.get('speaker', 'default')
    
    if not text.strip():
        return jsonify({"error": "Text cannot be empty"}), 400
    
    if speaking_rate < 0.25 or speaking_rate > 4.0:
        return jsonify({"error": "Speaking rate must be between 0.25 and 4.0"}), 400
    
    try:
        # Use voice mapping if no specific voice is provided
        if voice_name == 'en-US-Neural2-F' and speaker != 'default':
            voice_name = VOICE_MAPPING.get(speaker, VOICE_MAPPING["default"])
        
        # Set up the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )
        
        # Select the type of audio file to return
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )
        
        # Perform the text-to-speech request
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        # Convert audio content to base64
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        return jsonify({
            "audio_base64": audio_base64,
            "text": text,
            "voice_name": voice_name,
            "language_code": language_code,
            "speaking_rate": speaking_rate
        })
        
    except Exception as e:
        return jsonify({"error": f"TTS synthesis failed: {str(e)}"}), 500

@app.route('/api/tts/world-agent', methods=['POST'])
def tts_world_agent():
    """Generate TTS audio for world agent messages"""
    if not tts_client:
        return jsonify({"error": "TTS service not available"}), 503
    
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Missing message parameter"}), 400
    
    message = data.get('message', '')
    if not message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    
    try:
        audio_base64 = synthesize_tts(message, speaker="world_agent")
        return jsonify({
            "audio_base64": audio_base64,
            "message": message
        })
    except Exception as e:
        return jsonify({"error": f"TTS synthesis failed: {str(e)}"}), 500

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Only serve specific file types for security
    allowed_extensions = {'.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico'}
    if any(filename.endswith(ext) for ext in allowed_extensions):
        return send_from_directory('.', filename)
    return "File not found", 404

@app.route('/api/new-game', methods=['POST'])
def new_game():
    session_id = str(int(time.time() * 1000))  # Simple session ID
    game_sessions[session_id] = GameSession()
    
    return jsonify({
        "session_id": session_id,
        "world_state": game_sessions[session_id].get_world_state()
    })

@app.route('/api/conduct-round', methods=['POST'])
def conduct_round():
    data = request.json
    session_id = data.get('session_id')
    selected_event_ids = data.get('selected_event_ids', [])
    round_num = data.get('round_num', 1)
    player_message = data.get('player_message', '')
    
    if session_id not in game_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = game_sessions[session_id]
    responses = session.conduct_round(selected_event_ids, round_num, player_message)
    
    return jsonify({
        "responses": responses,
        "world_state": session.get_world_state()
    })

@app.route('/api/end-meeting', methods=['POST'])
def end_meeting():
    data = request.json
    session_id = data.get('session_id')
    selected_event_ids = data.get('selected_event_ids', [])
    
    if session_id not in game_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = game_sessions[session_id]
    outcomes = session.end_meeting(selected_event_ids)
    
    return jsonify({
        "outcomes": outcomes,
        "world_state": session.get_world_state()
    })

@app.route('/api/time-skip', methods=['POST'])
def time_skip():
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in game_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = game_sessions[session_id]
    session.time_skip()
    
    return jsonify({
        "world_state": session.get_world_state()
    })

@app.route('/api/generate-final-assessment', methods=['POST'])
def generate_final_assessment():
    """Generate AI assessment of player's diplomatic performance"""
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in game_sessions:
        return jsonify({"error": "Invalid session"}), 400
    
    session = game_sessions[session_id]
    
    try:
        # Prepare context for assessment
        context = {
            "world_state": session.get_world_state(),
            "meeting_number": session.world.meeting_number,
            "events_spawned": session.spawned,
            "events_resolved": session.resolved,
            "transcript": session.transcript
        }
        
        # Generate assessment using Claude AI
        assessment_prompt = [
            SystemMessage(content=textwrap.dedent("""
                You are a diplomatic analyst evaluating the performance of a UN Secretary-General in a crisis simulation.
                Analyze the diplomatic outcomes, relationships between countries, and overall world stability.
                Provide a comprehensive assessment in 3-4 paragraphs covering:
                1. Diplomatic effectiveness and relationship management
                2. Crisis resolution and event handling
                3. Overall impact on world stability
                4. Specific strengths and areas for improvement
                
                Be constructive, specific, and diplomatic in your assessment.
            """)),
            HumanMessage(content=json.dumps(context))
        ]
        
        assessment = llm.invoke(assessment_prompt).content.strip()
        
        return jsonify({
            "assessment": assessment
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate assessment: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 