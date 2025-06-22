import React from 'react';

interface LeaderPortraitProps {
  leaderName: string;
}

const LeaderPortrait: React.FC<LeaderPortraitProps> = ({ leaderName }) => {
  // Pollinations.ai generates an image from a URL-encoded prompt.
  const prompt = `A photorealistic portrait of a modern world leader named ${leaderName}. The portrait should have a professional and serious expression, with the leader wearing a contemporary suit, set against a simple, neutral background.`;
  const imageUrl = `https://pollinations.ai/p/${encodeURIComponent(prompt)}`;

  return (
    <img
      src={imageUrl}
      alt={`Portrait of ${leaderName}`}
      className="w-16 h-16 rounded-full bg-gray-700 border-2 border-gray-600 object-cover"
    />
  );
};

export default LeaderPortrait; 