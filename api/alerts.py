"""
Alert Aid - Active Alerts Endpoint
Fetches earthquake and weather alerts from USGS and other sources
"""

from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

USGS_EARTHQUAKE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            lat = float(params.get('lat', ['28.6139'])[0])
            lon = float(params.get('lon', ['77.2090'])[0])
            
            # Fetch earthquakes from USGS
            earthquakes = []
            try:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=1)
                
                usgs_params = {
                    "format": "geojson",
                    "starttime": start_time.strftime("%Y-%m-%d"),
                    "endtime": end_time.strftime("%Y-%m-%d"),
                    "minmagnitude": "2.5",
                    "latitude": str(lat),
                    "longitude": str(lon),
                    "maxradiuskm": "500"
                }
                
                url = f"{USGS_EARTHQUAKE_URL}?{urllib.parse.urlencode(usgs_params)}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                
                for feature in data.get("features", [])[:5]:
                    props = feature.get("properties", {})
                    earthquakes.append({
                        "id": feature.get("id"),
                        "magnitude": props.get("mag"),
                        "place": props.get("place"),
                        "time": props.get("time"),
                        "type": "earthquake"
                    })
            except Exception as e:
                print(f"USGS API error: {e}")
            
            # Generate alerts from earthquakes
            alerts = []
            for eq in earthquakes:
                mag = eq.get('magnitude', 0) or 0
                alerts.append({
                    "id": f"eq-{eq['id']}",
                    "title": f"Earthquake Alert - M{mag}",
                    "description": f"Earthquake detected: {eq['place']}",
                    "severity": "Severe" if mag >= 5.0 else "Moderate",
                    "urgency": "Immediate" if mag >= 5.0 else "Expected",
                    "event": "Earthquake",
                    "areas": [eq['place']] if eq['place'] else [],
                    "onset": datetime.now().isoformat(),
                    "expires": (datetime.now() + timedelta(hours=6)).isoformat()
                })
            
            result = {
                "alerts": alerts,
                "count": len(alerts),
                "source": "Alert_Aid_System",
                "is_real": len(earthquakes) > 0,
                "location": {"latitude": lat, "longitude": lon},
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            result = {
                "alerts": [],
                "count": 0,
                "source": "Alert_Aid_System",
                "is_real": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(result).encode())
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        return
