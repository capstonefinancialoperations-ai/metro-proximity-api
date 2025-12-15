# Metro Proximity API

A Flask API that checks if an address is within a specified distance of US metropolitan areas using Census Bureau data.

## Features
- Uses official Census Bureau CBSA (Core Based Statistical Area) boundaries
- Calculates accurate distance to metro area edges
- Returns all nearby metro areas within range
- Cloud-hosted on Render (no computer needed to run)

## API Endpoints

### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "message": "Metro Proximity API",
  "metros_loaded": 945
}
```

### `GET /check-proximity`
Check if coordinates are within distance of metro areas

**Query Parameters:**
- `lat` (required): Latitude
- `lon` (required): Longitude  
- `max_distance` (optional): Maximum distance in miles (default: 50)

**Example Request:**
```
https://your-app.onrender.com/check-proximity?lat=40.7128&lon=-74.0060&max_distance=50
```

**Response (inside metro):**
```json
{
  "within_range": true,
  "is_inside_metro": true,
  "nearest_metro": {
    "name": "New York-Newark-Jersey City, NY-NJ-PA",
    "cbsa_code": "35620",
    "distance_to_edge_miles": 0
  },
  "all_nearby_metros": [...]
}
```

**Response (outside metro, within range):**
```json
{
  "within_range": true,
  "is_inside_metro": false,
  "nearest_metro": {
    "name": "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD",
    "cbsa_code": "37980",
    "distance_to_edge_miles": 35.2
  },
  "all_nearby_metros": [...]
}
```

**Response (out of range):**
```json
{
  "within_range": false,
  "nearest_metro": null,
  "distance_miles": null,
  "message": "No metro areas within 50 miles"
}
```

## Setup Instructions

### 1. Download Census Data
Download the Census CBSA shapefile from:
https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html

1. Select year: 2023
2. Select layer type: "Core Based Statistical Areas (CBSAs)"
3. Download and extract to `data/` folder

### 2. Local Testing
```bash
pip install -r requirements.txt
python app.py
```

Test locally:
```bash
curl "http://localhost:5000/check-proximity?lat=40.7128&lon=-74.0060"
```

### 3. Deploy to Render
See deployment instructions in main documentation.

## Integration with Make/Monday.com

Use the `/check-proximity` endpoint in Make:
1. Geocode address to get lat/lon
2. Call this API with coordinates
3. Update Monday board based on `within_range` result
