const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Import map generation modules
// Note: We'll need to adapt the Fantasy Map Generator code to work as a module
const MapGenerator = require('./map-generator');

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'map-generation' });
});

// Generate a new world map
app.post('/generate-world', async (req, res) => {
  try {
    const { 
      width = 1000, 
      height = 600, 
      regions = 8,
      seed = Math.random().toString(36).substring(7)
    } = req.body;

    console.log(`Generating world map with ${regions} regions, seed: ${seed}`);

    // Generate the map
    const mapData = await MapGenerator.generateWorld({
      width,
      height,
      regions,
      seed
    });

    res.json({
      success: true,
      map: mapData,
      metadata: {
        width,
        height,
        regions: mapData.regions.length,
        seed
      }
    });

  } catch (error) {
    console.error('Error generating world:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get region information
app.get('/regions/:mapId', (req, res) => {
  try {
    const { mapId } = req.params;
    // This would retrieve a previously generated map
    // For now, we'll return a placeholder
    res.json({
      success: true,
      regions: []
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Map generation service running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Generate world: POST http://localhost:${PORT}/generate-world`);
}); 