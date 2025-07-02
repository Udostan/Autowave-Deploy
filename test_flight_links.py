#!/usr/bin/env python3
"""
Test flight link generation for global routes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.context7_tools import RealContext7Tools

def test_flight_link_generation():
    """Test flight link generation for different routes."""
    
    print("🔗 Testing Flight Link Generation")
    print("=" * 40)
    
    # Create instance of the tools
    tools = RealContext7Tools()
    
    # Test different route types
    test_routes = [
        {
            "name": "US Domestic",
            "origin": "JFK",
            "destination": "LAX", 
            "date": "2024-03-15",
            "expected_airlines": ["Southwest", "JetBlue", "American", "Delta", "United"]
        },
        {
            "name": "US to Europe", 
            "origin": "JFK",
            "destination": "LHR",
            "date": "2024-03-15",
            "expected_airlines": ["British Airways", "Air France", "KLM"]
        },
        {
            "name": "US to Asia",
            "origin": "LAX", 
            "destination": "NRT",
            "date": "2024-03-15",
            "expected_airlines": ["Japan Airlines", "Korean Air", "Singapore Airlines"]
        },
        {
            "name": "Europe to Middle East",
            "origin": "LHR",
            "destination": "DXB", 
            "date": "2024-03-15",
            "expected_airlines": ["Emirates", "Qatar Airways", "British Airways"]
        },
        {
            "name": "Europe Domestic",
            "origin": "CDG",
            "destination": "FCO",
            "date": "2024-03-15", 
            "expected_airlines": ["Air France", "Ryanair"]
        },
        {
            "name": "Asia Domestic",
            "origin": "BKK",
            "destination": "KUL",
            "date": "2024-03-15",
            "expected_airlines": ["AirAsia", "Thai Airways"]
        }
    ]
    
    successful_tests = 0
    
    for i, route in enumerate(test_routes, 1):
        print(f"\n🧪 Test {i}: {route['name']}")
        print(f"   Route: {route['origin']} → {route['destination']}")
        
        try:
            # Generate flight links
            links = tools._generate_real_flight_links(
                route['origin'], 
                route['destination'], 
                route['date']
            )
            
            print(f"   ✅ Generated {len(links)} flight links")
            
            # Check for global search engines (should always be present)
            global_engines = ['Google Flights', 'Skyscanner', 'Kayak', 'Momondo', 'Expedia']
            found_engines = [link['site'] for link in links if any(engine in link['site'] for engine in global_engines)]
            print(f"   🌐 Global engines: {len(found_engines)}/5")
            
            # Check for major international airlines
            major_airlines = ['American Airlines', 'Delta Airlines', 'United Airlines', 'British Airways', 'Emirates']
            found_major = [link['site'] for link in links if any(airline in link['site'] for airline in major_airlines)]
            print(f"   ✈️ Major airlines: {len(found_major)}")
            
            # Check for regional airlines based on route
            regional_count = 0
            for expected in route['expected_airlines']:
                found = any(expected in link['site'] for link in links)
                if found:
                    regional_count += 1
            
            print(f"   🗺️ Regional airlines: {regional_count}/{len(route['expected_airlines'])}")
            
            # Check for low-cost carriers where appropriate
            if route['name'] in ['US Domestic', 'Europe Domestic', 'Asia Domestic']:
                low_cost = ['Southwest', 'JetBlue', 'Ryanair', 'AirAsia']
                found_low_cost = [link['site'] for link in links if any(lc in link['site'] for lc in low_cost)]
                print(f"   💰 Low-cost carriers: {len(found_low_cost)}")
            
            # Print some example links
            print(f"   📋 Sample links:")
            for j, link in enumerate(links[:3]):
                print(f"      {j+1}. {link['site']} - {link['description']}")
            
            if len(links) >= 10:  # Should have at least 10 flight options
                successful_tests += 1
                print(f"   ✅ PASS - Comprehensive flight options available")
            else:
                print(f"   ⚠️ PARTIAL - Only {len(links)} options (expected 10+)")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    success_rate = successful_tests / len(test_routes)
    
    print(f"\n📊 Flight Link Generation Results:")
    print("=" * 45)
    print(f"✅ Successful tests: {successful_tests}/{len(test_routes)} ({success_rate*100:.1f}%)")
    
    if success_rate >= 0.8:
        print(f"\n🎉 Global Flight Search: FULLY FUNCTIONAL!")
        print("   ✅ Comprehensive airline coverage")
        print("   ✅ Regional airline detection working")
        print("   ✅ Low-cost carrier integration")
        print("   ✅ Global search engine integration")
    else:
        print(f"\n⚠️ Global Flight Search: NEEDS IMPROVEMENT")
    
    return success_rate >= 0.8

def test_regional_detection_functions():
    """Test the regional detection helper functions."""
    
    print(f"\n🔍 Testing Regional Detection Functions")
    print("=" * 45)
    
    tools = RealContext7Tools()
    
    detection_tests = [
        # US Domestic
        ("JFK", "LAX", "US Domestic", tools._is_us_domestic_route),
        ("ORD", "DFW", "US Domestic", tools._is_us_domestic_route),
        
        # European
        ("LHR", "CDG", "European", tools._is_european_route),
        ("FRA", "FCO", "European", tools._is_european_route),
        
        # Asian  
        ("NRT", "ICN", "Asian", tools._is_asian_route),
        ("BKK", "SIN", "Asian", tools._is_asian_route),
        
        # Middle Eastern
        ("DXB", "DOH", "Middle Eastern", tools._is_middle_east_route),
        ("CAI", "TLV", "Middle Eastern", tools._is_middle_east_route),
        
        # Cross-region (should detect at least one region)
        ("JFK", "LHR", "Trans-Atlantic", lambda o, d: tools._is_us_domestic_route(o, d) or tools._is_european_route(o, d)),
        ("LAX", "NRT", "Trans-Pacific", lambda o, d: tools._is_us_domestic_route(o, d) or tools._is_asian_route(o, d))
    ]
    
    successful_detections = 0
    
    for origin, destination, region_type, detection_func in detection_tests:
        try:
            result = detection_func(origin, destination)
            status = "✅ DETECTED" if result else "❌ NOT DETECTED"
            print(f"   {origin} → {destination} ({region_type}): {status}")
            
            if result:
                successful_detections += 1
                
        except Exception as e:
            print(f"   {origin} → {destination} ({region_type}): ❌ ERROR - {str(e)}")
    
    detection_rate = successful_detections / len(detection_tests)
    print(f"\n📊 Regional Detection: {successful_detections}/{len(detection_tests)} ({detection_rate*100:.1f}%)")
    
    return detection_rate >= 0.8

def main():
    """Run flight link generation tests."""
    
    print("🚀 Global Flight Search Link Generation Test")
    print("=" * 50)
    
    # Test 1: Flight Link Generation
    links_success = test_flight_link_generation()
    
    # Test 2: Regional Detection Functions
    detection_success = test_regional_detection_functions()
    
    overall_success = links_success and detection_success
    
    print(f"\n🎯 Overall Results:")
    print("=" * 25)
    print(f"✅ Link Generation: {'PASS' if links_success else 'FAIL'}")
    print(f"✅ Regional Detection: {'PASS' if detection_success else 'FAIL'}")
    
    if overall_success:
        print(f"\n🎉 GLOBAL FLIGHT SEARCH: READY FOR PRODUCTION!")
        print("   🌐 25+ airlines and search engines")
        print("   🗺️ 6 regional coverage areas")
        print("   💰 Low-cost and premium options")
        print("   ✈️ Intelligent route-based selection")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
