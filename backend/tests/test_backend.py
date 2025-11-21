#!/usr/bin/env python3
"""
Quick test script to validate the backend works with real data.
Run this after starting the FastAPI server.
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    print("Testing GR-Insight Backend...")
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test tracks endpoint
    print("\n2. Testing tracks endpoint...")
    response = requests.get(f"{BASE_URL}/tracks")
    print(f"Status: {response.status_code}")
    tracks = response.json()
    print(f"Available tracks: {len(tracks.get('tracks', []))}")
    for track in tracks.get('tracks', [])[:3]:  # Show first 3
        print(f"  - {track['name']}: {track['races']}")
    
    # Test telemetry endpoint
    print("\n3. Testing telemetry endpoint...")
    response = requests.get(f"{BASE_URL}/telemetry?track=barber&race=R1&limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Telemetry rows: {data['count']}")
        print(f"Columns: {len(data['columns'])}")
        if data['rows']:
            print(f"Sample row keys: {list(data['rows'][0].keys())}")
    
    # Test laps endpoint
    print("\n4. Testing laps endpoint...")
    response = requests.get(f"{BASE_URL}/laps?track=barber&race=R1")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Lap count: {data['lap_count']}")
        print(f"Lap stats rows: {len(data['lap_stats'])}")
    
    # Test different track
    print("\n5. Testing Indianapolis track...")
    response = requests.get(f"{BASE_URL}/telemetry?track=indianapolis&race=R1&limit=3")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Indianapolis telemetry rows: {data['count']}")
    
    print("\n✅ Backend test complete!")

if __name__ == "__main__":
    try:
        test_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure the server is running:")
        print("   uvicorn app.main:app --reload --app-dir backend/app")
    except Exception as e:
        print(f"❌ Test failed: {e}")
