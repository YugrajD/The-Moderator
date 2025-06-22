# Google Text-to-Speech Integration

This project now includes Google Cloud Text-to-Speech (TTS) functionality, allowing the diplomacy simulation game to speak leader responses, event descriptions, and meeting outcomes.

## Setup

### 1. Prerequisites
- Google Cloud project with Text-to-Speech API enabled
- Service account credentials file (already provided: `directed-optics-463710-f9-8f48037d3fa8.json`)

### 2. Installation
The required dependencies are already installed:
```bash
pip install google-cloud-texttospeech==2.16.3
```

## API Endpoints

### 1. TTS Status
**GET** `/api/tts/status`
- Check if TTS service is available
- Returns: `{"available": true/false, "service_type": "Google Cloud Text-to-Speech"}`

### 2. Available Voices
**GET** `/api/tts/voices?language_code=en-US`
- Get list of available voices for a language
- Returns: `{"voices": [...], "language_code": "en-US"}`

### 3. Speech Synthesis
**POST** `/api/tts/synthesize`
- Convert text to speech
- Request body:
```json
{
    "text": "Text to convert to speech",
    "voice_name": "en-US-Neural2-F",
    "language_code": "en-US",
    "speaking_rate": 0.9
}
```
- Returns: `{"audio_base64": "...", "text": "...", "voice_name": "...", "language_code": "...", "speaking_rate": 0.9}`

## Usage Examples

### Python Test Script
Run the test script to verify TTS functionality:
```bash
python test_tts.py
```

### JavaScript Client
Use the provided JavaScript client in your frontend:

```javascript
// Initialize TTS client
const tts = new TTSClient('http://localhost:5000');

// Check status
const status = await tts.checkStatus();
console.log('TTS available:', status.available);

// Get available voices
const voices = await tts.getVoices('en-US');
console.log('Available voices:', voices);

// Convert text to speech and play
const audio = await tts.speak("Hello, this is a test!");
```

### Diplomacy Game Integration
Use the `DiplomacyTTS` class for game-specific functionality:

```javascript
const diplomacyTTS = new DiplomacyTTS();

// Initialize
await diplomacyTTS.initialize();

// Speak leader responses
await diplomacyTTS.speakLeaderResponse("Leader A", "We must address this crisis together.", "A");

// Speak events
await diplomacyTTS.speakEvent({
    title: "Economic Crisis",
    description: "A major economic downturn affects multiple nations."
});

// Speak meeting outcomes
await diplomacyTTS.speakOutcomes({
    summary: "The meeting resulted in new trade agreements."
});

// Toggle TTS on/off
diplomacyTTS.toggle();

// Update voice options
diplomacyTTS.updateVoiceOptions({
    voice_name: 'en-US-Neural2-M',
    speaking_rate: 1.1
});
```

## Voice Options

### Popular Voice Names
- `en-US-Neural2-F` - Female voice (default)
- `en-US-Neural2-M` - Male voice
- `en-US-Neural2-C` - Child voice
- `en-US-Neural2-D` - Deep male voice
- `en-US-Neural2-E` - Elderly voice
- `en-US-Neural2-G` - Young female voice

### Speaking Rate
- Range: 0.25 to 4.0
- 0.25 = Very slow
- 1.0 = Normal speed
- 4.0 = Very fast
- Default: 0.9 (slightly slower than normal)

### Language Codes
- `en-US` - English (US)
- `en-GB` - English (UK)
- `es-ES` - Spanish (Spain)
- `fr-FR` - French (France)
- `de-DE` - German (Germany)
- And many more...

## Error Handling

The TTS service includes comprehensive error handling:

1. **Service Unavailable**: Returns 503 if TTS is not initialized
2. **Invalid Request**: Returns 400 for missing or invalid parameters
3. **Synthesis Errors**: Returns 500 with error details for TTS failures
4. **Graceful Degradation**: Game continues to work even if TTS fails

## Security Notes

- The credentials file contains sensitive information - keep it secure
- In production, use environment variables or secure credential management
- The TTS service is rate-limited by Google Cloud quotas

## Troubleshooting

### Common Issues

1. **"TTS service not available"**
   - Check if credentials file exists and is valid
   - Verify Google Cloud project has TTS API enabled
   - Check service account permissions

2. **"TTS synthesis failed"**
   - Verify text is not empty or too long
   - Check voice name is valid
   - Ensure speaking rate is within range (0.25-4.0)

3. **Audio not playing**
   - Check browser audio permissions
   - Verify base64 decoding is working
   - Test with different voice options

### Debug Mode
Enable debug logging by setting the environment variable:
```bash
export GOOGLE_CLOUD_DEBUG=1
```

## Performance Considerations

- Audio files are returned as base64-encoded MP3
- Typical response size: 1-10KB per sentence
- Consider caching frequently used phrases
- Implement audio queue for multiple requests

## Future Enhancements

- SSML support for more advanced speech control
- Multiple voice support for different leaders
- Audio caching and compression
- Real-time streaming audio
- Voice cloning for unique leader voices 