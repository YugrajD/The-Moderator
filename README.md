# UN Diplomatic Simulation - Web Version

A sophisticated diplomatic simulation powered by Claude AI where you act as the UN Secretary-General, mediating international crises between AI-powered world leaders.

## Features

- **AI-Powered Leaders**: Each country is led by a unique AI personality with distinct traits (honest, ambitious, empathetic, diplomatic, ruthless)
- **Dynamic World State**: Countries have evolving relationships, economic power, military strength, and populations
- **Complex Events**: Handle border disputes, economic crises, humanitarian disasters, and more
- **Real-Time Diplomacy**: Engage in multi-round diplomatic meetings with Claude AI generating realistic responses
- **Consequence System**: Your decisions have lasting impacts on the world state
- **Time Progression**: World evolves over multiple sessions with new challenges emerging

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Claude API key from Anthropic

### Installation

1. **Clone or download the project files**
   ```bash
   # Ensure you have these files:
   # - index.html
   # - game.js
   # - server.py
   # - requirements.txt
   # - .env.template
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the template file
   cp .env.template .env
   
   # Edit .env and add your Claude API key
   # Replace 'your_claude_api_key_here' with your actual API key
   ```

4. **Get a Claude API key**
   - Visit [Anthropic's website](https://www.anthropic.com/)
   - Sign up for an account and obtain an API key
   - Add the key to your `.env` file

### Running the Application

1. **Start the Flask backend**
   ```bash
   python server.py
   ```
   The server will start on `http://localhost:5000`

2. **Open the web application**
   - **Important**: Go to `http://localhost:5000` in your browser
   - **Do NOT** open `index.html` directly (this causes CORS errors)

**Alternative - Easy startup:**
```bash
python run.py
```
This will automatically start the server and open your browser to the correct URL.

### Game Instructions

1. **Start a New Game**
   - The game initializes with 3 countries, each with unique AI leaders
   - Leaders have different personality traits that influence their behavior

2. **Select Events**
   - Choose 1-3 events from the sidebar to address in your meeting
   - Events represent international crises requiring diplomatic intervention

3. **Conduct Diplomatic Meetings**
   - Start a meeting to begin multi-round discussions
   - AI leaders will discuss the selected events based on their personalities
   - Participate as the UN Secretary-General by sending messages

4. **Make Diplomatic Interventions**
   - Your words influence the leaders and can change relationship dynamics
   - Different approaches yield different outcomes

5. **Manage Consequences**
   - Addressed events may be resolved or evolve
   - Unaddressed events can escalate and cause problems
   - The world state evolves over time

6. **Progress Through Time**
   - After each meeting, the world advances by 6 months
   - New events emerge and relationships change
   - Your diplomatic legacy shapes the world's future

## Technical Details

### Architecture

- **Frontend**: Pure HTML/CSS/JavaScript
- **Backend**: Flask with Claude API integration
- **AI Engine**: Anthropic's Claude for generating leader personalities and responses

### API Endpoints

- `POST /api/new-game` - Initialize a new game session
- `POST /api/conduct-round` - Process a round of diplomatic discussion
- `POST /api/end-meeting` - Conclude a meeting and analyze outcomes
- `POST /api/time-skip` - Advance the world state by 6 months

### Game State

The game maintains a complex world state including:
- **Countries**: Economic power, military strength, population
- **Leaders**: Personality traits, backstories, ages
- **Relationships**: Dynamic diplomatic relations between countries
- **Events**: International crises with evolution over time

## Troubleshooting

### Common Issues

1. **"Connection error" message**
   - Ensure the Flask server is running on port 5000
   - Check that your Claude API key is correctly set in the `.env` file

2. **No AI responses**
   - Verify your Claude API key is valid and has sufficient credits
   - Check the browser console for JavaScript errors

3. **Flask server won't start**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that port 5000 is not in use by another application

### Development Notes

- The game uses session-based state management
- Each game session maintains an independent world state
- AI responses are generated in real-time using Claude API calls
- The frontend automatically handles loading states and error recovery

## Customization

### Adding New Events

Edit the `generate_events()` function in `server.py` to add new crisis scenarios.

### Modifying Leader Traits

Adjust the personality generation in the `generate_leader()` function to create different leader archetypes.

### Changing Game Flow

Modify the round limits, time skip intervals, or consequence systems in the `GameSession` class.

## Credits

Based on the original terminal-based diplomatic simulation. Adapted for web deployment with Claude AI integration for enhanced realism and dynamic storytelling. 