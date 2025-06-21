// Map Generator Module
// This adapts the Fantasy Map Generator code for our microservice

const seedrandom = require('seedrandom');
const { Delaunay } = require('d3-delaunay');

class MapGenerator {
  constructor() {
    this.maps = new Map(); // Store generated maps
  }

  // Generate a new world map
  async generateWorld(options = {}) {
    const {
      width = 1000,
      height = 600,
      regions = 8,
      seed = Math.random().toString(36).substring(7)
    } = options;

    // Set up the random seed
    this.setSeed(seed);

    // Generate basic map structure
    const mapData = {
      id: this.generateId(),
      width,
      height,
      seed,
      regions: [],
      borders: [],
      metadata: {
        generatedAt: new Date().toISOString(),
        version: '1.0.0'
      }
    };

    // Generate regions using Voronoi tessellation
    const regionsData = this.generateRegions(width, height, regions);
    mapData.regions = regionsData;

    // Generate borders between regions - NO LONGER PASSING VORONOI
    mapData.borders = this.generateBorders(regionsData);

    // Store the map
    this.maps.set(mapData.id, mapData);

    return mapData;
  }

  // Generate regions using Voronoi tessellation
  generateRegions(width, height, count) {
    const regions = [];
    
    // Generate random center points for the regions
    const points = Array.from({ length: count }, () => [
      Math.random() * width,
      Math.random() * height
    ]);

    // Compute Voronoi diagram
    const delaunay = Delaunay.from(points);
    const voronoi = delaunay.voronoi([0, 0, width, height]);

    // Create regions from Voronoi cells
    for (let i = 0; i < count; i++) {
      const polygon = voronoi.cellPolygon(i);
      if (!polygon) continue; // Skip cells that can't be computed

      const centerPoint = { x: points[i][0], y: points[i][1] };
      
      // Calculate area of the polygon
      let area = 0;
      for (let j = 0, len = polygon.length; j < len; j++) {
          const p1 = polygon[j];
          const p2 = polygon[(j + 1) % len];
          area += p1[0] * p2[1] - p2[0] * p1[1];
      }
      area = Math.abs(area / 2);

      const region = {
        id: i + 1,
        name: this.generateRegionName(),
        center: centerPoint,
        polygon: polygon.map(p => ({ x: p[0], y: p[1] })),
        neighbors: [...voronoi.neighbors(i)].map(n => n + 1),
        area: area,
        population: Math.floor(area * (Math.random() * 50 + 10)),
        terrain: this.getRandomTerrain(),
        climate: this.getRandomClimate()
      };
      regions.push(region);
    }

    return regions;
  }

  // Generate borders between regions
  generateBorders(regions) {
    const borders = [];
    const processedBorders = new Set(); // To avoid duplicating work

    regions.forEach(region1 => {
      if (!region1.neighbors) return;

      region1.neighbors.forEach(neighborId => {
        const region2 = regions.find(r => r.id === neighborId);
        if (!region2) return;

        // Create a unique key for each border pair so we only draw it once
        const borderKey = region1.id < region2.id ? `${region1.id}-${region2.id}` : `${region2.id}-${region1.id}`;
        if (processedBorders.has(borderKey)) return;

        // Find the shared vertices between the two region polygons
        const sharedPoints = region1.polygon.filter(p1 =>
          region2.polygon.some(p2 => Math.abs(p2.x - p1.x) < 0.1 && Math.abs(p2.y - p1.y) < 0.1)
        );

        if (sharedPoints.length >= 2) {
          // The shared edge is defined by the first two common points
          const startPoint = sharedPoints[0];
          const endPoint = sharedPoints[1];
          const path = this.generateWavyBorder(startPoint, endPoint);

          borders.push({
            id: borderKey,
            region1: region1.id,
            region2: region2.id,
            path: path
          });
          processedBorders.add(borderKey);
        }
      });
    });
    return borders;
  }

  generateWavyBorder(start, end, segments = 10, noise = 0.2) {
    const path = [start];
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    
    for (let i = 1; i < segments; i++) {
        const t = i / segments;
        const noiseFactor = (Math.random() - 0.5) * length * noise;
        
        // Point along the straight line
        const pointOnLine = {
            x: start.x + t * dx,
            y: start.y + t * dy
        };
        
        // Add perpendicular noise
        const noisyPoint = {
            x: pointOnLine.x - dy / length * noiseFactor,
            y: pointOnLine.y + dx / length * noiseFactor
        };
        
        path.push(noisyPoint);
    }
    
    path.push(end);
    return path;
  }

  // Generate a region name
  generateRegionName() {
    const prefixes = ['North', 'South', 'East', 'West', 'Central', 'Upper', 'Lower', 'New', 'Old'];
    const suffixes = ['land', 'ia', 'stan', 'burg', 'shire', 'vale', 'moor', 'dale', 'wood'];
    
    const prefix = prefixes[Math.floor(Math.random() * prefixes.length)];
    const suffix = suffixes[Math.floor(Math.random() * suffixes.length)];
    
    return `${prefix}${suffix}`;
  }

  // Get random terrain type
  getRandomTerrain() {
    const terrains = ['plains', 'mountains', 'forest', 'desert', 'swamp', 'hills', 'coastal', 'tundra'];
    return terrains[Math.floor(Math.random() * terrains.length)];
  }

  // Get random climate
  getRandomClimate() {
    const climates = ['temperate', 'tropical', 'arctic', 'desert', 'mediterranean', 'continental'];
    return climates[Math.floor(Math.random() * climates.length)];
  }

  // Get random border type
  getRandomBorderType() {
    const types = ['natural', 'river', 'mountain', 'artificial', 'disputed'];
    return types[Math.floor(Math.random() * types.length)];
  }

  // Calculate distance between two points
  calculateDistance(point1, point2) {
    const dx = point1.x - point2.x;
    const dy = point1.y - point2.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // Set random seed
  setSeed(seed) {
    // Use the seedrandom library to seed the Math.random() function
    seedrandom(seed, { global: true });
  }

  // Generate unique ID
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Get a stored map
  getMap(mapId) {
    return this.maps.get(mapId);
  }

  // List all stored maps
  listMaps() {
    return Array.from(this.maps.keys());
  }
}

module.exports = new MapGenerator(); 