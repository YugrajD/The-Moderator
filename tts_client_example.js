/**
 * Google TTS Client Example
 * This file demonstrates how to use the TTS API from a JavaScript frontend
 */

class TTSClient {
    constructor(baseUrl = 'http://localhost:5001') {
        this.baseUrl = baseUrl;
    }

    /**
     * Check TTS service status
     */
    async checkStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/api/tts/status`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error checking TTS status:', error);
            throw error;
        }
    }

    /**
     * Get available voices
     */
    async getVoices(languageCode = 'en-US') {
        try {
            const response = await fetch(`${this.baseUrl}/api/tts/voices?language_code=${languageCode}`);
            const data = await response.json();
            return data.voices;
        } catch (error) {
            console.error('Error getting voices:', error);
            throw error;
        }
    }

    /**
     * Convert text to speech
     */
    async synthesizeSpeech(text, options = {}) {
        const {
            voice_name = 'en-US-Neural2-F',
            language_code = 'en-US',
            speaking_rate = 0.9
        } = options;

        try {
            const response = await fetch(`${this.baseUrl}/api/tts/synthesize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text,
                    voice_name,
                    language_code,
                    speaking_rate
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'TTS synthesis failed');
            }

            return data;
        } catch (error) {
            console.error('Error synthesizing speech:', error);
            throw error;
        }
    }

    /**
     * Play audio from base64 data
     */
    playAudio(audioBase64) {
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
            audio.play();
            
            // Clean up URL after playing
            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
            };
            
            return audio;
        } catch (error) {
            console.error('Error playing audio:', error);
            throw error;
        }
    }

    /**
     * Convert text to speech and play it immediately
     */
    async speak(text, options = {}) {
        try {
            const result = await this.synthesizeSpeech(text, options);
            return this.playAudio(result.audio_base64);
        } catch (error) {
            console.error('Error in speak function:', error);
            throw error;
        }
    }
}

// Example usage
async function exampleUsage() {
    const tts = new TTSClient();

    try {
        // Check if TTS is available
        const status = await tts.checkStatus();
        console.log('TTS Status:', status);

        if (!status.available) {
            console.error('TTS service is not available');
            return;
        }

        // Get available voices
        const voices = await tts.getVoices();
        console.log('Available voices:', voices.slice(0, 3)); // Show first 3

        // Speak some text
        const audio = await tts.speak(
            "Hello! This is a test of the Google Text-to-Speech service for the diplomacy simulation game.",
            {
                voice_name: 'en-US-Neural2-F',
                speaking_rate: 0.9
            }
        );

        console.log('Audio is playing...');

    } catch (error) {
        console.error('Example failed:', error);
    }
}

// Integration with diplomacy game
class DiplomacyTTS {
    constructor() {
        this.tts = new TTSClient();
        this.isEnabled = false;
        this.voiceOptions = {
            voice_name: 'en-US-Neural2-F',
            language_code: 'en-US',
            speaking_rate: 0.9
        };
    }

    /**
     * Initialize TTS for the diplomacy game
     */
    async initialize() {
        try {
            const status = await this.tts.checkStatus();
            this.isEnabled = status.available;
            
            if (this.isEnabled) {
                console.log('TTS initialized successfully');
            } else {
                console.warn('TTS is not available');
            }
            
            return this.isEnabled;
        } catch (error) {
            console.error('Failed to initialize TTS:', error);
            this.isEnabled = false;
            return false;
        }
    }

    /**
     * Speak a leader's response
     */
    async speakLeaderResponse(leaderName, response, countryCode) {
        if (!this.isEnabled) return;

        try {
            const text = `${leaderName} says: ${response}`;
            await this.tts.speak(text, this.voiceOptions);
        } catch (error) {
            console.error('Error speaking leader response:', error);
        }
    }

    /**
     * Speak event descriptions
     */
    async speakEvent(event) {
        if (!this.isEnabled) return;

        try {
            const text = `Breaking news: ${event.title}. ${event.description}`;
            await this.tts.speak(text, this.voiceOptions);
        } catch (error) {
            console.error('Error speaking event:', error);
        }
    }

    /**
     * Speak meeting outcomes
     */
    async speakOutcomes(outcomes) {
        if (!this.isEnabled) return;

        try {
            const text = `Meeting outcomes: ${outcomes.summary}`;
            await this.tts.speak(text, this.voiceOptions);
        } catch (error) {
            console.error('Error speaking outcomes:', error);
        }
    }

    /**
     * Toggle TTS on/off
     */
    toggle() {
        this.isEnabled = !this.isEnabled;
        console.log(`TTS ${this.isEnabled ? 'enabled' : 'disabled'}`);
        return this.isEnabled;
    }

    /**
     * Update voice options
     */
    updateVoiceOptions(options) {
        this.voiceOptions = { ...this.voiceOptions, ...options };
        console.log('Voice options updated:', this.voiceOptions);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TTSClient, DiplomacyTTS };
}

// Auto-run example if this file is loaded directly
if (typeof window !== 'undefined') {
    // Browser environment - make available globally
    window.TTSClient = TTSClient;
    window.DiplomacyTTS = DiplomacyTTS;
    
    // Uncomment to run example automatically
    // exampleUsage();
} 