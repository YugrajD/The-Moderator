import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

interface LeaderResponse {
  leader_code: string;
  leader_name: string;
  response: string;
}

interface AgentMeetingData {
  event_title: string;
  event_description: string;
  leader_responses: LeaderResponse[];
  transcript: string[];
  meeting_complete: boolean;
}

interface AgentMeetingModalProps {
  meetingData: AgentMeetingData | null;
  onClose: () => void;
  onEndMeeting: () => void;
}

const AgentMeetingModal: React.FC<AgentMeetingModalProps> = ({ 
  meetingData, 
  onClose, 
  onEndMeeting 
}) => {
  const [playerInput, setPlayerInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [currentMeeting, setCurrentMeeting] = useState<AgentMeetingData | null>(meetingData);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setCurrentMeeting(meetingData);
  }, [meetingData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentMeeting?.transcript]);

  const handlePlayerInput = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerInput.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/agent/player-input`, {
        player_input: playerInput
      });
      
      setCurrentMeeting(response.data);
      setPlayerInput('');
    } catch (error) {
      console.error('Error sending player input:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEndMeeting = async () => {
    setIsSubmitting(true);
    try {
      await axios.post(`${API_BASE_URL}/agent/end-meeting`);
      onEndMeeting();
    } catch (error) {
      console.error('Error ending meeting:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!currentMeeting) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-teal-300 mb-2">
                Diplomatic Council
              </h2>
              <h3 className="text-lg text-gray-300 mb-1">
                {currentMeeting.event_title}
              </h3>
              <p className="text-gray-400 text-sm">
                {currentMeeting.event_description}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {currentMeeting.transcript.map((message, index) => {
            const isPlayer = message.startsWith('PLAYER:');
            const isLeader = /^[A-Z]:/.test(message);
            
            if (isPlayer) {
              return (
                <div key={index} className="flex justify-end">
                  <div className="bg-teal-600 text-white rounded-lg px-4 py-2 max-w-[70%]">
                    <div className="font-semibold text-sm mb-1">You</div>
                    <div>{message.replace('PLAYER: ', '')}</div>
                  </div>
                </div>
              );
            } else if (isLeader) {
              const leaderCode = message.charAt(0);
              const leaderName = currentMeeting.leader_responses.find(
                lr => lr.leader_code === leaderCode
              )?.leader_name || `Leader ${leaderCode}`;
              const response = message.substring(message.indexOf(':') + 2);
              
              return (
                <div key={index} className="flex justify-start">
                  <div className="bg-gray-700 text-white rounded-lg px-4 py-2 max-w-[70%]">
                    <div className="font-semibold text-sm mb-1 text-purple-300">
                      {leaderName} ({leaderCode})
                    </div>
                    <div>{response}</div>
                  </div>
                </div>
              );
            }
            return null;
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="p-6 border-t border-gray-700">
          <form onSubmit={handlePlayerInput} className="flex gap-4">
            <input
              type="text"
              value={playerInput}
              onChange={(e) => setPlayerInput(e.target.value)}
              placeholder="Enter your diplomatic response..."
              className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
              disabled={isSubmitting}
            />
            <button
              type="submit"
              disabled={isSubmitting || !playerInput.trim()}
              className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-6 rounded-lg transition-colors duration-300 disabled:opacity-50"
            >
              {isSubmitting ? 'Sending...' : 'Send'}
            </button>
            <button
              type="button"
              onClick={handleEndMeeting}
              disabled={isSubmitting}
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-6 rounded-lg transition-colors duration-300 disabled:opacity-50"
            >
              {isSubmitting ? 'Ending...' : 'End Meeting'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AgentMeetingModal; 