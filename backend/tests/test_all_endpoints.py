#!/usr/bin/env python3
"""
Comprehensive test script for ALL GR-Insight Backend API endpoints.
Tests all 20+ endpoints across all modules.
"""
import requests
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.errors = []
        self.warnings = []

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_endpoint(
    method: str,
    endpoint: str,
    description: str,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    results: Optional[TestResults] = None
) -> Optional[Dict[str, Any]]:
    """Test an endpoint and return response."""
    print(f"\n{Colors.BOLD}Testing:{Colors.END} {description}")
    print(f"  {method.upper()} {endpoint}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", params=params, json=json_data, timeout=timeout)
        else:
            print_error(f"Unsupported method: {method}")
            if results:
                results.failed += 1
                results.total += 1
            return None
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                data = response.json()
                size = len(json.dumps(data))
                print_success(f"Success! Response size: {size:,} bytes")
                if results:
                    results.passed += 1
                return data
            except json.JSONDecodeError:
                print_warning(f"Response is not JSON: {response.text[:100]}")
                if results:
                    results.passed += 1  # Still counts as success if endpoint responded
                return {"raw_response": response.text[:200]}
        elif response.status_code == 404:
            print_warning(f"Not found (404) - may be expected for some endpoints")
            if results:
                results.warnings.append(f"{endpoint}: 404 Not Found")
            return None
        elif response.status_code in [400, 422]:
            print_warning(f"Bad request (400/422) - check parameters")
            print(f"  Response: {response.text[:200]}")
            if results:
                results.warnings.append(f"{endpoint}: {response.status_code}")
            return None
        else:
            print_error(f"Failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            if results:
                results.failed += 1
                results.errors.append(f"{endpoint}: {response.status_code} - {response.text[:100]}")
            return None
            
    except requests.exceptions.Timeout:
        print_error(f"Request timeout ({timeout}s limit)")
        if results:
            results.failed += 1
            results.errors.append(f"{endpoint}: Timeout")
        return None
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to backend. Make sure server is running:")
        print(f"  cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        if results:
            results.failed += 1
            results.errors.append(f"{endpoint}: Connection Error")
        return None
    except Exception as e:
        print_error(f"Error: {e}")
        if results:
            results.failed += 1
            results.errors.append(f"{endpoint}: {str(e)}")
        return None
    finally:
        if results:
            results.total += 1

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🏎️  GR-Insight Backend - Comprehensive Endpoint Test Suite{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}Testing ALL endpoints across all modules{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    results = TestResults()
    
    # Test data constants
    TEST_TRACK = "barber"
    TEST_RACE = "R1"
    TEST_VEHICLE = "GR86-002-000"
    TEST_LAP = 5
    
    # ========================================================================
    # 1. CORE API ENDPOINTS
    # ========================================================================
    print_section("1. Core API Endpoints")
    
    data = test_endpoint("GET", "/", "Root health check", results=results)
    if data:
        print(f"  Service: {data.get('service')}")
        print(f"  Version: {data.get('version')}")
    
    data = test_endpoint("GET", "/tracks", "Available tracks and races", results=results)
    if data:
        print(f"  Total tracks: {data.get('total_tracks')}")
        if data.get('tracks'):
            print(f"  Sample tracks: {', '.join([t['name'] for t in data['tracks'][:3]])}")
    
    # Test individual track races endpoint
    data = test_endpoint("GET", f"/tracks/{TEST_TRACK}/races", "Get races for specific track", results=results)
    if data:
        print(f"  Track: {data.get('track')}")
        print(f"  Races: {data.get('races')}")
    
    # ========================================================================
    # 2. TELEMETRY ENDPOINTS
    # ========================================================================
    print_section("2. Telemetry & Lap Data Endpoints")
    
    # Telemetry endpoint
    data = test_endpoint(
        "GET",
        "/telemetry",
        "Raw telemetry data",
        params={"track": TEST_TRACK, "race": TEST_RACE, "limit": 10},
        timeout=30,
        results=results
    )
    if data:
        print(f"  Records returned: {data.get('count')}")
        print(f"  Columns: {len(data.get('columns', []))}")
    
    # Telemetry with vehicle filter
    data = test_endpoint(
        "GET",
        "/telemetry",
        "Telemetry filtered by vehicle",
        params={"track": TEST_TRACK, "race": TEST_RACE, "vehicle_id": TEST_VEHICLE, "limit": 10},
        timeout=30,
        results=results
    )
    if data:
        print(f"  Vehicle: {data.get('vehicle_id')}")
        print(f"  Records: {data.get('count')}")
    
    # Laps endpoint
    data = test_endpoint(
        "GET",
        "/laps",
        "Lap time analysis",
        params={"track": TEST_TRACK, "race": TEST_RACE},
        timeout=30,
        results=results
    )
    if data:
        print(f"  Vehicles analyzed: {len(data.get('laps_by_vehicle', {}))}")
        print(f"  Total lap records: {data.get('total_lap_records')}")
    
    # Lap times endpoint
    data = test_endpoint(
        "GET",
        "/laps/times",
        "Lap times with timing data",
        params={"track": TEST_TRACK, "race": TEST_RACE, "vehicle_id": TEST_VEHICLE},
        timeout=30,
        results=results
    )
    if data:
        print(f"  Total records: {data.get('total_records')}")
        print(f"  Lap times available: {len(data.get('lap_times', []))}")
    
    # ========================================================================
    # 3. ANALYTICS ENDPOINTS
    # ========================================================================
    print_section("3. Analytics Endpoints")
    
    # Tire degradation analysis
    data = test_endpoint(
        "GET",
        f"/analytics/degradation/{TEST_TRACK}/{TEST_RACE}",
        "Tire degradation analysis",
        timeout=45,
        results=results
    )
    if data:
        model_perf = data.get('model_performance', {})
        print(f"  Model R² Score: {model_perf.get('r2_score', 0):.3f}")
        print(f"  Degradation Rate: {model_perf.get('avg_degradation_rate_per_lap', 0):.3f}% per lap")
        print(f"  Total vehicles: {data.get('summary_statistics', {}).get('total_vehicles', 0)}")
    
    # Tire degradation predictions
    data = test_endpoint(
        "GET",
        f"/analytics/degradation/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}/predictions",
        "Tire degradation predictions",
        params={"current_tire_age": 10, "prediction_laps": 5},
        timeout=45,
        results=results
    )
    if data:
        stint = data.get('stint_recommendation', {})
        print(f"  Optimal Tire Age for Pit: {stint.get('optimal_tire_age_for_pit')}")
        print(f"  Baseline Time: {data.get('baseline_time', 0):.2f}s")
    
    # Driving style analysis
    data = test_endpoint(
        "GET",
        f"/analytics/driving-style/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}",
        "Driving style analysis",
        params={"sample_size": 1000},
        timeout=45,
        results=results
    )
    if data:
        metrics = data.get('driving_style_metrics', {})
        print(f"  Aggression Score: {metrics.get('composite_aggression_score', 0):.1f}/100")
        print(f"  Style Impact: {data.get('style_impact_assessment')}")
    
    # ========================================================================
    # 4. STRATEGY ENDPOINTS
    # ========================================================================
    print_section("4. Pit Stop Strategy Endpoints")
    
    # Pit strategy
    data = test_endpoint(
        "GET",
        f"/strategy/pit/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}",
        "Pit stop strategy calculation",
        params={
            "current_lap": 10,
            "total_race_laps": 30,
            "current_tire_age": 8,
            "track_position": 5
        },
        timeout=45,
        results=results
    )
    if data:
        strategy = data.get('pit_strategy', {})
        print(f"  Optimal Pit Lap: {strategy.get('optimal_pit_lap')}")
        print(f"  Recommendation: {strategy.get('recommendation')}")
        print(f"  Net Advantage: {strategy.get('net_advantage', 0):.2f}s")
    
    # Undercut analysis
    data = test_endpoint(
        "GET",
        f"/strategy/pit/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}/undercut",
        "Undercut opportunity analysis",
        params={
            "current_lap": 15,
            "own_tire_age": 12,
            "competitor_tire_age": 10,
            "gap_to_competitor": 3.5
        },
        timeout=45,
        results=results
    )
    if data:
        analysis = data.get('undercut_analysis', {})
        print(f"  Undercut Viable: {analysis.get('undercut_viable')}")
        print(f"  Time Gain Potential: {analysis.get('time_gain_potential', 0):.2f}s")
    
    # Strategy comparison
    data = test_endpoint(
        "GET",
        f"/strategy/compare/{TEST_TRACK}/{TEST_RACE}",
        "Strategy comparison (multi-strategy)",
        params={
            "vehicle_id": TEST_VEHICLE,
            "current_lap": 5,
            "total_race_laps": 30,
            "current_tire_age": 4
        },
        timeout=45,
        results=results
    )
    if data:
        print(f"  Recommended Strategy: {data.get('recommended_strategy')}")
        comparisons = data.get('strategy_comparison', [])
        if comparisons:
            print(f"  Fastest Strategy: {comparisons[0]['strategy']}")
            print(f"  Projected Time: {comparisons[0]['total_time']:.2f}s")
    
    # Strategy simulation (POST)
    data = test_endpoint(
        "POST",
        f"/strategy/pit/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}/simulate",
        "Race strategy simulation",
        params={
            "current_lap": 10,
            "total_race_laps": 30,
            "current_tire_age": 8,
            "pit_laps": [15, 25]
        },
        timeout=45,
        results=results
    )
    if data:
        sim = data.get('simulation_results', {})
        print(f"  Total Race Time: {sim.get('total_race_time', 0):.2f}s")
        print(f"  Average Lap Time: {sim.get('average_lap_time', 0):.2f}s")
    
    # ========================================================================
    # 5. PREDICTIONS ENDPOINTS
    # ========================================================================
    print_section("5. Lap Time Prediction Endpoints")
    
    # Predict lap time
    data = test_endpoint(
        "GET",
        f"/predictions/laptime/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}",
        "Predict lap time for specific lap",
        params={"lap_number": TEST_LAP},
        timeout=30,
        results=results
    )
    if data:
        print(f"  Predicted Lap Time: {data.get('predicted_lap_time')}s")
        print(f"  Model Source: {data.get('model_source')}")
        if data.get('actual_lap_time'):
            print(f"  Actual Lap Time: {data.get('actual_lap_time')}s")
            print(f"  Error: {data.get('error')}s")
    
    # Predict next lap
    data = test_endpoint(
        "GET",
        f"/predictions/laptime/next/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}",
        "Predict next lap time",
        timeout=30,
        results=results
    )
    if data:
        print(f"  Current Lap: {data.get('current_lap')}")
        print(f"  Predicted Next Lap: {data.get('predicted_next_lap_time')}s")
        print(f"  Model Source: {data.get('model_source')}")
    
    # ========================================================================
    # 6. SIMULATION ENDPOINTS
    # ========================================================================
    print_section("6. Race Simulation Endpoints")
    
    # Full race simulation
    data = test_endpoint(
        "GET",
        f"/simulation/race/{TEST_TRACK}/{TEST_RACE}",
        "Full race simulation with multiple strategies",
        params={"strategies": "all"},
        timeout=60,
        results=results
    )
    if data:
        config = data.get('simulation_config', {})
        print(f"  Baseline Lap Time: {config.get('baseline_lap_time', 0):.2f}s")
        print(f"  Total Race Laps: {config.get('total_race_laps')}")
        print(f"  Strategies Simulated: {config.get('strategies_simulated')}")
        results_list = data.get('results', [])
        if results_list:
            print(f"  Winner Strategy: {results_list[0].get('strategy_name')}")
    
    # Strategy comparison
    data = test_endpoint(
        "GET",
        f"/simulation/compare/{TEST_TRACK}/{TEST_RACE}",
        "Compare two strategies side-by-side",
        params={"strategy1": "one_stop_early", "strategy2": "one_stop_late"},
        timeout=60,
        results=results
    )
    if data:
        print(f"  Strategy 1: {data.get('strategy1')}")
        print(f"  Strategy 2: {data.get('strategy2')}")
        print(f"  Winner: {data.get('winner')}")
        print(f"  Time Difference: {data.get('time_difference', 0):.2f}s")
    
    # ========================================================================
    # 7. CONSISTENCY ENDPOINTS
    # ========================================================================
    print_section("7. Driver Consistency Endpoints")
    
    # Driver consistency
    data = test_endpoint(
        "GET",
        f"/consistency/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}",
        "Driver consistency analysis",
        timeout=45,
        results=results
    )
    if data:
        print(f"  Consistency Score: {data.get('consistency_score', 0):.1f}/100")
        stats = data.get('lap_time_statistics', {})
        if stats:
            print(f"  Average Lap Time: {stats.get('mean', 0):.2f}s")
            print(f"  Standard Deviation: {stats.get('std', 0):.2f}s")
    
    # Driver strengths
    data = test_endpoint(
        "GET",
        f"/consistency/{TEST_TRACK}/{TEST_RACE}/{TEST_VEHICLE}/strengths",
        "Driver strengths and weaknesses",
        timeout=45,
        results=results
    )
    if data:
        strengths = data.get('strongest_sector', {})
        if strengths:
            print(f"  Strongest Sector: {strengths.get('sector')}")
    
    # ========================================================================
    # 8. TEST MULTIPLE TRACKS
    # ========================================================================
    print_section("8. Multi-Track Testing")
    
    test_tracks = ["barber", "indianapolis", "COTA"]
    for track in test_tracks:
        data = test_endpoint(
            "GET",
            f"/tracks/{track}/races",
            f"Test track: {track}",
            timeout=10,
            results=results
        )
        if data:
            print(f"  ✓ {track} - {len(data.get('races', []))} races available")
    
    # ========================================================================
    # TEST SUMMARY
    # ========================================================================
    print_section("Test Summary")
    
    print(f"{Colors.BOLD}Total Tests Executed: {results.total}{Colors.END}")
    print(f"{Colors.GREEN}✅ Passed: {results.passed}{Colors.END}")
    print(f"{Colors.RED}❌ Failed: {results.failed}{Colors.END}")
    if results.warnings:
        print(f"{Colors.YELLOW}⚠️  Warnings: {len(results.warnings)}{Colors.END}")
    
    success_rate = (results.passed / results.total * 100) if results.total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if results.warnings:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}Warnings:{Colors.END}")
        for warning in results.warnings[:10]:  # Show first 10 warnings
            print(f"  ⚠️  {warning}")
    
    if results.errors:
        print(f"\n{Colors.RED}{Colors.BOLD}Errors:{Colors.END}")
        for error in results.errors[:10]:  # Show first 10 errors
            print(f"  ❌ {error}")
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    if success_rate == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! Backend is fully operational!{Colors.END}")
    elif success_rate >= 80:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Most tests passed. Check warnings/errors above.{Colors.END}")
    elif success_rate >= 60:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Review errors above.{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Multiple tests failed. Backend needs attention.{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    
    print(f"\n{Colors.BOLD}API Documentation: http://localhost:8000/docs{Colors.END}")
    print(f"{Colors.BOLD}OpenAPI Schema: http://localhost:8000/openapi.json{Colors.END}\n")
    
    return results

if __name__ == "__main__":
    try:
        results = main()
        exit(0 if results.failed == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        exit(1)
    except Exception as e:
        print_error(f"Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
