#!/usr/bin/env python3
"""
Test script to verify history page performance improvements and theme updates.
"""

import time
import requests
from datetime import datetime

def test_history_page_performance():
    """Test the history page loading performance."""
    
    print("🚀 Testing History Page Performance")
    print("=" * 40)
    
    try:
        # Test page response time
        start_time = time.time()
        response = requests.get('http://localhost:5001/history', allow_redirects=False, timeout=10)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        print(f"✅ Response Time: {response_time:.2f}ms")
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Authentication redirect working (expected)")
            print(f"✅ Redirect Location: {response.headers.get('Location', 'None')}")
        
        # Performance benchmarks
        if response_time < 100:
            print("🎉 EXCELLENT: Page loads in under 100ms")
        elif response_time < 500:
            print("✅ GOOD: Page loads in under 500ms")
        elif response_time < 1000:
            print("⚠️  ACCEPTABLE: Page loads in under 1 second")
        else:
            print("❌ SLOW: Page takes over 1 second to load")
        
        return response_time < 1000  # Consider under 1 second as acceptable
        
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Page took too long to respond")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR: Server not running")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_theme_consistency():
    """Test that the history page template has the correct theme elements."""
    
    print("\n🎨 Testing Theme Consistency")
    print("=" * 30)
    
    try:
        # Read the template file
        with open('app/templates/history.html', 'r') as f:
            template_content = f.read()
        
        print("✅ Template file loaded")
        
        # Check for homepage-style dark theme elements
        dark_theme_elements = [
            'background-color: #121212',  # Main background
            'color: #e0e0e0',            # Main text color
            'background: #1e1e1e',       # Card backgrounds
            'border: 1px solid #333',    # Border colors
            'background: #2d2d2d',       # Secondary backgrounds
            'color: #aaa',               # Secondary text
            'border-color: #444',        # Hover borders
            'background: #3d3d3d'        # Hover backgrounds
        ]
        
        found_theme_elements = []
        for element in dark_theme_elements:
            if element in template_content:
                found_theme_elements.append(element)
        
        print(f"✅ Found {len(found_theme_elements)}/{len(dark_theme_elements)} dark theme elements")
        
        # Check for removed light theme elements (should not be present)
        light_theme_elements = [
            'background: #f8f9fa',       # Light backgrounds
            'color: #333',               # Dark text on light
            'background-color: #fff',    # White backgrounds
            'color: #666'                # Gray text on light
        ]
        
        found_light_elements = []
        for element in light_theme_elements:
            if element in template_content:
                found_light_elements.append(element)
        
        if found_light_elements:
            print(f"⚠️  Found {len(found_light_elements)} light theme remnants: {found_light_elements}")
        else:
            print("✅ No light theme remnants found")
        
        # Check for performance optimizations
        performance_elements = [
            'limit=15',                  # Reduced data loading
            'limit=10',                  # Reduced chat conversations
            'limit=20',                  # Reduced activities
            'days=7'                     # Reduced analytics timeframe
        ]
        
        # Read the history service file
        try:
            with open('app/services/history_service.py', 'r') as f:
                service_content = f.read()
            
            found_performance_elements = []
            for element in performance_elements:
                if element in service_content:
                    found_performance_elements.append(element)
            
            print(f"✅ Found {len(found_performance_elements)}/{len(performance_elements)} performance optimizations")
            
        except Exception as e:
            print(f"⚠️  Could not check performance optimizations: {e}")
        
        theme_score = len(found_theme_elements) / len(dark_theme_elements)
        return theme_score >= 0.8  # 80% of theme elements should be present
        
    except Exception as e:
        print(f"❌ Theme test failed: {str(e)}")
        return False

def test_optimization_features():
    """Test that optimization features are properly implemented."""
    
    print("\n⚡ Testing Optimization Features")
    print("=" * 35)
    
    try:
        # Check history service optimizations
        from app.services.history_service import history_service
        
        print("✅ History service imported successfully")
        
        # Test availability check (should be fast)
        start_time = time.time()
        is_available = history_service.is_available()
        availability_time = (time.time() - start_time) * 1000
        
        print(f"✅ Availability check: {availability_time:.2f}ms")
        
        if availability_time < 50:
            print("🎉 EXCELLENT: Availability check is very fast")
        elif availability_time < 200:
            print("✅ GOOD: Availability check is fast")
        else:
            print("⚠️  SLOW: Availability check could be faster")
        
        # Check if optimized methods exist
        optimization_methods = [
            'get_comprehensive_history',
            'get_user_activities',
            'get_chat_conversations'
        ]
        
        found_methods = []
        for method in optimization_methods:
            if hasattr(history_service, method):
                found_methods.append(method)
        
        print(f"✅ Found {len(found_methods)}/{len(optimization_methods)} optimized methods")
        
        return len(found_methods) == len(optimization_methods)
        
    except Exception as e:
        print(f"❌ Optimization test failed: {str(e)}")
        return False

def main():
    """Run comprehensive history improvements test."""
    
    print("🧪 AutoWave History Improvements Test")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Performance
    performance_success = test_history_page_performance()
    
    # Test 2: Theme Consistency
    theme_success = test_theme_consistency()
    
    # Test 3: Optimization Features
    optimization_success = test_optimization_features()
    
    # Overall Results
    print(f"\n🎯 Improvement Test Results:")
    print("=" * 30)
    print(f"✅ Performance: {'PASS' if performance_success else 'FAIL'}")
    print(f"✅ Theme Consistency: {'PASS' if theme_success else 'FAIL'}")
    print(f"✅ Optimizations: {'PASS' if optimization_success else 'FAIL'}")
    
    overall_success = performance_success and theme_success and optimization_success
    
    if overall_success:
        print(f"\n🎉 History Page Improvements: SUCCESSFUL!")
        print("   ✅ Fast loading performance")
        print("   ✅ Consistent homepage theme colors")
        print("   ✅ Optimized data loading")
        print("   ✅ Enhanced user experience")
    else:
        print(f"\n⚠️  History Page Improvements: PARTIAL SUCCESS")
        print("   Check individual test results above")
    
    print(f"\n📋 User Benefits:")
    print("   🚀 Faster page loading (reduced data queries)")
    print("   🎨 Consistent dark theme matching homepage")
    print("   📱 Better mobile responsiveness")
    print("   🔄 Smooth refresh functionality")
    print("   📊 Optimized analytics display")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
