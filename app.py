from flask import Flask, request, jsonify, render_template_string
import geopandas as gpd
from shapely.geometry import Point
import folium
from geopy.geocoders import Nominatim
import os
import json

app = Flask(__name__)

# Global variable to store loaded data
metro_data = None

# States where we don't lend
EXCLUDED_STATES = {
    'HI', 'AK', 'FL', 'NY', 'NJ', 'ND', 'SD',
    'Hawaii', 'Alaska', 'Florida', 'New York', 'New Jersey', 'North Dakota', 'South Dakota'
}

def get_state_from_coords(lat, lon):
    """Get state from coordinates - use metro name to infer state"""
    # Quick method: check if coordinates fall within any metro area
    # and extract state from metro name (they all include state abbreviations)
    try:
        if metro_data is None:
            return None
            
        point = gpd.GeoSeries([Point(lon, lat)], crs='EPSG:4326')
        point_proj = point.to_crs('EPSG:3857')
        
        # Check if point is inside any metro
        for idx, row in metro_data.iterrows():
            if row.geometry.contains(point_proj.iloc[0]):
                # Extract state from metro name (e.g., "Miami, FL" -> "FL")
                metro_name = row['NAME']
                # State abbreviations are usually after comma or hyphen
                parts = metro_name.replace('-', ',').split(',')
                for part in parts:
                    part = part.strip()
                    # Check if it's a state abbreviation (2 letters) or full name
                    if len(part) == 2 and part.isupper():
                        return part
                    # Check against full state names
                    for state in EXCLUDED_STATES:
                        if state in part:
                            return state
                break
    except Exception as e:
        print(f"State lookup error: {e}")
    return None

def is_excluded_state(state):
    """Check if state is in excluded list"""
    if not state:
        return False
    return state in EXCLUDED_STATES or state.upper() in EXCLUDED_STATES

def ensure_metro_data_loaded():
    """Lazy load metro data if not already loaded"""
    global metro_data
    if metro_data is None:
        load_metro_data()

def load_metro_data():
    """Load Census MSA boundaries on startup"""
    global metro_data
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    shapefile_path = os.path.join(base_dir, 'data', 'tl_2023_us_cbsa.shp')
    target_metros_path = os.path.join(base_dir, 'target_metros.txt')
    
    if os.path.exists(shapefile_path):
        print("Loading Census MSA data...")
        all_metro_data = gpd.read_file(shapefile_path)
        
        # Load target metro names
        target_names = set()
        if os.path.exists(target_metros_path):
            with open(target_metros_path, 'r') as f:
                for line in f:
                    name = line.strip()
                    if name and name not in ['Other', 'Rural']:
                        target_names.add(name)
            print(f"Loaded {len(target_names)} target metro areas from list")
        
        # Filter to only include target metros
        # Match by checking if the Census NAME contains key parts of our target names
        if target_names:
            # Create a simplified matching - extract city/main area names
            def matches_target(census_name):
                census_name_clean = census_name.lower()
                for target in target_names:
                    # Extract the main part before comma
                    target_main = target.split(',')[0].lower().strip()
                    # Remove MSA suffix
                    target_main = target_main.replace(' msa', '').strip()
                    if target_main in census_name_clean:
                        return True
                return False
            
            metro_data = all_metro_data[all_metro_data['NAME'].apply(matches_target)].copy()
            print(f"Filtered to {len(metro_data)} metropolitan areas matching your list")
        else:
            metro_data = all_metro_data
            print(f"No filter applied - using all {len(metro_data)} metropolitan areas")
        
        # Convert to appropriate CRS for distance calculations (meters)
        metro_data = metro_data.to_crs('EPSG:3857')
    else:
        print(f"Warning: Shapefile not found at {shapefile_path}")

