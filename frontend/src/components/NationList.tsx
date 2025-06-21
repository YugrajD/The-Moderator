import React from 'react';

interface LeaderProfile {
  name: string;
  personality: string;
  ambition: string;
}

interface Nation {
  name: string;
  government_type: string;
  leader: LeaderProfile;
  region_name: string;
  terrain: string;
  climate: string;
}

interface NationListProps {
  nations: Nation[] | null;
  isLoading: boolean;
}

const NationList: React.FC<NationListProps> = ({ nations, isLoading }) => {
  if (isLoading) {
    return (
      <div className="w-full h-full bg-gray-800 p-4 rounded-lg overflow-y-auto">
        <h2 className="text-xl font-bold text-white mb-4">Nations</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-gray-700 p-4 rounded-lg">
              <div className="h-5 bg-gray-600 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-600 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!nations || nations.length === 0) {
    return (
      <div className="w-full h-full bg-gray-800 p-4 rounded-lg flex items-center justify-center">
        <p className="text-gray-400">No nations generated yet.</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-gray-800 p-4 rounded-lg overflow-y-auto">
      <h2 className="text-2xl font-bold text-white mb-6 text-center">The Nations of the World</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {nations.map((nation, index) => (
          <div
            key={index}
            className="bg-gray-700 rounded-lg shadow-lg p-5 transform hover:-translate-y-1 transition-transform duration-300"
          >
            <h3 className="text-lg font-bold text-teal-300 mb-2 truncate">{nation.name}</h3>
            <p className="text-sm text-gray-300 mb-3"><span className="font-semibold text-gray-400">Government:</span> {nation.government_type}</p>
            
            <div className="bg-gray-600 p-3 rounded-md mb-3">
                <p className="text-md font-semibold text-white">Leader: {nation.leader.name}</p>
                <p className="text-xs text-gray-400 italic">"{nation.leader.personality}"</p>
                <p className="text-sm text-amber-300 mt-2"><span className="font-semibold text-gray-400">Ambition:</span> {nation.leader.ambition}</p>
            </div>

            <div className="text-xs text-gray-400">
                <p><span className="font-semibold">Region:</span> {nation.region_name}</p>
                <p><span className="font-semibold">Terrain:</span> {nation.terrain}</p>
                <p><span className="font-semibold">Climate:</span> {nation.climate}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NationList; 