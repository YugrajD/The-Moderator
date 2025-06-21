import React, { useState } from 'react'
import axios from 'axios'
import MapDisplay from './components/MapDisplay'
import NationList from './components/NationList'

const API_BASE_URL = 'http://localhost:8000'

// --- Interfaces ---
interface MapData {
  width: number
  height: number
  regions: any[]
  borders: any[]
}

interface LeaderProfile {
  name: string
  personality: string
  ambition: string
}

interface Nation {
  name: string
  government_type: string
  leader: LeaderProfile
  region_name: string
  terrain: string
  climate: string
}

interface GameState {
  map_data: MapData | null
  nations: Nation[] | null
}

function App() {
  const [gameState, setGameState] = useState<GameState>({ map_data: null, nations: null })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [numNations, setNumNations] = useState(8)
  const [gameStarted, setGameStarted] = useState(false)
  const [showNationList, setShowNationList] = useState(false)

  const handleStartGame = async () => {
    setIsLoading(true)
    setError(null)
    setShowNationList(false)

    try {
      // Use window dimensions for the map
      const response = await axios.post(`${API_BASE_URL}/initialize-game`, {
        regions: numNations,
        width: window.innerWidth,
        height: window.innerHeight,
      })
      setGameState(response.data)
      setGameStarted(true) // This triggers the view change
    } catch (err: any) {
      console.error('Error starting game:', err)
      setError(err.response?.data?.detail || 'Failed to start the game. Is the backend server running?')
      setGameStarted(false) // Ensure we stay on the setup screen if it fails
    } finally {
      setIsLoading(false)
    }
  }

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
            max="20"
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
      {/* Header */}
      <header className="w-full mx-auto px-4 py-2 flex justify-between items-center bg-gray-800/50 backdrop-blur-sm z-10">
        <div>
          <h1 className="text-3xl font-bold text-teal-300">The Moderator</h1>
          <p className="text-sm text-gray-400">A Diplomatic Simulation Game</p>
        </div>
        {gameStarted && (
          <div className="flex items-center gap-4">
            <span className="text-gray-300">{`World with ${gameState.nations?.length || 0} Nations`}</span>
            <button
              onClick={() => setShowNationList(!showNationList)}
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300"
            >
              {showNationList ? 'Hide Nations' : 'Show Nations'}
            </button>
            <button
              onClick={handleStartGame}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300 disabled:opacity-50"
            >
              {isLoading ? 'Generating...' : 'Generate New World'}
            </button>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="flex-1 flex w-full h-full mx-auto">
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