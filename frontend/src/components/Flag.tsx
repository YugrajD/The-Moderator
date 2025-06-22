import React from 'react';
import seedrandom from 'seedrandom';

interface FlagProps {
  nationId: number;
  width?: number;
  height?: number;
}

const Flag: React.FC<FlagProps> = ({ nationId, width = 80, height = 50 }) => {
  // Seed the random number generator to make flag generation deterministic
  const rng = seedrandom(nationId.toString());

  // --- Generate Flag Design ---

  // 1. Colors
  const colors = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#800000', '#9A6324', '#000075'];
  const primaryColor = colors[Math.floor(rng() * colors.length)];
  let secondaryColor = colors[Math.floor(rng() * colors.length)];
  while (primaryColor === secondaryColor) {
    secondaryColor = colors[Math.floor(rng() * colors.length)];
  }

  // 2. Layout
  const layoutType = Math.floor(rng() * 3); // 0: Bicolor, 1: Tricolor, 2: Central Symbol

  const renderBicolor = () => (
    <>
      <rect width={width / 2} height={height} fill={primaryColor} />
      <rect x={width / 2} width={width / 2} height={height} fill={secondaryColor} />
    </>
  );

  const renderTricolor = () => (
    <>
      <rect width={width / 3} height={height} fill={primaryColor} />
      <rect x={width / 3} width={width / 3} height={height} fill={secondaryColor} />
      <rect x={(width / 3) * 2} width={width / 3} height={height} fill={colors[Math.floor(rng() * colors.length)]} />
    </>
  );

  const renderCentralSymbol = () => {
    const symbols = ['★', '●', '✚', '◆'];
    const symbol = symbols[Math.floor(rng() * symbols.length)];
    const symbolSize = Math.min(width, height) * 0.5;
    return (
      <>
        <rect width={width} height={height} fill={primaryColor} />
        <text
          x={width / 2}
          y={height / 2}
          textAnchor="middle"
          dy=".35em"
          fill={secondaryColor}
          fontSize={symbolSize}
          style={{ textShadow: '0 0 2px black' }}
        >
          {symbol}
        </text>
      </>
    );
  };
  
  let flagLayout;
  switch (layoutType) {
    case 0: flagLayout = renderBicolor(); break;
    case 1: flagLayout = renderTricolor(); break;
    default: flagLayout = renderCentralSymbol(); break;
  }
  
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="rounded-md shadow-md">
      {flagLayout}
    </svg>
  );
};

export default Flag; 