// Advanced diplomatic simulation game with Claude API integration
class DiplomaticGame {
    constructor() {
        this.sessionId = null;
        this.world = null;
        this.selectedEvents = [];
        this.currentRound = 0;
        this.maxRounds = 3;
        this.maxMeetings = 2; // Maximum number of meetings total
        this.isInMeeting = false;
        this.meetingNumber = 0;
        this.isLoading = false;
        this.ttsEnabled = true; // TTS toggle
        this.audioQueue = []; // Queue for TTS audio
        this.isPlayingAudio = false; // Track if audio is currently playing
        
        this.initializeGame();
        this.setupEventListeners();
    }
    
    async initializeGame() {
        this.setLoading(true);
        this.updateStatus("Initializing world with Claude AI...");
        
        try {
            const response = await fetch('/api/new-game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            this.sessionId = data.session_id;
            this.world = data.world_state;
            
            this.renderLeaders();
            this.renderEvents();
            await this.addMessage("🌍 World Agent", "Welcome to the UN Diplomatic Simulation powered by Claude AI. The world leaders have gathered for crisis management.", "world-agent");
            this.updateStatus("World initialized. Select events and start your first meeting.");
        } catch (error) {
            console.error('Failed to initialize game:', error);
            await this.addMessage("🌍 World Agent", "Error connecting to AI backend. Please refresh and try again.", "world-agent");
            this.updateStatus("Connection error. Please refresh the page.");
        } finally {
            this.setLoading(false);
        }
    }
    
    renderLeaders() {
        const container = document.getElementById('leaders-list');
        container.innerHTML = '';
        
        Object.values(this.world.countries).forEach(country => {
            const leader = country.leader;
            const dominantTrait = Object.entries(leader.traits)
                .reduce((a, b) => leader.traits[a[0]] > leader.traits[b[0]] ? a : b)[0];
            
            const relationships = Object.entries(country.relationships)
                .map(([code, value]) => `${code}:${value.toFixed(1)}`)
                .join(', ');
            
            const card = document.createElement('div');
            card.className = 'leader-card';
            card.innerHTML = `
                <div class="leader-name">${leader.name} (${dominantTrait})</div>
                <div class="leader-stats">
                    Country: ${country.code}<br>
                    Econ: ${leader.econ_power.toFixed(2)} | War: ${leader.war_power.toFixed(2)}<br>
                    Pop: ${(leader.population / 1000000).toFixed(1)}M<br>
                    Relations: ${relationships || 'None'}<br>
                    <small style="color: #666; font-style: italic;">${leader.backstory}</small>
                </div>
            `;
            container.appendChild(card);
        });
    }
    
    renderEvents() {
        const container = document.getElementById('events-list');
        container.innerHTML = '';
        
        this.world.events.forEach(event => {
            const card = document.createElement('div');
            card.className = 'event-card';
            card.dataset.eventId = event.eid;
            
            if (this.selectedEvents.includes(event.eid)) {
                card.classList.add('selected');
            }
            
            const statusText = event.resolved ? ' (RESOLVED)' : event.addressed ? ' (ADDRESSED)' : '';
            
            card.innerHTML = `
                <div class="event-title">${event.title}${statusText}</div>
                <div class="event-description">${event.description}</div>
                <small style="color: #888;">Type: ${event.e_type} | Cycles: ${event.cycles_alive}</small>
            `;
            
            card.addEventListener('click', () => this.toggleEventSelection(event.eid));
            container.appendChild(card);
            
            // Play TTS audio for new events (events with audio_base64 that haven't been played yet)
            if (event.audio_base64 && !event.audio_played) {
                // Mark as played to avoid repeating
                event.audio_played = true;
                // Add to audio queue with a delay
                setTimeout(() => {
                    this.playAudioFromBase64(event.audio_base64);
                }, 1000);
            }
        });
    }
    
    toggleEventSelection(eventId) {
        if (this.isInMeeting || this.isLoading) return;
        
        const index = this.selectedEvents.indexOf(eventId);
        if (index > -1) {
            this.selectedEvents.splice(index, 1);
        } else {
            this.selectedEvents.push(eventId);
        }
        this.renderEvents();
    }
    
    setupEventListeners() {
        document.getElementById('start-meeting').addEventListener('click', () => this.startMeeting());
        document.getElementById('send-message').addEventListener('click', () => this.sendPlayerMessage());
        document.getElementById('skip-turn').addEventListener('click', () => this.skipPlayerTurn());
        document.getElementById('next-round').addEventListener('click', () => this.nextRound());
        document.getElementById('end-meeting').addEventListener('click', () => this.endMeeting());
        
        // Enter key support for player input
        document.getElementById('player-message').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isLoading) {
                this.sendPlayerMessage();
            }
        });
    }
    
    async startMeeting() {
        if (this.selectedEvents.length === 0) {
            alert('Please select at least one event to address in the meeting.');
            return;
        }
        
        this.isInMeeting = true;
        this.currentRound = 1;
        this.meetingNumber++;
        
        // Clear any pending audio from previous meetings
        this.clearAudioQueue();
        
        const eventTitles = this.selectedEvents.map(id => 
            this.world.events.find(e => e.eid === id)?.title
        ).join('; ');
        
        await this.addMessage("🌍 World Agent", `Meeting ${this.meetingNumber} has begun. Addressing: ${eventTitles}`, "world-agent");
        this.updateStatus(`Meeting ${this.meetingNumber} - Round ${this.currentRound} of ${this.maxRounds}`);
        
        // Update UI
        document.getElementById('start-meeting').disabled = true;
        document.getElementById('player-controls').classList.remove('hidden');
        document.getElementById('meeting-controls').classList.remove('hidden');
        
        // Start first round
        await this.conductRound();
    }
    
    async conductRound() {
        this.setLoading(true);
        await this.addMessage("🌍 World Agent", `Round ${this.currentRound}: Leaders are discussing the selected issues with Claude AI...`, "world-agent");
        
        try {
            const response = await fetch('/api/conduct-round', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    selected_event_ids: this.selectedEvents,
                    round_num: this.currentRound
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update world state
            this.world = data.world_state;
            this.renderLeaders();
            
            // Display AI responses with staggered timing
            for (let i = 0; i < data.responses.length; i++) {
                setTimeout(async () => {
                    const response = data.responses[i];
                    await this.addMessage(response.speaker, response.content, response.type);
                    
                    // Play TTS audio for leader responses with delay
                    if (response.type === 'leader' && response.audio_base64) {
                        // Add a small delay before playing audio to ensure message is displayed first
                        setTimeout(() => {
                            this.playAudioFromBase64(response.audio_base64);
                        }, 500);
                    }
                }, (i + 1) * 2000); // Increased delay between responses
            }
            
            // Enable player input after all responses and audio
            setTimeout(async () => {
                await this.addMessage("🌍 World Agent", "Your turn to respond, Secretary-General.", "world-agent");
                this.setLoading(false);
            }, data.responses.length * 2000 + 2000); // Longer delay to account for audio
            
        } catch (error) {
            console.error('Failed to conduct round:', error);
            await this.addMessage("🌍 World Agent", "Error communicating with AI backend. Please try again.", "world-agent");
            this.setLoading(false);
        }
    }
    
    async sendPlayerMessage() {
        const input = document.getElementById('player-message');
        const message = input.value.trim();
        
        if (message && !this.isLoading) {
            this.addMessage("UN Secretary-General", message, "player");
            input.value = '';
            
            this.setLoading(true);
            
            try {
                // Send player message to backend for AI processing
                const response = await fetch('/api/conduct-round', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        selected_event_ids: this.selectedEvents,
                        round_num: this.currentRound,
                        player_message: message
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Update world state
                this.world = data.world_state;
                this.renderLeaders();
                
                setTimeout(() => {
                    this.addMessage("🌍 World Agent", "The leaders consider your diplomatic intervention carefully.", "world-agent");
                    this.setLoading(false);
                }, 1000);
                
            } catch (error) {
                console.error('Failed to send player message:', error);
                this.addMessage("🌍 World Agent", "Error processing your message. Please try again.", "world-agent");
                this.setLoading(false);
            }
        }
    }
    
    skipPlayerTurn() {
        if (!this.isLoading) {
            this.addMessage("🌍 World Agent", "The Secretary-General observes the discussion.", "world-agent");
        }
    }
    
    async nextRound() {
        if (this.currentRound < this.maxRounds) {
            this.currentRound++;
            this.updateStatus(`Meeting ${this.meetingNumber} - Round ${this.currentRound} of ${this.maxRounds}`);
            await this.conductRound();
        } else {
            await this.endMeeting();
        }
    }
    
    async endMeeting() {
        this.setLoading(true);
        this.isInMeeting = false;
        
        this.addMessage("🌍 World Agent", "The meeting has concluded. Claude AI is analyzing outcomes and consequences...", "world-agent");
        
        try {
            const response = await fetch('/api/end-meeting', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    selected_event_ids: this.selectedEvents
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update world state
            this.world = data.world_state;
            this.renderLeaders();
            this.renderEvents();
            
            // Display outcomes
            const outcomes = data.outcomes;
            this.addMessage("🌍 World Agent", `Meeting Analysis: ${outcomes.summary}`, "world-agent");
            
            // Play TTS audio for meeting outcomes with delay
            if (outcomes.audio_base64) {
                setTimeout(() => {
                    this.playAudioFromBase64(outcomes.audio_base64);
                }, 1000); // Delay to ensure message is displayed first
            }
            
            // Reset for next meeting
            this.selectedEvents = [];
            this.currentRound = 0;
            
            // Update UI
            document.getElementById('start-meeting').disabled = false;
            document.getElementById('player-controls').classList.add('hidden');
            document.getElementById('meeting-controls').classList.add('hidden');
            
            this.updateStatus("Meeting ended. Preparing time skip...");
            
            // Time skip after a brief pause
            setTimeout(() => {
                this.timeSkip();
            }, 3000);
            
        } catch (error) {
            console.error('Failed to end meeting:', error);
            this.addMessage("🌍 World Agent", "Error analyzing meeting outcomes. Please refresh and try again.", "world-agent");
            this.setLoading(false);
        }
    }
    
    async timeSkip() {
        this.setLoading(true);
        this.addMessage("🌍 World Agent", "=== Six months later ===", "world-agent");
        this.addMessage("🌍 World Agent", "Claude AI is evolving the world situation...", "world-agent");
        
        try {
            const response = await fetch('/api/time-skip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update world state
            this.world = data.world_state;
            this.renderLeaders();
            this.renderEvents();
            
            this.addMessage("🌍 World Agent", "The world situation has evolved. New challenges await your attention.", "world-agent");
            
            if (this.world.meeting_number >= this.maxMeetings) {
                this.endGame();
            } else {
                this.updateStatus("Time skip complete. Select events for the next meeting.");
            }
            
        } catch (error) {
            console.error('Failed to time skip:', error);
            this.addMessage("🌍 World Agent", "Error evolving world state. Please refresh and try again.", "world-agent");
        } finally {
            this.setLoading(false);
        }
    }
    
    async endGame() {
        await this.addMessage("🌍 World Agent", "=== Simulation Complete ===", "world-agent");
        
        // Generate final country statistics
        let statsReport = "📊 **FINAL WORLD STATE REPORT**\n\n";
        Object.values(this.world.countries).forEach(country => {
            const leader = country.leader;
            const relationships = Object.entries(country.relationships)
                .map(([code, value]) => `${code}: ${value.toFixed(1)}`)
                .join(', ');
            
            statsReport += `🏛️ **Country ${country.code}** - Leader: ${leader.name}\n`;
            statsReport += `   💰 Economic Power: ${leader.econ_power.toFixed(2)} | ⚔️ Military Power: ${leader.war_power.toFixed(2)}\n`;
            statsReport += `   👥 Population: ${(leader.population / 1000000).toFixed(1)}M | 🤝 Relations: ${relationships}\n\n`;
        });
        
        await this.addMessage("🌍 World Agent", statsReport, "world-agent");
        
        // Generate AI performance assessment
        this.setLoading(true);
        await this.addMessage("🌍 World Agent", "Claude AI is analyzing your diplomatic performance...", "world-agent");
        
        try {
            const response = await fetch('/api/generate-final-assessment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Display the AI-generated assessment
            await this.addMessage("🌍 World Agent", `📋 **DIPLOMATIC PERFORMANCE ASSESSMENT**\n\n${data.assessment}`, "world-agent");
            
        } catch (error) {
            console.error('Failed to generate assessment:', error);
            // Fallback assessment
            await this.addMessage("🌍 World Agent", "📋 **DIPLOMATIC PERFORMANCE ASSESSMENT**\n\nYour tenure as UN Secretary-General demonstrated commitment to international cooperation. Through diplomatic engagement, you helped navigate complex global challenges and facilitated dialogue between world leaders.", "world-agent");
        } finally {
            this.setLoading(false);
        }
        

        this.updateStatus("Simulation complete! Refresh the page to start a new scenario.");
        
        // Disable all controls
        document.getElementById('start-meeting').disabled = true;
        document.querySelectorAll('.event-card').forEach(card => {
            card.style.pointerEvents = 'none';
            card.style.opacity = '0.6';
        });
    }
    
    async addMessage(speaker, content, type) {
        const chatArea = document.getElementById('chat-area');
        const message = document.createElement('div');
        message.className = `message ${type}`;
        
        message.innerHTML = `
            <div class="speaker">${speaker}</div>
            <div class="content">${content}</div>
        `;
        
        chatArea.appendChild(message);
        chatArea.scrollTop = chatArea.scrollHeight;
        
        // Generate TTS audio for world agent messages
        if (type === 'world-agent' && this.ttsEnabled) {
            try {
                const response = await fetch('/api/tts/world-agent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: content })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.audio_base64) {
                        // Add a small delay before playing audio
                        setTimeout(() => {
                            this.playAudioFromBase64(data.audio_base64);
                        }, 500);
                    }
                }
            } catch (error) {
                console.error('Failed to generate TTS for world agent message:', error);
            }
        }
    }
    
    updateStatus(text) {
        document.getElementById('status').textContent = text;
    }
    
    setLoading(isLoading) {
        this.isLoading = isLoading;
        const buttons = document.querySelectorAll('.btn');
        const input = document.getElementById('player-message');
        
        buttons.forEach(btn => {
            btn.disabled = isLoading;
        });
        
        if (input) {
            input.disabled = isLoading;
        }
        
        if (isLoading) {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.id = 'loading-indicator';
            loadingDiv.textContent = 'Claude AI is thinking';
            
            const statusDiv = document.getElementById('status');
            if (!document.getElementById('loading-indicator')) {
                statusDiv.appendChild(loadingDiv);
            }
        } else {
            const loadingDiv = document.getElementById('loading-indicator');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }
    }
    
    // TTS Audio Functions
    playAudioFromBase64(audioBase64) {
        if (!this.ttsEnabled || !audioBase64) return;
        
        // Add to queue instead of playing immediately
        this.audioQueue.push(audioBase64);
        this.processAudioQueue();
    }
    
    processAudioQueue() {
        if (this.isPlayingAudio || this.audioQueue.length === 0) return;
        
        this.isPlayingAudio = true;
        this.showAudioIndicator();
        const audioBase64 = this.audioQueue.shift();
        
        try {
            // Convert base64 to audio blob
            const audioData = atob(audioBase64);
            const audioArray = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
                audioArray[i] = audioData.charCodeAt(i);
            }
            
            const audioBlob = new Blob([audioArray], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create and play audio
            const audio = new Audio(audioUrl);
            
            // When audio ends, play next in queue
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                this.isPlayingAudio = false;
                this.hideAudioIndicator();
                this.processAudioQueue(); // Play next audio in queue
            };
            
            // Handle errors
            audio.onerror = () => {
                URL.revokeObjectURL(audioUrl);
                this.isPlayingAudio = false;
                this.hideAudioIndicator();
                this.processAudioQueue(); // Try next audio in queue
            };
            
            audio.play();
            
        } catch (error) {
            console.error('Error playing TTS audio:', error);
            this.isPlayingAudio = false;
            this.hideAudioIndicator();
            this.processAudioQueue(); // Try next audio in queue
        }
    }
    
    showAudioIndicator() {
        const indicator = document.getElementById('audio-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    }
    
    hideAudioIndicator() {
        const indicator = document.getElementById('audio-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    clearAudioQueue() {
        this.audioQueue = [];
        this.isPlayingAudio = false;
        this.hideAudioIndicator();
    }
    
    toggleTTS() {
        this.ttsEnabled = !this.ttsEnabled;
        const button = document.getElementById('toggle-tts');
        if (button) {
            button.textContent = this.ttsEnabled ? '🔊 TTS ON' : '🔇 TTS OFF';
            button.className = this.ttsEnabled ? 'btn btn-secondary' : 'btn btn-secondary muted';
        }
        console.log(`TTS ${this.ttsEnabled ? 'enabled' : 'disabled'}`);
    }
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.game = new DiplomaticGame();
}); 