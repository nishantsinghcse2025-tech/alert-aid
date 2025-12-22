"""
Alert Aid - Earthquakes Endpoint
Fetches earthquake data from USGS
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
            days = int(params.get('days', ['7'])[0])
            min_magnitude = float(params.get('min_magnitude', ['2.5'])[0])
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            usgs_params = {
                "format": "geojson",
                "starttime": start_time.strftime("%Y-%m-%d"),
                "endtime": end_time.strftime("%Y-%m-%d"),
                "minmagnitude": str(min_magnitude),
                "latitude": str(lat),
                "longitude": str(lon),
                "maxradiuskm": "2000",
                "limit": "50"
            }
            
            url = f"{USGS_EARTHQUAKE_URL}?{urllib.parse.urlencode(usgs_params)}"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
            
            result = {
                "success": True,
                "is_real": True,
                "source": "USGS",
                "earthquakes": data.get("features", []),
                "count": len(data.get("features", [])),
                "query_params": {
                    "latitude": lat,
                    "longitude": lon,
                    "days": days,
                    "min_magnitude": min_magnitude
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "success": False}).encode())
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        return
