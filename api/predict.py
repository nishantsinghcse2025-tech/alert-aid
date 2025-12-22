"""
Alert Aid - Disaster Risk Prediction Endpoint
Calculates risk scores based on weather data
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import random
from datetime import datetime

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "1801423b3942e324ab80f5b47afe0859")

def calculate_risk(weather_data):
    """Simple rule-based risk calculation"""
    temp = weather_data.get("main", {}).get("temp", 25)
    humidity = weather_data.get("main", {}).get("humidity", 60)
    wind_speed = weather_data.get("wind", {}).get("speed", 10)
    pressure = weather_data.get("main", {}).get("pressure", 1013)
    
    risk_score = 3.0
    
    if temp > 35 or temp < 5:
        risk_score += 2
    elif temp > 30 or temp < 10:
        risk_score += 1
    
    storm_risk = 2.0
    if wind_speed > 20:
        storm_risk = 8.0
        risk_score += 2
    elif wind_speed > 15:
        storm_risk = 6.0
        risk_score += 1
    elif wind_speed > 10:
        storm_risk = 4.0
    
    fire_risk = 2.0
    if humidity < 30:
        fire_risk = 7.0
        risk_score += 1.5
    elif humidity < 50:
        fire_risk = 4.0
    
    flood_risk = 2.0
    if humidity > 80:
        flood_risk = 6.0
        risk_score += 1
    elif humidity > 70:
        flood_risk = 4.0
    
    if pressure < 1000:
        risk_score += 1.5
        storm_risk += 2
    
    if risk_score >= 8:
        overall_risk = "critical"
    elif risk_score >= 6:
        overall_risk = "high"
    elif risk_score >= 4:
        overall_risk = "moderate"
    else:
        overall_risk = "low"
    
    return {
        "overall_risk": overall_risk,
        "risk_score": min(round(risk_score, 1), 10),
        "flood_risk": min(round(flood_risk, 1), 10),
        "fire_risk": min(round(fire_risk, 1), 10),
        "earthquake_risk": round(random.uniform(1, 3), 1),
        "storm_risk": min(round(storm_risk, 1), 10),
        "confidence": 0.85
    }

class handler(BaseHTTPRequestHandler):
    def _get_coordinates(self):
        """Extract coordinates from query params or POST body"""
        # Try query params first
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        lat = params.get('lat', [None])[0]
        lon = params.get('lon', [None])[0]
        
        # If POST, try to read from body
        if self.command == 'POST' and (lat is None or lon is None):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length)
                    data = json.loads(body.decode())
                    lat = data.get('latitude', data.get('lat', lat))
                    lon = data.get('longitude', data.get('lon', lon))
            except:
                pass
        
        # Default coordinates (Delhi)
        lat = float(lat) if lat else 28.6139
        lon = float(lon) if lon else 77.2090
        return lat, lon
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        try:
            lat, lon = self._get_coordinates()
            
            # Fetch weather
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
            
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as response:
                    weather_data = json.loads(response.read().decode())
                
                risk = calculate_risk(weather_data)
                result = {
                    "success": True,
                    "is_real": True,
                    **risk,
                    "location_analyzed": {"latitude": lat, "longitude": lon},
                    "model_version": "RuleBased-v1",
                    "timestamp": datetime.now().isoformat()
                }
            except:
                result = {
                    "success": True,
                    "is_real": False,
                    "overall_risk": "moderate",
                    "risk_score": 4.5,
                    "flood_risk": 3.2,
                    "fire_risk": 2.8,
                    "earthquake_risk": 1.5,
                    "storm_risk": 4.1,
                    "confidence": 0.75,
                    "location_analyzed": {"latitude": lat, "longitude": lon},
                    "model_version": "fallback",
                    "timestamp": datetime.now().isoformat()
                }
            
            self._send_json(result)
            
        except Exception as e:
            self._send_json({"error": str(e), "success": False}, 500)
        return
    
    def do_POST(self):
        return self.do_GET()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        return
