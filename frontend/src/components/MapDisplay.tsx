import React from 'react';
import polylabel from 'polylabel';

interface Point {
  x: number;
  y: number;
}

interface Province {
  id: number;
  nationId: number;
  isCapital?: boolean;
  name: string;
  center: Point;
  polygon: Point[];
  terrain: string;
  area: number;
}

interface Nation {
  id: number;
  name: string;
}

interface MapData {
  width: number;
  height: number;
  regions: Province[];
  borders: any[];
}

interface MapDisplayProps {
  mapData: MapData | null;
  nations: Nation[] | null;
}

const TERRAIN_COLORS: { [key: string]: string } = {
  plains: '#90EE90', // lightgreen
  mountains: '#A9A9A9', // darkgray
  forest: '#228B22', // forestgreen
  desert: '#F4A460', // sandybrown
  swamp: '#556B2F', // darkolivegreen
  hills: '#D2B48C', // tan
  coastal: '#4682B4', // steelblue
  tundra: '#E0FFFF', // lightcyan
  water: '#1E90FF',  // dodgerblue
  default: '#CCCCCC'
};

// New, larger palette of distinct colors for nations
const NATION_COLORS = [
  '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', 
  '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9A6324', '#fffac8', '#800000', '#aaffc3', 
  '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#ffffff', '#000000'
];

const MapDisplay: React.FC<MapDisplayProps> = ({ mapData, nations }) => {
  if (!mapData || !nations) {
    return (
      <div className="flex items-center justify-center w-full h-full bg-gray-800 rounded-lg">
        <p className="text-gray-400">Generate a world to see the map.</p>
      </div>
    );
  }

  const { width, height, regions: provinces, borders } = mapData;

  // Create a color map for nations
  const nationColorMap = new Map<number, string>();
  nations.forEach((nation, index) => {
    nationColorMap.set(nation.id, NATION_COLORS[index % NATION_COLORS.length]);
  });
  
  // Find the capital province for each nation to place the label
  const capitals = provinces.filter((p: Province) => p.isCapital);

  return (
    <div className="w-full h-full bg-gray-900 overflow-hidden">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full object-contain"
      >
        <rect width={width} height={height} fill="#1a202c" />

        {/* Draw borders between provinces of DIFFERENT nations */}
        {borders.map(border => {
            // This part needs the full province data to check nation Ids
            // A simplified border is drawn for now. A future improvement would be to pass
            // the full province objects to the border generation.
            const pathData = "M" + border.path.map(p => `${p.x} ${p.y}`).join(" L ");
            return (
              <path
                key={border.id}
                d={pathData}
                fill="none"
                stroke="#111827" // Darker borders
                strokeWidth="1.5"
              />
            );
        })}
        
        {/* Draw Provinces */}
        {provinces.map(province => {
          const fillColor = nationColorMap.get(province.nationId) || '#333';
          const points = province.polygon.map(p => `${p.x},${p.y}`).join(' ');

          return (
            <polygon
              key={province.id}
              points={points}
              fill={fillColor}
              stroke="#111827"
              strokeWidth="0.5"
              className="transition-all duration-300 group-hover:stroke-teal-300"
            />
          );
        })}

        {/* Draw Nation Labels on Capitals */}
        {capitals.map(capital => {
          const nation = nations.find(n => n.id === capital.nationId);
          if (!nation) return null;

          const polygonForLabel = capital.polygon.map(p => [p.x, p.y]);
          const labelPosArr = polylabel([polygonForLabel], 1.0);
          const labelPos = { x: labelPosArr[0], y: labelPosArr[1] };
          
          const dynamicFontSize = Math.max(10, Math.min(28, Math.sqrt(capital.area) / 3));

          return (
            <g key={`capital-group-${capital.id}`}>
              {/* Capital City Indicator (Star) */}
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dy="-0.6em" // Adjusted vertical position
                fill="#FFD700" // Gold color for the star
                fontSize={dynamicFontSize * 1.2} // Reduced size
                className="pointer-events-none"
                style={{ textShadow: '0 0 3px black, 0 0 5px black' }}
              >
                ★
              </text>

              {/* Nation Name */}
              <text
                key={`label-${capital.id}`}
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dy=".3em"
                fill="#FFFFFF"
                fontSize={dynamicFontSize}
                fontWeight="bold"
                paintOrder="stroke"
                stroke="#000000"
                strokeWidth="3px"
                strokeLinecap="butt"
                strokeLinejoin="miter"
                className="pointer-events-none"
              >
                {nation.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default MapDisplay; 