#!/usr/bin/env python3
"""
Text-based interface for UN Diplomatic Simulation
Uses message.txt as the UI while maintaining all TTS and game functionalities
"""

import requests
import json
import time
import os
import sys
from datetime import datetime

class TextInterface:
    def __init__(self, server_url="http://localhost:5001"):
        self.server_url = server_url
        self.session_id = None
        self.world_state = None
        self.is_in_meeting = False
        self.current_round = 0
        self.max_rounds = 3
        self.selected_events = []
        
    def write_message(self, message, append=True):
        """Write message to message.txt file"""
        try:
            if append:
                with open('message.txt', 'a', encoding='utf-8') as f:
                    f.write(f"\n{message}")
            else:
                with open('message.txt', 'w', encoding='utf-8') as f:
                    f.write(message)
        except Exception as e:
            print(f"Error writing to message.txt: {e}")
    
    def clear_messages(self):
        """Clear the message.txt file and write the header"""
        header = """╔══════════════════════════════════════════════════════════════════════════════╗
║                    🌍 UN DIPLOMATIC SIMULATION SYSTEM                        ║
║                              Text Interface                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Welcome to the United Nations Diplomatic Simulation powered by Claude AI.
You are the UN Secretary-General mediating international crises.

══════════════════════════════════════════════════════════════════════════════════

📊 SYSTEM STATUS:
   • Server: ✅ Connected (Port 5001)
   • TTS: ✅ Available (Google Cloud)
   • Session: None
   • Meeting: None
   • Round: 0/3

══════════════════════════════════════════════════════════════════════════════════

🎮 AVAILABLE COMMANDS:

   🚀 GAME CONTROL:
   • START          - Begin a new diplomatic simulation
   • STATUS         - Show current world status and leaders
   • TIME           - Advance time by 6 months

   🏛️ MEETING CONTROL:
   • SELECT <ID>    - Select/deselect event for meeting (e.g., SELECT E1)
   • MEETING        - Start diplomatic meeting with selected events
   • RESPOND <MSG>  - Send diplomatic message (e.g., RESPOND We must cooperate)
   • SKIP           - Skip your turn
   • NEXT           - Move to next round
   • END            - End current meeting

   ℹ️ UTILITY:
   • HELP           - Show detailed help information
   • QUIT           - Exit the simulation

══════════════════════════════════════════════════════════════════════════════════

🔊 TTS FEATURES:
   • All leader responses generate natural speech
   • Event announcements with TTS narration
   • Meeting outcomes with voice summaries
   • Audio is queued and plays sequentially

══════════════════════════════════════════════════════════════════════════════════

💡 QUICK START:
   1. Type 'START' to begin a new game
   2. Type 'STATUS' to see world leaders and events
   3. Type 'SELECT E1' to choose an event to address
   4. Type 'MEETING' to start diplomatic negotiations
   5. Type 'RESPOND <your message>' to send diplomatic messages

══════════════════════════════════════════════════════════════════════════════════

Ready to begin diplomatic negotiations...
Type 'START' to begin or 'HELP' for detailed instructions.

══════════════════════════════════════════════════════════════════════════════════"""
        self.write_message(header, append=False)
    
    def log_message(self, speaker, content, msg_type="info"):
        """Log a message with timestamp and formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji_map = {
            "world-agent": "🌍",
            "leader": "👑", 
            "player": "🕊️",
            "info": "ℹ️",
            "error": "❌",
            "success": "✅",
            "event": "⚡",
            "system": "🔧"
        }
        emoji = emoji_map.get(msg_type, "💬")
        
        # Format the message nicely
        if msg_type == "leader":
            message = f"\n[{timestamp}] {emoji} {speaker}:\n   \"{content}\""
        elif msg_type == "player":
            message = f"\n[{timestamp}] {emoji} UN Secretary-General:\n   \"{content}\""
        elif msg_type == "event":
            message = f"\n[{timestamp}] {emoji} EVENT: {content}"
        else:
            message = f"\n[{timestamp}] {emoji} {speaker}: {content}"
        
        self.write_message(message)
        
        # Add TTS note if applicable
        if msg_type in ["leader", "event"]:
            self.write_message(f"   🔊 [TTS audio generated]")
    
    def check_server(self):
        """Check if server is running"""
        try:
            response = requests.get(f"{self.server_url}/api/tts/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_new_game(self):
        """Start a new game session"""
        try:
            response = requests.post(f"{self.server_url}/api/new-game")
            if response.status_code == 200:
                data = response.json()
                self.session_id = data['session_id']
                self.world_state = data['world_state']
                self.log_message("System", f"New diplomatic simulation started! Session ID: {self.session_id}", "success")
                self.display_world_status()
                return True
            else:
                self.log_message("System", "Failed to start new game", "error")
                return False
        except Exception as e:
            self.log_message("System", f"Error starting game: {e}", "error")
            return False
    
    def display_world_status(self):
        """Display current world status with nice formatting"""
        if not self.world_state:
            return
        
        self.log_message("System", "══════════════════════════════════════════════════════════════════════════════════", "info")
        self.log_message("System", "🏛️ WORLD LEADERS:", "info")
        
        # Display leaders with nice formatting
        for code, country in self.world_state['countries'].items():
            leader = country['leader']
            dominant_trait = max(leader['traits'].items(), key=lambda x: x[1])[0]
            self.log_message(f"Leader {code}", f"{leader['name']} ({dominant_trait}) - Economic Power: {leader['econ_power']:.2f}, Military Power: {leader['war_power']:.2f}, Population: {leader['population']/1000000:.1f}M", "leader")
        
        # Display events
        if self.world_state['events']:
            self.log_message("System", "⚡ CURRENT CRISES:", "info")
            for event in self.world_state['events']:
                status = "RESOLVED" if event['resolved'] else "ADDRESSED" if event['addressed'] else "ACTIVE"
                status_emoji = "✅" if event['resolved'] else "🔄" if event['addressed'] else "⚠️"
                self.log_message("Event", f"{status_emoji} {event['title']} ({status})", "event")
                self.log_message("Event", f"   {event['description']}", "event")
        else:
            self.log_message("System", "No active crises at this time.", "info")
        
        self.log_message("System", "══════════════════════════════════════════════════════════════════════════════════", "info")
    
    def start_meeting(self):
        """Start a diplomatic meeting"""
        if not self.session_id:
            self.log_message("System", "No active game session. Use START first.", "error")
            return False
        
        if not self.selected_events:
            self.log_message("System", "No events selected. Use SELECT <event_id> to choose events.", "error")
            return False
        
        self.is_in_meeting = True
        self.current_round = 1
        self.log_message("System", f"🏛️ DIPLOMATIC MEETING COMMENCED - Round {self.current_round} of {self.max_rounds}", "success")
        self.log_message("System", "The world leaders are gathering to address the selected crises...", "world-agent")
        return self.conduct_round()
    
    def conduct_round(self):
        """Conduct a round of the meeting"""
        if not self.session_id:
            return False
        
        try:
            response = requests.post(f"{self.server_url}/api/conduct-round", json={
                'session_id': self.session_id,
                'selected_event_ids': self.selected_events,
                'round_num': self.current_round
            })
            
            if response.status_code == 200:
                data = response.json()
                self.world_state = data['world_state']
                
                # Display leader responses
                for resp in data['responses']:
                    if resp['type'] == 'leader':
                        self.log_message(resp['speaker'], resp['content'], "leader")
                
                self.log_message("System", "Your turn to respond, Secretary-General. Use RESPOND <message> to speak.", "world-agent")
                return True
            else:
                self.log_message("System", "Failed to conduct round", "error")
                return False
        except Exception as e:
            self.log_message("System", f"Error conducting round: {e}", "error")
            return False
    
    def send_player_message(self, message):
        """Send a player message"""
        if not self.session_id or not self.is_in_meeting:
            self.log_message("System", "No active meeting. Use MEETING to start one.", "error")
            return False
        
        self.log_message("UN Secretary-General", message, "player")
        
        try:
            response = requests.post(f"{self.server_url}/api/conduct-round", json={
                'session_id': self.session_id,
                'selected_event_ids': self.selected_events,
                'round_num': self.current_round,
                'player_message': message
            })
            
            if response.status_code == 200:
                data = response.json()
                self.world_state = data['world_state']
                self.log_message("System", "Message delivered. The leaders are considering your diplomatic response.", "world-agent")
                return True
            else:
                self.log_message("System", "Failed to send message", "error")
                return False
        except Exception as e:
            self.log_message("System", f"Error sending message: {e}", "error")
            return False
    
    def next_round(self):
        """Move to next round"""
        if not self.is_in_meeting:
            self.log_message("System", "No active meeting", "error")
            return False
        
        if self.current_round < self.max_rounds:
            self.current_round += 1
            self.log_message("System", f"🔄 Moving to Round {self.current_round} of {self.max_rounds}", "info")
            return self.conduct_round()
        else:
            return self.end_meeting()
    
    def end_meeting(self):
        """End the current meeting"""
        if not self.session_id:
            return False
        
        try:
            response = requests.post(f"{self.server_url}/api/end-meeting", json={
                'session_id': self.session_id,
                'selected_event_ids': self.selected_events
            })
            
            if response.status_code == 200:
                data = response.json()
                self.world_state = data['world_state']
                outcomes = data['outcomes']
                
                self.log_message("System", "🏛️ MEETING ADJOURNED - Analyzing diplomatic outcomes...", "world-agent")
                self.log_message("Meeting Analysis", outcomes.get('summary', 'No summary available'), "world-agent")
                
                if outcomes.get('audio_base64'):
                    self.log_message("System", "🔊 [TTS audio generated for meeting outcomes]", "info")
                
                self.is_in_meeting = False
                self.current_round = 0
                self.selected_events = []
                return True
            else:
                self.log_message("System", "Failed to end meeting", "error")
                return False
        except Exception as e:
            self.log_message("System", f"Error ending meeting: {e}", "error")
            return False
    
    def time_skip(self):
        """Advance time by 6 months"""
        if not self.session_id:
            self.log_message("System", "No active game session", "error")
            return False
        
        try:
            response = requests.post(f"{self.server_url}/api/time-skip", json={
                'session_id': self.session_id
            })
            
            if response.status_code == 200:
                data = response.json()
                self.world_state = data['world_state']
                self.log_message("System", "⏰ SIX MONTHS LATER...", "world-agent")
                self.log_message("System", "The world situation has evolved. New challenges and opportunities await.", "world-agent")
                self.display_world_status()
                return True
            else:
                self.log_message("System", "Failed to advance time", "error")
                return False
        except Exception as e:
            self.log_message("System", f"Error advancing time: {e}", "error")
            return False
    
    def select_event(self, event_id):
        """Select an event for the meeting"""
        if not self.world_state:
            self.log_message("System", "No active game session", "error")
            return False
        
        event_ids = [e['eid'] for e in self.world_state['events']]
        if event_id not in event_ids:
            self.log_message("System", f"Event {event_id} not found", "error")
            return False
        
        if event_id in self.selected_events:
            self.selected_events.remove(event_id)
            self.log_message("System", f"Event {event_id} deselected for meeting", "info")
        else:
            self.selected_events.append(event_id)
            self.log_message("System", f"Event {event_id} selected for meeting", "success")
        
        return True
    
    def show_help(self):
        """Show help information"""
        help_text = """
