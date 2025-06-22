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
  generateRegions(width, height, nationCount) {
    const allProvinces = [];
    const numProvinces = 120; // Generate a lot of small provinces

    const points = Array.from({ length: numProvinces }, () => [
      Math.random() * width,
      Math.random() * height
    ]);

    const delaunay = Delaunay.from(points);
    const voronoi = delaunay.voronoi([0, 0, width, height]);

    // 1. Create all the base provinces
    for (let i = 0; i < numProvinces; i++) {
      const polygon = voronoi.cellPolygon(i);
      if (!polygon) continue;

      const neighbors = [...voronoi.neighbors(i)];
      
      allProvinces.push({
        id: i, // Use index as ID for now
        nationId: null, // To be assigned
        name: this.generateRegionName(), // Add the missing name
        center: { x: points[i][0], y: points[i][1] },
        polygon: polygon.map(p => ({ x: p[0], y: p[1] })),
        neighbors: neighbors, // Store neighbor indices
        terrain: this.getRandomLandTerrain(), // No more water
        climate: this.getRandomClimate(),
        area: this.getPolygonArea(polygon)
      });
    }

    // 2. Grow nations from random capitals
    const unassignedProvinces = new Set(allProvinces.map(p => p.id));
    const nationCapitals = [];
    // Shuffle provinces to pick random capitals
    const shuffledProvinces = [...allProvinces].sort(() => 0.5 - Math.random());

    for (let i = 0; i < nationCount; i++) {
      const capital = shuffledProvinces[i];
      capital.nationId = i + 1;
      capital.isCapital = true;
      nationCapitals.push(capital);
      unassignedProvinces.delete(capital.id);
    }

    // Use a queue for each nation to expand outwards (BFS)
    const queues = nationCapitals.map(capital => [capital]);

    while (unassignedProvinces.size > 0) {
      for (let i = 0; i < queues.length; i++) {
        const nationId = i + 1;
        const queue = queues[i];
        if (queue.length === 0) continue;

        const currentProvince = queue.shift();
        
        for (const neighborId of currentProvince.neighbors) {
          if (unassignedProvinces.has(neighborId)) {
            const neighborProvince = allProvinces[neighborId];
            neighborProvince.nationId = nationId;
            unassignedProvinces.delete(neighborId);
            queue.push(neighborProvince);
          }
        }
      }
      // If all queues are empty but there are still unassigned provinces, break to avoid infinite loop
      if (queues.every(q => q.length === 0)) break;
    }

    return allProvinces;
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

  generateWavyBorder(start, end, roughness = 0.75, displacement = 0.45) {
    const subdivide = (p1, p2, disp) => {
      const dist = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
      
      // Base case: if the segment is too short, just return the end point.
      if (dist < 5) {
        return [p2];
      }
  
      // Calculate the midpoint.
      const midX = (p1.x + p2.x) / 2;
      const midY = (p1.y + p2.y) / 2;
  
      // Calculate the perpendicular vector.
      const normalX = -(p2.y - p1.y) / dist;
      const normalY = (p2.x - p1.x) / dist;
      
      // Displace the midpoint.
      const offset = (Math.random() - 0.5) * disp;
      const displacedMid = {
        x: midX + normalX * offset,
        y: midY + normalY * offset,
      };
  
      // Reduce displacement for the next level of recursion.
      const newDisp = disp * roughness;
      
      // Recurse on the two new segments and combine the results.
      const path1 = subdivide(p1, displacedMid, newDisp);
      const path2 = subdivide(displacedMid, p2, newDisp);
      
      return [...path1, ...path2];
    };

    // Calculate the initial displacement based on the total length.
    const initialDisplacement = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2)) * displacement;
    
    // Start the path with the start point, then add the subdivided points.
    return [start, ...subdivide(start, end, initialDisplacement)];
  }

  getPolygonArea(polygon) {
    let area = 0;
    for (let i = 0, len = polygon.length; i < len; i++) {
      const p1 = polygon[i];
      const p2 = polygon[(i + 1) % len];
      area += p1[0] * p2[1] - p2[0] * p1[1];
    }
    return Math.abs(area / 2);
  }

  // No more water terrain
  getRandomLandTerrain() {
    const terrains = ['plains', 'mountains', 'forest', 'desert', 'swamp', 'hills', 'coastal', 'tundra'];
    return terrains[Math.floor(Math.random() * terrains.length)];
  }

  // Generate a region name
  generateRegionName() {
    const starts = [
      "Val", "Sol", "Eld", "Mor", "Lun", "Ast", "Cor", "Pyr", "Aer", "Zeph", "Glorn", "Ith", "Rhun", "Sil",
      "Bel", "Kael", "Zan", "Drak", "Fael", "Gwyn", "Tyr", "Vor", "Xyl", "Cairn", "Dun", "Strath", "Glen", "Loch"
    ];
    const middles = [
      "en", "ar", "ia", "or", "an", "el", "in", "yr", "os", "um", "ak", "ir",
      "ana", "eth", "ion", "o", "u", "ae", "is", "ali"
    ];
    const ends = [
      "ia", "dor", "grad", "fall", "wind", "port", "gard", "th", "is", "a", "gard", "nar", "dale", "stead",
      "burg", "fel", "wood", "mire", "peak", "ford", "ham", "wick", "ton", "vale", "crest", "rock", "burn"
    ];
    
    const hasMiddle = Math.random() > 0.4;
    
    let name = starts[Math.floor(Math.random() * starts.length)];
    if (hasMiddle) {
      name += middles[Math.floor(Math.random() * middles.length)];
    }
    name += ends[Math.floor(Math.random() * ends.length)];
    
    return name;
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

  // Helper to calculate distance from map center
  distanceFromCenter(point, width, height) {
    const cx = width / 2;
    const cy = height / 2;
    return Math.sqrt(Math.pow(point.x - cx, 2) + Math.pow(point.y - cy, 2));
  }
}

module.exports = new MapGenerator(); 