@app.route('/')
def home():
    """Redirect to map view"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Metro Proximity API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .link { display: block; margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; text-decoration: none; color: #0066cc; }
            .link:hover { background: #e5e5e5; }
        </style>
    </head>
    <body>
        <h1>Metro Proximity API</h1>
        <p>Status: ✓ Running</p>
        <p>Metros loaded: ''' + str(len(metro_data) if metro_data is not None else 0) + '''</p>
        
        <a href="/map" class="link">
            <strong>📍 Interactive Map View</strong><br>
            <small>Visualize metro areas and search addresses</small>
        </a>
        
        <a href="/check-proximity?lat=40.7128&lon=-74.0060" class="link">
            <strong>🔌 API Endpoint</strong><br>
            <small>JSON API for programmatic access</small>
        </a>
    </body>
    </html>
    '''

@app.route('/metros.geojson')
def metros_geojson():
    """Return metro centers as points for lightweight loading"""
    ensure_metro_data_loaded()
    if metro_data is None:
        return jsonify({"error": "Metro data not loaded"}), 500
    
    # Convert to WGS84 and get centroids as simple list
    metro_display = metro_data.to_crs('EPSG:4326')
    features = []
    for idx, row in metro_display.iterrows():
        centroid = row.geometry.centroid
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [centroid.x, centroid.y]
            },
            "properties": {
                "name": row['NAME']
            }
        })
    
    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

@app.route('/map')
def map_view():
    """Interactive map visualization"""
    # Don't pre-load metros - let JavaScript load them asynchronously
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4, tiles='OpenStreetMap')
    
    # Add search functionality
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Metro Coverage Map</title>
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
            #map { width: 100%; height: 100vh; }
            .search-box {
                position: absolute;
                top: 10px;
                left: 50px;
                z-index: 1000;
                background: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }
            .search-box input {
                width: 300px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 14px;
            }
            .search-box button {
                padding: 10px 20px;
                background: #0066cc;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 14px;
            }
            .search-box button:hover { background: #0052a3; }
            #result {
                margin-top: 10px;
                padding: 10px;
                background: #f0f8ff;
                border-radius: 3px;
                display: none;
            }
            .info-box {
                position: absolute;
                bottom: 20px;
                left: 50px;
                z-index: 1000;
                background: white;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                max-width: 300px;
            }
        </style>
    </head>
    <body>
        <div class="search-box">
            <h3 style="margin-top:0">Search Address</h3>
            <input type="text" id="addressInput" placeholder="Enter address..." onkeypress="if(event.key===\'Enter\')searchAddress()">
            <button onclick="searchAddress()">Search</button>
            <div style="margin-top: 10px; font-size: 12px;">
                <label><input type="checkbox" id="useGoogle"> Use Google Maps (more accurate)</label>
                <input type="text" id="googleApiKey" placeholder="Google API Key" style="width: 200px; margin-left: 5px; font-size: 11px;" title="Optional: Paste your Google Maps API key for better address lookup">
            </div>
            <div id="result"></div>
        </div>
        
        <div class="info-box">
            <strong>Metro Coverage Map</strong><br>
            <small>Blue circles = 50-mile radius from metro centers<br>
            <strong>Search tips:</strong><br>
            • City, State: "Phoenix, AZ"<br>
            • Zip code: "85718"<br>
            • Full addresses may not always work</small>
        </div>
        
        ''' + m.get_root().render() + '''
        
        <script>
            let marker = null;
            let circle = null;
            let line = null;
            let metroLayer = null;
            
            // Load metros from GeoJSON endpoint after map loads
            window.addEventListener('DOMContentLoaded', async () => {
                const theMap = getMap();
                if (theMap) {
                    try {
                        const response = await fetch('/metros.geojson');
                        const geojsonData = await response.json();
                        
                        metroLayer = L.geoJSON(geojsonData, {
                            pointToLayer: (feature, latlng) => {
                                return L.circle(latlng, {
                                    radius: 50 * 1609.34, // 50 miles in meters
                                    fillColor: '#3388ff',
                                    color: '#0066cc',
                                    weight: 2,
                                    fillOpacity: 0.15,
                                    opacity: 0.5
                                });
                            },
                            onEachFeature: (feature, layer) => {
                                if (feature.properties && feature.properties.name) {
                                    layer.bindTooltip(feature.properties.name);
                                }
                            }
                        }).addTo(theMap);
                    } catch (error) {
                        console.error('Failed to load metro boundaries:', error);
                    }
                }
                
                // Load saved Google API key from localStorage
                const savedKey = localStorage.getItem('googleMapsApiKey');
                if (savedKey) {
                    document.getElementById('googleApiKey').value = savedKey;
                    document.getElementById('useGoogle').checked = true;
                }
            });
            
            // Save API key when changed
            document.addEventListener('DOMContentLoaded', () => {
                document.getElementById('googleApiKey').addEventListener('change', (e) => {
                    if (e.target.value) {
                        localStorage.setItem('googleMapsApiKey', e.target.value);
                    }
                });
            });
            
            // Get the map object - Folium creates it in the global scope
            function getMap() {
                // Find the map object in the global scope
                for (let key in window) {
                    if (window[key] && typeof window[key] === 'object' && window[key]._container) {
                        return window[key];
                    }
                }
                return null;
            }
            
            async function searchAddress() {
                const address = document.getElementById('addressInput').value;
                const resultDiv = document.getElementById('result');
                
                if (!address) {
                    alert('Please enter an address');
                    return;
                }
                
                const theMap = getMap();
                if (!theMap) {
                    alert('Map not ready yet, please wait a moment and try again');
                    return;
                }
                
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = 'Searching...';
                
                try {
                    let lat, lon, displayName;
                    const useGoogle = document.getElementById('useGoogle').checked;
                    const googleApiKey = document.getElementById('googleApiKey').value;
                    
                    if (useGoogle && googleApiKey) {
                        // Use Google Maps Geocoding
                        const googleUrl = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${googleApiKey}`;
                        const googleResponse = await fetch(googleUrl);
                        const googleData = await googleResponse.json();
                        
                        if (googleData.status === 'OK' && googleData.results.length > 0) {
                            const location = googleData.results[0].geometry.location;
                            lat = location.lat;
                            lon = location.lng;
                            displayName = googleData.results[0].formatted_address;
                        } else {
                            resultDiv.innerHTML = `<span style="color: red;">Google Maps error: ${googleData.status}</span>`;
                            return;
                        }
                    } else {
                        // Use Nominatim (free)
                        const geoResponse = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1&addressdetails=1`);
                        const geoData = await geoResponse.json();
                        
                        if (geoData.length > 0) {
                            lat = parseFloat(geoData[0].lat);
                            lon = parseFloat(geoData[0].lon);
                            displayName = geoData[0].display_name;
                        } else {
                            resultDiv.innerHTML = 'Address not found. Try:<br>• City name ("Scottsdale, AZ")<br>• Zip code ("85718")<br>• Or enable Google Maps above';
                            return;
                        }
                    }
                    
                    // Check proximity via API
                    const apiResponse = await fetch(`/check-proximity?lat=${lat}&lon=${lon}&max_distance=50`);
                    const apiData = await apiResponse.json();
                    
                    // Remove old marker, circle, and line if they exist
                    if (marker) {
                        theMap.removeLayer(marker);
                    }
                    if (circle) {
                        theMap.removeLayer(circle);
                    }
                    if (line) {
                        theMap.removeLayer(line);
                    }
                    
                    // Add marker to map
                    marker = L.marker([lat, lon]).addTo(theMap);
                    marker.bindPopup(`<b>${displayName}</b><br>${apiData.within_range ? '✓ Within range' : '✗ Outside range'}`).openPopup();
                    
                    // Add 50-mile radius circle
                    circle = L.circle([lat, lon], {
                        radius: 50 * 1609.34, // 50 miles in meters
                        color: apiData.within_range ? 'green' : 'red',
                        fillColor: apiData.within_range ? '#90EE90' : '#FFB6C1',
                        fillOpacity: 0.2,
                        weight: 2
                    }).addTo(theMap);
                    
                    // Draw line to nearest metro edge if not inside
                    if (!apiData.excluded && !apiData.is_inside_metro && apiData.nearest_metro.edge_coords) {
                        const edgeCoords = apiData.nearest_metro.edge_coords;
                        line = L.polyline(
                            [[lat, lon], edgeCoords],
                            {
                                color: apiData.within_range ? 'blue' : 'red',
                                weight: 3,
                                opacity: 0.7,
                                dashArray: '10, 10'
                            }
                        ).addTo(theMap);
                        
                        // Add a small marker at the metro edge
                        L.circleMarker(edgeCoords, {
                            radius: 6,
                            fillColor: apiData.within_range ? 'blue' : 'red',
                            color: '#fff',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.8
                        }).addTo(theMap).bindPopup(`Nearest point on ${apiData.nearest_metro.name} boundary`);
                    }
                    
                    // Zoom to location
                    theMap.setView([lat, lon], 8);
                    
                    // Display result
                    if (apiData.excluded) {
                        resultDiv.innerHTML = `
                            <strong style="color: #ff6600;">⛔ Excluded State</strong><br>
                            ${apiData.message}<br>
                            <small>We do not lend in: HI, AK, FL, NY, NJ, ND, SD</small>
                        `;
                        // Update marker color to orange
                        marker.remove();
                        marker = L.marker([lat, lon], {
                            icon: L.icon({
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
                                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                iconSize: [25, 41],
                                iconAnchor: [12, 41],
                                popupAnchor: [1, -34],
                                shadowSize: [41, 41]
                            })
                        }).addTo(theMap);
                        marker.bindPopup(`<b>${displayName}</b><br>⛔ Excluded State: ${apiData.excluded_state}`).openPopup();
                        // Make circle orange
                        circle.setStyle({color: 'orange', fillColor: '#FFA500'});
                    } else if (apiData.within_range) {
                        resultDiv.innerHTML = `
                            <strong style="color: green;">✓ Within Range</strong><br>
                            ${apiData.is_inside_metro ? 'Inside' : 'Near'}: ${apiData.nearest_metro.name}<br>
                            Distance: ${apiData.nearest_metro.distance_to_edge_miles} miles to edge
                        `;
                    } else {
                        resultDiv.innerHTML = `
                            <strong style="color: red;">✗ Outside Range</strong><br>
                            Nearest: ${apiData.nearest_metro.name}<br>
                            Distance: ${apiData.nearest_metro.distance_to_edge_miles} miles away
                        `;
                    }
                } catch (error) {
                    resultDiv.innerHTML = `<span style="color: red;">Error: ${error.message}</span>`;
                }
            }
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(html_template)

@app.route('/check-proximity', methods=['GET'])
def check_proximity():
    """
    Check if a location is within specified distance of any metro area
    
    Query params:
    - lat: latitude
    - lon: longitude
    - max_distance: maximum distance in miles (default: 50)
    """
    try:
        # Get parameters
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        max_distance_miles = float(request.args.get('max_distance', 50))
        
        # Convert miles to meters (1 mile = 1609.34 meters)
        max_distance_meters = max_distance_miles * 1609.34
        
        if metro_data is None:
            return jsonify({
                "error": "Metro data not loaded"
            }), 500
        
        # Check if location is in excluded state
        try:
            state = get_state_from_coords(lat, lon)
            print(f"State check for ({lat}, {lon}): {state}")
            if state and is_excluded_state(state):
                print(f"Location is in excluded state: {state}")
                return jsonify({
                    "excluded": True,
                    "excluded_state": state,
                    "within_range": False,
                    "message": f"We do not lend in {state}"
                })
        except Exception as e:
            print(f"Error checking state: {e}")
            # Continue with metro check even if state check fails
        
        # Create point from coordinates (WGS84)
        point = gpd.GeoSeries([Point(lon, lat)], crs='EPSG:4326')
        # Convert to same CRS as metro data
        point = point.to_crs('EPSG:3857')
        
        # Make a copy to avoid modifying global data
        metro_working = metro_data.copy()
        
        # Calculate distance to each metro area boundary
        metro_working['distance'] = metro_working.geometry.distance(point.iloc[0])
        
        # Get the absolute nearest metro (regardless of distance)
        nearest_overall = metro_working.loc[metro_working['distance'].idxmin()]
        nearest_distance_miles = nearest_overall['distance'] / 1609.34
        is_inside_nearest = nearest_overall.geometry.contains(point.iloc[0])
        
        # Get closest point on metro boundary for line drawing
        nearest_geom_wgs84 = metro_data.to_crs('EPSG:4326').loc[nearest_overall.name].geometry
        from shapely.ops import nearest_points
        point_wgs84 = Point(lon, lat)
        _, closest_point = nearest_points(point_wgs84, nearest_geom_wgs84)
        nearest_edge_coords = [closest_point.y, closest_point.x]  # [lat, lon]
        
        # Find metros within max distance
        nearby_metros = metro_working[metro_working['distance'] <= max_distance_meters].copy()
        
        if len(nearby_metros) == 0:
            # Still return nearest metro info, but indicate it's outside range
            return jsonify({
                "within_range": False,
                "is_inside_metro": False,
                "nearest_metro": {
                    "name": nearest_overall['NAME'],
                    "cbsa_code": nearest_overall['CBSAFP'],
                    "distance_to_edge_miles": round(nearest_distance_miles, 2),
                    "edge_coords": nearest_edge_coords
                },
                "message": f"Nearest metro is {round(nearest_distance_miles, 2)} miles away (outside {max_distance_miles} mile range)"
            })
        
        # Get the nearest metro
        nearest = nearby_metros.loc[nearby_metros['distance'].idxmin()]
        distance_miles = nearest['distance'] / 1609.34
        
        # Check if point is inside the metro area
        is_inside = nearest.geometry.contains(point.iloc[0])
        
        result = {
            "within_range": True,
            "is_inside_metro": is_inside,
            "nearest_metro": {
                "name": nearest['NAME'],
                "cbsa_code": nearest['CBSAFP'],
                "distance_to_edge_miles": 0 if is_inside else round(distance_miles, 2),
                "edge_coords": nearest_edge_coords
            },
            "all_nearby_metros": []
        }
        
        # Add all nearby metros
        for idx, row in nearby_metros.iterrows():
            metro_info = {
                "name": row['NAME'],
                "distance_miles": round(row['distance'] / 1609.34, 2),
                "cbsa_code": row['CBSAFP']
            }
            result["all_nearby_metros"].append(metro_info)
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid parameters. Provide lat, lon as numbers."
        }), 400
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# Load metro data when module is imported (for Gunicorn)
load_metro_data()

if __name__ == '__main__':
    # This runs only when running directly with python (not with Gunicorn)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
