import React from 'react';
import { Nation } from './MapDisplay'; // Import the unified Nation type
import Flag from './Flag'; // Import the new Flag component

interface NationListProps {
  nations: Nation[] | null;
  isLoading: boolean;
}

const NationList: React.FC<NationListProps> = ({ nations, isLoading }) => {
  if (isLoading) {
    return <div className="text-center p-4">Inspecting the entrails...</div>;
  }

  if (!nations || nations.length === 0) {
    return <div className="text-center p-4">No nations have been formed yet.</div>;
  }

  return (
    <div className="bg-gray-800/80 p-4 rounded-lg shadow-lg h-full overflow-y-auto">
      <h2 className="text-2xl font-bold mb-4 text-teal-300 text-center">The Nations of the World</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {nations.map((nation) => (
          <div key={nation.id} className="bg-gray-900 p-4 rounded-lg flex flex-col justify-between">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-teal-400">{nation.name}</h3>
                <p className="text-sm text-gray-400">{nation.government_type}</p>
              </div>
              <Flag nationId={nation.id} />
            </div>
            <div className="bg-gray-800 p-3 rounded-md my-2 flex items-center gap-3">
              <img
                src={`https://api.dicebear.com/8.x/personas/svg?seed=${nation.leader.name}`}
                alt={`Portrait of ${nation.leader.name}`}
                className="w-16 h-16 rounded-full bg-gray-700 border-2 border-gray-600"
              />
              <div>
                <p className="font-semibold text-gray-200">Leader: {nation.leader.name}</p>
                <p className="text-xs text-gray-400 italic">"{nation.leader.personality}"</p>
                <p className="text-sm text-amber-400 mt-1">Ambition: {nation.leader.ambition}</p>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500">Capital: {nation.capital_province_name}</p>
              <p className="text-xs text-gray-500">Provinces: {nation.provinces.length}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NationList; 