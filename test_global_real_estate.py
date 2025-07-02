#!/usr/bin/env python3
"""
Test script to verify global real estate functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.mcp.tools.context7_tools import Context7Tools

def test_global_real_estate():
    """Test real estate search with global locations."""
    tools = Context7Tools()
    
    # Test locations from different regions
    test_locations = [
        "London, UK",
        "Lagos, Nigeria", 
        "Madrid, Spain",
        "Paris, France",
        "Rome, Italy",
        "Dublin, Ireland",
        "Cape Town, South Africa",
        "New York, USA"
    ]
    
    print("🏠 Testing Global Real Estate Search\n")
    
    for location in test_locations:
        print(f"📍 Testing location: {location}")
        
        result = tools.scout_real_estate(
            location=location,
            property_type="apartment",
            min_price=100000,
            max_price=500000,
            bedrooms=2
        )
        
        if result.get("success"):
            properties = result.get("properties", [])
            viewing_links = result.get("viewing_links", {})
            
            print(f"   ✅ Found {len(properties)} properties")
            
            if properties:
                sample_property = properties[0]
                print(f"   🏡 Sample property: {sample_property.get('platform')} - {sample_property.get('currency')} {sample_property.get('price'):,}")
                print(f"   🌍 Region: {sample_property.get('region')}")
            
            # Show available platforms
            platforms = list(viewing_links.keys())
            print(f"   🔗 Available platforms: {', '.join(platforms[:5])}{'...' if len(platforms) > 5 else ''}")
            
        else:
            print(f"   ❌ Error: {result.get('error')}")
        
        print()

if __name__ == "__main__":
    test_global_real_estate()
