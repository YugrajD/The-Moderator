import React, { useState } from 'react';
import polylabel from 'polylabel';

// --- Shared Interfaces ---
interface Point { x: number; y: number; }

export interface Province {
  id: number;
  nationId: number;
  isCapital?: boolean;
  cityType?: 'capital' | 'major';
  name: string;
  center: Point;
  polygon: Point[];
  terrain: string;
  area: number;
  population: number;
  marker?: string;
}

export interface LeaderProfile {
  name: string;
  personality: string;
  ambition: string;
  age: number;
}

export interface Nation {
  id: number;
  name: string;
  government_type: string;
  leader: LeaderProfile;
  capital_province_name: string;
  provinces: Province[];
  military_strength: number;
  population: number;
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
  const [selectedProvince, setSelectedProvince] = useState<Province | null>(null);

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

  const handleProvinceClick = (e: React.MouseEvent, province: Province) => {
    e.stopPropagation(); // Prevent the background click from firing
    setSelectedProvince(province);
  };

  const handleBackgroundClick = () => {
    setSelectedProvince(null);
  };

  return (
    <div className="w-full h-full bg-gray-900 overflow-hidden" onClick={handleBackgroundClick}>
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
            const pathData = "M" + border.path.map((p: { x: number; y: number }) => `${p.x} ${p.y}`).join(" L ");
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
              onClick={(e) => handleProvinceClick(e, province)}
            />
          );
        })}

        {/* Draw Nation & City Labels */}
        {provinces.map(province => {
          if (!province.cityType) return null;

          const nation = nations.find(n => n.id === province.nationId);
          if (!nation) return null;

          const polygonForLabel = province.polygon.map(p => [p.x, p.y]);
          const labelPosArr = polylabel([polygonForLabel], 1.0);
          const labelPos = { x: labelPosArr[0], y: labelPosArr[1] };
          
          let cityName = '';
          let symbol = '';
          let fontSize = 0;
          let symbolDy = '0em';
          let nameDy = '0em';

          if (province.cityType === 'capital') {
            cityName = nation.name;
            symbol = '★';
            fontSize = Math.max(10, Math.min(28, Math.sqrt(province.area) / 3));
            symbolDy = "-0.1em";
            nameDy = "0.9em";
          } else if (province.cityType === 'major') {
            cityName = province.name;
            symbol = '●';
            fontSize = Math.max(8, Math.min(20, Math.sqrt(province.area) / 4.5));
            symbolDy = '0.35em';
            nameDy = '1.4em';
          } else {
            return null;
          }

          return (
            <g key={`city-label-${province.id}`} className="pointer-events-none">
              {/* City Symbol */}
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dy={symbolDy}
                fill={province.cityType === 'capital' ? '#FFD700' : '#FFFFFF'}
                fontSize={fontSize * 1.1}
                style={{ textShadow: '0 0 3px black, 0 0 5px black' }}
              >
                {symbol}
              </text>

              {/* City/Nation Name */}
              <text
                x={labelPos.x}
                y={labelPos.y}
                textAnchor="middle"
                dy={nameDy}
                fill="#FFFFFF"
                fontSize={fontSize}
                fontWeight="bold"
                paintOrder="stroke"
                stroke="#000000"
                strokeWidth="3px"
                strokeLinecap="butt"
                strokeLinejoin="miter"
              >
                {cityName}
              </text>
            </g>
          );
        })}

        {/* Draw Event Markers */}
        {provinces.map(province => {
          if (!province.marker) return null;

          let symbol = '';
          let color = '#FFFFFF';
          switch (province.marker) {
            case 'conquered':
              symbol = '⚔️'; // Crossed swords
              color = '#FF4136'; // Red
              break;
            case 'defended':
              symbol = '🛡️'; // Shield
              color = '#0074D9'; // Blue
              break;
            case 'disaster':
              symbol = '➕'; // Medical Cross
              color = '#FFDC00'; // Yellow
              break;
            default:
              return null;
          }

          return (
            <text
              key={`marker-${province.id}`}
              x={province.center.x}
              y={province.center.y}
              textAnchor="middle"
              dy=".35em"
              fill={color}
              fontSize="24"
              className="pointer-events-none"
              style={{ textShadow: '0 0 4px black, 0 0 6px black' }}
            >
              {symbol}
            </text>
          );
        })}

        {/* Draw Selected Province Tooltip */}
        {selectedProvince && (() => {
          const tooltipWidth = 120;
          const tooltipHeight = 40;
          const offset = 15; // How far from the center point

          // Default position is above the center point
          let tooltipX = selectedProvince.center.x - tooltipWidth / 2;
          let tooltipY = selectedProvince.center.y - tooltipHeight - offset;

          // Flip to appear below if it would go off the top of the map
          if (tooltipY < 0) {
            tooltipY = selectedProvince.center.y + offset;
          }

          // Adjust horizontally to stay within the map bounds
          if (tooltipX < 0) {
            tooltipX = 5; // Small margin from the edge
          }
          if (tooltipX + tooltipWidth > width) {
            tooltipX = width - tooltipWidth - 5; // Small margin from the edge
          }
          
          // Adjust vertically to stay within the map bounds
          if (tooltipY + tooltipHeight > height) {
            tooltipY = height - tooltipHeight - 5; // Small margin from the edge
          }

          const textX = tooltipX + tooltipWidth / 2;

          return (
            <g className="pointer-events-none">
              <rect
                x={tooltipX}
                y={tooltipY}
                width={tooltipWidth}
                height={tooltipHeight}
                fill="rgba(0,0,0,0.7)"
                rx="5"
              />
              <text
                x={textX}
                y={tooltipY + 17}
                textAnchor="middle"
                fill="white"
                fontSize="12"
                fontWeight="bold"
              >
                {selectedProvince.name}
              </text>
              <text
                x={textX}
                y={tooltipY + 32}
                textAnchor="middle"
                fill="white"
                fontSize="10"
              >
                Pop: {(selectedProvince.population ?? 0).toLocaleString()}
              </text>
            </g>
          );
        })()}
      </svg>
    </div>
  );
};

export default MapDisplay; 