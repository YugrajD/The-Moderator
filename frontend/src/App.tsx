import React, { useState } from 'react'
import axios from 'axios'
import MapDisplay, { Nation } from './components/MapDisplay'
import NationList from './components/NationList'
import AgentMeetingModal from './components/AgentMeetingModal'

const API_BASE_URL = 'http://localhost:8000'

// --- Interfaces ---
interface MapData {
  width: number
  height: number
  regions: any[]
  borders: any[]
}

interface GameState {
  map_data: MapData | null
  nations: Nation[] | null
  diplomatic_relations: any; // Added to hold the relations data
  event_log: string[];
  agent_world_initialized?: boolean;
  current_meeting?: any;
}

interface DateState {
  year: number;
  season: 'Summer' | 'Winter';
}

function App() {
  const [gameState, setGameState] = useState<GameState>({ map_data: null, nations: null, diplomatic_relations: {}, event_log: [] })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [numNations, setNumNations] = useState(4)
  const [gameStarted, setGameStarted] = useState(false)
  const [showNationList, setShowNationList] = useState(false)
  const [currentDate, setCurrentDate] = useState<DateState>({ year: 2025, season: 'Summer' });
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const [showAgentMeeting, setShowAgentMeeting] = useState(false);

  const handleGoHome = () => {
    setGameStarted(false);
    setGameState({ map_data: null, nations: null, diplomatic_relations: {}, event_log: [] });
    setShowNationList(false);
  }

  const handleStartGame = async () => {
    setIsLoading(true)
    setError(null)
    setShowNationList(false)
    setCurrentDate({ year: 2025, season: 'Summer' }); // Reset date on new game

    try {
      // Use window dimensions for the map
      const response = await axios.post(`${API_BASE_URL}/initialize-game`, {
        regions: numNations,
        width: window.innerWidth,
        height: window.innerHeight,
      })
      setGameState(response.data)
      setGameStarted(true) // This triggers the view change
      
      // Check if there's an active agent meeting to show immediately
      if (response.data.current_meeting) {
        setShowAgentMeeting(true);
      }
    } catch (err: any) {
      console.error('Error starting game:', err)
      setError(err.response?.data?.detail || 'Failed to start the game. Is the backend server running?')
      setGameStarted(false) // Ensure we stay on the setup screen if it fails
    } finally {
      setIsLoading(false)
    }
  }

  const handleAdvanceTime = async () => {
    setIsLoading(true);
    setError(null);
    setShowAgentMeeting(false);

    try {
      const response = await axios.post(`${API_BASE_URL}/advance-time`, gameState);
      
      const newGameState = response.data;
      setGameState(newGameState);

      // Check if there's an active agent meeting
      if (newGameState.current_meeting) {
        setShowAgentMeeting(true);
      }

      // Advance the date by 6 months
      setCurrentDate(prevDate => {
        if (prevDate.season === 'Summer') {
          return { year: prevDate.year, season: 'Winter' };
        } else {
          return { year: prevDate.year + 1, season: 'Summer' };
        }
      });

    } catch (err: any) {
      console.error('Error advancing time:', err);
      setError(err.response?.data?.detail || 'Failed to advance time. An error occurred in the simulation.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndAgentMeeting = () => {
    setShowAgentMeeting(false);
    // The meeting consequences will be applied when the meeting ends
  };

  const GameControls = () => (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg">
      <h2 className="text-xl font-bold mb-4">Game Controls</h2>
      <div className="flex flex-col gap-4">
        <div>
          <label htmlFor="numNations" className="block text-sm font-medium text-gray-300 mb-1">
            Number of Nations: <span className="text-teal-300 font-bold">{numNations}</span>
          </label>
          <input
            type="range"
            id="numNations"
            min="2"
            max="4"
            value={numNations}
            onChange={(e) => setNumNations(parseInt(e.target.value, 10))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            disabled={isLoading}
          />
        </div>
        <button
          onClick={handleStartGame}
          disabled={isLoading}
          className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300 disabled:opacity-50 disabled:cursor-wait"
        >
          {isLoading ? 'Generating World...' : 'Start New Game'}
        </button>
        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
      </div>
    </div>
  )
  
  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col font-sans">
      {showAgentMeeting && gameState.current_meeting && (
        <AgentMeetingModal
          meetingData={gameState.current_meeting}
          onClose={() => setShowAgentMeeting(false)}
          onEndMeeting={handleEndAgentMeeting}
        />
      )}
      {!isHeaderVisible && gameStarted && (
        <button
          onClick={() => setIsHeaderVisible(true)}
          className="absolute top-2 right-2 z-30 bg-gray-700/80 p-2 rounded-full hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
          title="Show Header"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      )}

      {isHeaderVisible && (
        <header className="w-full mx-auto px-4 py-2 flex justify-between items-center bg-gray-800/50 backdrop-blur-sm z-10 shrink-0">
          <div onClick={handleGoHome} className="cursor-pointer">
            <h1 className="text-3xl font-bold text-teal-300">The Moderator</h1>
            <p className="text-sm text-gray-400">A Diplomatic Simulation Game</p>
          </div>
          <div className="flex items-center gap-4">
            {gameStarted && (
              <>
                <span className="text-lg font-semibold text-gray-300 bg-gray-700/50 px-3 py-1 rounded-md">
                  {currentDate.season} {currentDate.year}
                </span>
                <span className="text-gray-300">{`World with ${gameState.nations?.length || 0} Nations`}</span>
                <button
                  onClick={() => setShowNationList(!showNationList)}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300"
                >
                  {showNationList ? 'Hide Nations' : 'Show Nations'}
                </button>
                <button
                  onClick={handleAdvanceTime}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300 disabled:opacity-50"
                >
                  {isLoading ? 'Simulating...' : 'Advance Time (6 Months)'}
                </button>
                <button
                  onClick={handleStartGame}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300 disabled:opacity-50"
                >
                  {isLoading ? 'Generating...' : 'Generate New World'}
                </button>
              </>
            )}
            <button
              onClick={() => setIsHeaderVisible(false)}
              className="bg-gray-700/80 p-2 rounded-full hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-teal-500"
              title="Hide Header"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </header>
      )}

      {/* Main Content */}
      <main className="flex-1 flex w-full h-full mx-auto overflow-hidden">
        {!gameStarted ? (
          // --- PRE-GAME LAYOUT ---
          <div className="w-full flex items-center justify-center">
            <div className="w-full max-w-md p-8 bg-gray-800 rounded-lg shadow-2xl">
              <GameControls />
            </div>
          </div>
        ) : (
          // --- IN-GAME LAYOUT ---
          <div className="w-full h-full flex flex-col">
            <div className="flex-grow h-full absolute inset-0">
              <MapDisplay mapData={gameState.map_data} nations={gameState.nations} />
            </div>
            
            {showNationList && (
              <div className="absolute bottom-0 left-0 w-full bg-gray-900/80 backdrop-blur-md p-4 max-h-[40vh] overflow-y-auto z-20">
                <NationList nations={gameState.nations} isLoading={false} />
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default App 