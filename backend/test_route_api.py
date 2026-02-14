import requests
import json

url = "http://localhost:8000/api/forecast/optimize-route/"
data = {
    "floor_idx": 0,
    "start_pos": {"x": 0, "y": 0},
    "picks": [
        {"x": 5, "y": 10},
        {"x": 15, "y": 3}
    ]
}

try:
    response = requests.post(url, json=data, timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
