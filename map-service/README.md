# Map Generation Microservice

A Node.js microservice for generating fantasy world maps using procedural generation algorithms.

## Features

- Generate random world maps with configurable regions
- Extract region data (names, borders, terrain, climate)
- RESTful API for map generation
- Seed-based generation for reproducible results

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the service:
   ```bash
   npm start
   ```

   Or use the startup script:
   ```bash
   ./start.sh
   ```

The service will run on `http://localhost:3001`

## API Endpoints

### Health Check
```
GET /health
```
Returns service health status.

### Generate World
```
POST /generate-world
```

**Request Body:**
```json
{
  "width": 1000,
  "height": 600,
  "regions": 8,
  "seed": "optional-seed-string"
}
```

**Response:**
```json
{
  "success": true,
  "map": {
    "id": "map-id",
    "width": 1000,
    "height": 600,
    "seed": "seed-string",
    "regions": [
      {
        "id": 1,
        "name": "Northland",
        "center": {"x": 100, "y": 200},
        "neighbors": [2, 3],
        "area": 750,
        "population": 500000,
        "terrain": "plains",
        "climate": "temperate"
      }
    ],
    "borders": [
      {
        "id": "1-2",
        "region1": 1,
        "region2": 2,
        "length": 75,
        "type": "natural"
      }
    ]
  },
  "metadata": {
    "width": 1000,
    "height": 600,
    "regions": 8,
    "seed": "seed-string"
  }
}
```

## Integration with FastAPI Backend

The FastAPI backend communicates with this service via HTTP requests:

- **Health Check**: `GET http://localhost:3001/health`
- **Generate World**: `POST http://localhost:3001/generate-world`

## Development

For development with auto-restart:
```bash
npm run dev
```

## Architecture

This service provides a simplified version of map generation for the diplomatic simulation game. It generates:

- **Regions**: Geographic areas with unique names, terrain, and climate
- **Borders**: Connections between neighboring regions
- **Metadata**: Map dimensions, seed, and generation info

The generated data is used by the main game to create nations and their relationships. 