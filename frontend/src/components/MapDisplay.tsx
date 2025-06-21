import React from 'react';

interface Point {
  x: number;
  y: number;
}

interface Region {
  id: number;
  name: string;
  center: Point;
  neighbors: number[];
  terrain: string;
  climate: string;
  area: number;
  polygon: Point[];
}

interface Border {
  id: string;
  region1: number;
  region2: number;
  path: Point[];
}

interface MapData {
  width: number;
  height: number;
  regions: Region[];
  borders: Border[];
}

interface MapDisplayProps {
  mapData: MapData | null;
  nations: any[] | null;
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
  default: '#CCCCCC'
};

const MapDisplay: React.FC<MapDisplayProps> = ({ mapData, nations }) => {
  if (!mapData) {
    return (
      <div className="flex items-center justify-center w-full h-full bg-gray-800 rounded-lg">
        <p className="text-gray-400">Generate a world to see the map.</p>
      </div>
    );
  }

  const { width, height, regions, borders } = mapData;

  const getRegionById = (id: number) => regions.find(r => r.id === id);

  return (
    <div className="w-full h-full bg-gray-900 p-4 rounded-lg shadow-inner overflow-hidden">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-full object-contain"
      >
        <rect width={width} height={height} fill="#1a202c" />

        {/* Draw borders */}
        {borders.map(border => {
          const pathData = "M" + border.path.map(p => `${p.x} ${p.y}`).join(" L ");
          return (
            <path
              key={border.id}
              d={pathData}
              fill="none"
              stroke="#4A5568"
              strokeWidth="2"
            />
          );
        })}

        {/* Draw regions */}
        {regions.map(region => {
          const nation = nations?.find(n => n.region_id === region.id);
          const terrainColor = TERRAIN_COLORS[region.terrain] || TERRAIN_COLORS.default;
          const points = region.polygon.map(p => `${p.x},${p.y}`).join(' ');

          return (
            <g key={region.id} className="cursor-pointer group">
              <polygon
                points={points}
                fill={terrainColor}
                stroke="#1a202c"
                strokeWidth="3"
                className="transition-all duration-300 group-hover:stroke-teal-300"
              />
              <text
                x={region.center.x}
                y={region.center.y}
                textAnchor="middle"
                dy=".3em"
                fill="#FFFFFF"
                fontSize="14"
                fontWeight="bold"
                paintOrder="stroke"
                stroke="#000000"
                strokeWidth="3px"
                strokeLinecap="butt"
                strokeLinejoin="miter"
                className="pointer-events-none transition-all duration-300 group-hover:text-lg"
              >
                {nation ? nation.name : region.name}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default MapDisplay; 