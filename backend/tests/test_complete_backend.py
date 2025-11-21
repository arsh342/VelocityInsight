#!/usr/bin/env python3
"""
Comprehensive test script for GR-Insight Backend API.
Tests all endpoints including tire degradation, pit strategy, and analytics.
"""
import requests
import json
from pathlib import Path
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")

def test_endpoint(endpoint: str, description: str, params: Dict[str, Any] = None) -> Any:
    """Test a GET endpoint and return response."""
    print(f"\n{Colors.BOLD}Testing:{Colors.END} {description}")
    print(f"  Endpoint: {endpoint}")
    
    try:
        # Increase timeout for endpoints that load large datasets
        timeout = 30 if any(x in endpoint for x in ['/telemetry', '/laps', '/driving-style', '/pit/']) else 15
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=timeout)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Success! Response size: {len(json.dumps(data))} bytes")
            return data
        else:
            print_error(f"Failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print_error("Request timeout (30s limit)")
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def main():
    print(f"\n{Colors.BOLD}🏎️  GR-Insight Backend Comprehensive Test Suite{Colors.END}")
    print(f"{Colors.BOLD}Testing all endpoints for race strategy & analytics{Colors.END}\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Test 1: Root endpoint
    print_section("1. Core API Tests")
    data = test_endpoint("/", "Root health check")
    if data:
        results["passed"] += 1
        print(f"  Service: {data.get('service')}")
        print(f"  Version: {data.get('version')}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 2: Tracks endpoint
    data = test_endpoint("/tracks", "Available tracks and races")
    if data:
        results["passed"] += 1
        print(f"  Total tracks: {data.get('total_tracks')}")
        if data.get('tracks'):
            print(f"  Sample track: {data['tracks'][0]['name']}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 3: Telemetry endpoint
    print_section("2. Telemetry & Data Tests")
    data = test_endpoint("/telemetry", "Raw telemetry data", {"track": "barber", "race": "R1", "limit": 10})
    if data:
        results["passed"] += 1
        print(f"  Records returned: {data.get('count')}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 4: Laps endpoint
    data = test_endpoint("/laps", "Lap time analysis", {"track": "barber", "race": "R1"})
    if data:
        results["passed"] += 1
        print(f"  Vehicles analyzed: {len(data.get('laps_by_vehicle', {}))}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 5: Tire Degradation Analysis
    print_section("3. Tire Degradation Analytics")
    data = test_endpoint("/analytics/degradation/barber/R1", "Tire degradation analysis")
    if data:
        results["passed"] += 1
        model_perf = data.get('model_performance', {})
        print(f"  Model R² Score: {model_perf.get('r2_score', 0):.3f}")
        print(f"  Degradation Rate: {model_perf.get('avg_degradation_rate_per_lap', 0):.3f}% per lap")
        print(f"  Training Samples: {model_perf.get('samples', 0)}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 6: Tire Degradation Predictions
    data = test_endpoint(
        "/analytics/degradation/barber/R1/GR86-002-000/predictions",
        "Tire degradation predictions",
        {"current_tire_age": 10, "prediction_laps": 5}
    )
    if data:
        results["passed"] += 1
        stint = data.get('stint_recommendation', {})
        print(f"  Recommendation: {stint.get('recommendation')}")
        print(f"  Optimal Tire Age for Pit: {stint.get('optimal_tire_age_for_pit')}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 7: Driving Style Analysis
    data = test_endpoint(
        "/analytics/driving-style/barber/R1/GR86-002-000",
        "Driving style analysis"
    )
    if data:
        results["passed"] += 1
        metrics = data.get('driving_style_metrics', {})
        print(f"  Aggression Score: {metrics.get('composite_aggression_score', 0):.1f}/100")
        print(f"  Style Impact: {data.get('style_impact_assessment')}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 8: Pit Stop Strategy
    print_section("4. Pit Stop Strategy Optimization")
    data = test_endpoint(
        "/strategy/pit/barber/R1/GR86-002-000",
        "Pit stop strategy calculation",
        {
            "current_lap": 10,
            "total_race_laps": 30,
            "current_tire_age": 8,
            "track_position": 5
        }
    )
    if data:
        results["passed"] += 1
        strategy = data.get('pit_strategy', {})
        print(f"  Optimal Pit Lap: {strategy.get('optimal_pit_lap')}")
        print(f"  Laps Until Pit: {strategy.get('laps_until_pit')}")
        print(f"  Recommendation: {strategy.get('recommendation')}")
        print(f"  Net Advantage: {strategy.get('net_advantage', 0):.2f}s")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 9: Undercut Analysis
    data = test_endpoint(
        "/strategy/pit/barber/R1/GR86-002-000/undercut",
        "Undercut opportunity analysis",
        {
            "current_lap": 15,
            "own_tire_age": 12,
            "competitor_tire_age": 10,
            "gap_to_competitor": 3.5
        }
    )
    if data:
        results["passed"] += 1
        analysis = data.get('undercut_analysis', {})
        print(f"  Undercut Viable: {analysis.get('undercut_viable')}")
        print(f"  Time Gain Potential: {analysis.get('time_gain_potential', 0):.2f}s")
        print(f"  Recommendation: {analysis.get('recommendation')}")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 10: Strategy Comparison
    data = test_endpoint(
        "/strategy/compare/barber/R1",
        "Strategy comparison",
        {
            "vehicle_id": "GR86-002-000",
            "current_lap": 5,
            "total_race_laps": 30,
            "current_tire_age": 4
        }
    )
    if data:
        results["passed"] += 1
        print(f"  Recommended Strategy: {data.get('recommended_strategy')}")
        comparisons = data.get('strategy_comparison', [])
        if comparisons:
            print(f"  Fastest Strategy: {comparisons[0]['strategy']}")
            print(f"  Projected Time: {comparisons[0]['total_time']:.2f}s")
    else:
        results["failed"] += 1
    results["total"] += 1
    
    # Test 11: WebSocket endpoint info
    print_section("5. Real-time Streaming")
    print_info("WebSocket live telemetry available at:")
    print(f"  ws://localhost:8000/ws/live/barber/R1")
    print_info("Use a WebSocket client to test real-time data streaming")
    
    # Print summary
    print_section("Test Summary")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    
    success_rate = (results['passed'] / results['total']) * 100
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Backend is fully operational!{Colors.END}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Most tests passed. Check failed tests above.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Multiple tests failed. Backend needs attention.{Colors.END}")
    
    print(f"\n{Colors.BOLD}API Documentation: http://localhost:8000/docs{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to backend. Make sure the server is running:")
        print("  cd backend && uvicorn app.main:app --reload")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print_error(f"Test suite failed: {e}")