══════════════════════════════════════════════════════════════════════════════════
📖 DETAILED HELP:

🚀 GAME CONTROL:
   START          - Begin a new diplomatic simulation
   STATUS         - Show current world status and leaders
   TIME           - Advance time by 6 months

🏛️ MEETING CONTROL:
   SELECT <ID>    - Select/deselect event for meeting (e.g., SELECT E1)
   MEETING        - Start diplomatic meeting with selected events
   RESPOND <MSG>  - Send diplomatic message (e.g., RESPOND We must cooperate)
   SKIP           - Skip your turn
   NEXT           - Move to next round
   END            - End current meeting

ℹ️ UTILITY:
   HELP           - Show this help message
   QUIT           - Exit the simulation

🔊 TTS FEATURES:
   • All leader responses generate natural speech
   • Event announcements with TTS narration
   • Meeting outcomes with voice summaries
   • Audio is queued and plays sequentially

💡 GAME FLOW:
   1. START → Begin simulation
   2. STATUS → Review world situation
   3. SELECT → Choose events to address
   4. MEETING → Start negotiations
   5. RESPOND → Send diplomatic messages
   6. NEXT → Continue through rounds
   7. END → Conclude meeting
   8. TIME → Advance world timeline
══════════════════════════════════════════════════════════════════════════════════"""
        self.log_message("System", help_text, "info")
    
    def run(self):
        """Main interface loop"""
        self.clear_messages()
        
        if not self.check_server():
            self.log_message("System", "❌ Server not running. Please start the server first.", "error")
            return
        
        self.log_message("System", "✅ Server connected. Ready to begin diplomatic negotiations.", "success")
        
        while True:
            try:
                command = input("\n🎮 Command: ").strip().upper()
                
                if command == "QUIT":
                    self.log_message("System", "Exiting simulation. Thank you for your diplomatic service!", "info")
                    break
                elif command == "START":
                    self.start_new_game()
                elif command == "MEETING":
                    self.start_meeting()
                elif command == "SKIP":
                    self.log_message("System", "Turn skipped", "info")
                elif command == "NEXT":
                    self.next_round()
                elif command == "END":
                    self.end_meeting()
                elif command == "TIME":
                    self.time_skip()
                elif command == "STATUS":
                    self.display_world_status()
                elif command == "HELP":
                    self.show_help()
                elif command.startswith("RESPOND "):
                    message = command[8:]  # Remove "RESPOND " prefix
                    self.send_player_message(message)
                elif command.startswith("SELECT "):
                    event_id = command[7:]  # Remove "SELECT " prefix
                    self.select_event(event_id)
                else:
                    self.log_message("System", f"Unknown command: {command}. Type HELP for available commands.", "error")
                    
            except KeyboardInterrupt:
                self.log_message("System", "Interrupted. Type QUIT to exit.", "info")
            except Exception as e:
                self.log_message("System", f"Error: {e}", "error")

if __name__ == "__main__":
    interface = TextInterface()
    interface.run() 