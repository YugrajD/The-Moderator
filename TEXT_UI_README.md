# Text-Based UN Diplomatic Simulation Interface

This is a text-based interface for the UN Diplomatic Simulation that uses `message.txt` as the UI while maintaining all TTS and game functionalities.

## Features

- **Text-based UI**: All game interactions are displayed in `message.txt`
- **Full TTS Support**: All leader responses, events, and meeting outcomes generate TTS audio
- **Complete Game Functionality**: All features from the web interface are available
- **Command-line Interface**: Simple text commands for game control
- **Real-time Updates**: Messages are written to `message.txt` in real-time

## Quick Start

### Option 1: Automatic Launcher (Recommended)
```bash
python run_text_ui.py
```

This will:
1. Check if the server is running
2. Start the server if needed
3. Launch the text interface

### Option 2: Manual Start
1. Start the server:
   ```bash
   python server.py
   ```

2. In another terminal, run the text interface:
   ```bash
   python text_interface.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `START` | Begin a new game |
| `MEETING` | Start a diplomatic meeting (requires selected events) |
| `RESPOND <message>` | Send a diplomatic message |
| `SKIP` | Skip your turn |
| `NEXT` | Move to next round |
| `END` | End current meeting |
| `TIME` | Advance time (6 months) |
| `STATUS` | Show current world status |
| `SELECT <event_id>` | Select/deselect event for meeting |
| `HELP` | Show help message |
| `QUIT` | Exit the simulation |

## Game Flow

1. **Start Game**: Use `START` to begin a new simulation
2. **Select Events**: Use `SELECT <event_id>` to choose which crises to address
3. **Start Meeting**: Use `MEETING` to begin diplomatic negotiations
4. **Respond**: Use `RESPOND <message>` to send diplomatic messages
5. **Continue**: Use `NEXT` to move through rounds
6. **End Meeting**: Use `END` to conclude negotiations
7. **Advance Time**: Use `TIME` to see how the world evolves

## TTS Features

The text interface maintains full TTS functionality:

- **Leader Responses**: Each leader's speech generates TTS audio
- **Event Announcements**: New events are announced with TTS
- **Meeting Outcomes**: Meeting summaries are narrated with TTS
- **Audio Logging**: TTS generation is noted in the message log

## File Structure

- `message.txt` - Main UI file (updated in real-time)
- `text_interface.py` - Text interface implementation
- `run_text_ui.py` - Automatic launcher
- `server.py` - Backend server (same as web interface)

## Example Session

```
Command: START
[09:15:30] ✅ System: New game started. Session ID: 1734876930
[09:15:30] ℹ️ System: === WORLD STATUS ===
[09:15:30] ℹ️ System: 🏛️ WORLD LEADERS:
[09:15:30] 👑 Leader A: Leader_A_42 (diplomatic) - Econ: 0.75, War: 0.45, Pop: 150.0M
[09:15:30] 👑 Leader B: Leader_B_17 (ambitious) - Econ: 0.82, War: 0.68, Pop: 89.0M
[09:15:30] 👑 Leader C: Leader_C_93 (empathetic) - Econ: 0.61, War: 0.33, Pop: 210.0M
[09:15:30] ℹ️ System: ⚡ CURRENT EVENTS:
[09:15:30] ℹ️ Event: Economic Crisis in Country A (ACTIVE) - Severe economic downturn affecting millions.

Command: SELECT E1
[09:15:31] ℹ️ System: Event E1 selected

Command: MEETING
[09:15:32] ✅ System: Meeting started. Round 1 of 3
[09:15:32] 👑 Leader A (diplomatic): We must address this crisis with careful diplomacy and international cooperation.
[09:15:32] ℹ️ System: [TTS audio generated for Leader A (diplomatic)]
[09:15:32] 🌍 System: Your turn to respond, Secretary-General.

Command: RESPOND I call upon all nations to work together in this time of crisis.
[09:15:33] 🕊️ UN Secretary-General: I call upon all nations to work together in this time of crisis.
[09:15:33] 🌍 System: Message sent. Leaders are considering your response.
```

## Advantages of Text Interface

1. **Lightweight**: No browser required
2. **Persistent Log**: All interactions saved to `message.txt`
3. **Scriptable**: Can be automated or integrated with other tools
4. **Accessible**: Works on any system with Python
5. **Full Functionality**: All TTS and game features preserved

## Troubleshooting

- **Server not running**: Use `python server.py` to start manually
- **Port conflicts**: The server runs on port 5001 by default
- **TTS errors**: Check Google Cloud credentials in `directed-optics-463710-f9-8f48037d3fa8.json`
- **File permissions**: Ensure write access to `message.txt`

## Requirements

- Python 3.7+
- Flask server running on port 5001
- Google Cloud TTS credentials
- Internet connection for TTS API calls 