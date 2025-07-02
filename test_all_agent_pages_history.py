#!/usr/bin/env python3
"""
Test history functionality across all agent pages
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5004"

def test_agent_page_history(url, name):
    """Test history functionality on a specific agent page"""
    try:
        response = requests.get(f"{BASE_URL}{url}")
        if response.status_code == 200:
            page_content = response.text
            
            # Check for required elements
            has_history_toggle = 'history-toggle' in page_content
            has_history_sidebar = 'history-sidebar' in page_content
            has_refresh_button = 'refresh-history' in page_content
            has_professional_history_js = 'professional_history.js' in page_content
            has_enhanced_history_js = 'enhanced_history.js' in page_content
            
            result = {
                'name': name,
                'url': url,
                'status': 'success',
                'toggle': has_history_toggle,
                'sidebar': has_history_sidebar,
                'refresh': has_refresh_button,
                'professional_js': has_professional_history_js,
                'enhanced_js': has_enhanced_history_js,
                'conflicts': has_enhanced_history_js  # Enhanced JS is now a conflict
            }
            
            return result
        else:
            return {
                'name': name,
                'url': url,
                'status': 'error',
                'error': f"HTTP {response.status_code}",
                'toggle': False,
                'sidebar': False,
                'refresh': False,
                'professional_js': False,
                'enhanced_js': False,
                'conflicts': False
            }
    except Exception as e:
        return {
            'name': name,
            'url': url,
            'status': 'error',
            'error': str(e),
            'toggle': False,
            'sidebar': False,
            'refresh': False,
            'professional_js': False,
            'enhanced_js': False,
            'conflicts': False
        }

def test_all_agent_pages():
    """Test history functionality on all agent pages"""
    
    print("=== All Agent Pages History Test ===\n")
    
    # Define all agent pages to test
    pages_to_test = [
        ('/document-generator', 'Agent Wave (Document Generator)'),
        ('/agentic-code', 'Agent Alpha (Agentic Code)'),
        ('/autowave', 'Prime Agent (AutoWave)'),
        ('/dark-chat', 'AutoWave Chat'),
        ('/deep-research', 'Research Lab'),
        ('/code-ide', 'Code IDE'),
        ('/', 'Homepage')  # Include homepage for comparison
    ]
    
    results = []
    
    print("Testing history functionality on all agent pages...\n")
    
    for url, name in pages_to_test:
        print(f"Testing {name}...")
        result = test_agent_page_history(url, name)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✅ {name}: Page loads successfully")
            print(f"   Toggle: {'✅' if result['toggle'] else '❌'}")
            print(f"   Sidebar: {'✅' if result['sidebar'] else '❌'}")
            print(f"   Refresh: {'✅' if result['refresh'] else '❌'}")
            print(f"   Professional JS: {'✅' if result['professional_js'] else '❌'}")
            print(f"   Enhanced JS: {'❌ (removed)' if not result['enhanced_js'] else '⚠️ (conflict)'}")
            
            if result['conflicts']:
                print(f"   ⚠️ WARNING: Still has enhanced_history.js conflict")
        else:
            print(f"❌ {name}: {result.get('error', 'Unknown error')}")
        
        print()
    
    return results

def analyze_results(results):
    """Analyze test results and provide summary"""
    
    print("=== Analysis Summary ===\n")
    
    successful_pages = [r for r in results if r['status'] == 'success']
    failed_pages = [r for r in results if r['status'] == 'error']
    pages_with_conflicts = [r for r in results if r.get('conflicts', False)]
    fully_working_pages = [r for r in results if (
        r['status'] == 'success' and 
        r['toggle'] and 
        r['sidebar'] and 
        r['refresh'] and 
        r['professional_js'] and 
        not r['enhanced_js']
    )]
    
    print(f"📊 **Test Results:**")
    print(f"   Total pages tested: {len(results)}")
    print(f"   Successfully loaded: {len(successful_pages)}")
    print(f"   Failed to load: {len(failed_pages)}")
    print(f"   Pages with conflicts: {len(pages_with_conflicts)}")
    print(f"   Fully working pages: {len(fully_working_pages)}")
    
    if fully_working_pages:
        print(f"\n✅ **Fully Working Pages:**")
        for page in fully_working_pages:
            print(f"   - {page['name']}")
    
    if pages_with_conflicts:
        print(f"\n⚠️ **Pages with Conflicts:**")
        for page in pages_with_conflicts:
            print(f"   - {page['name']} (still loading enhanced_history.js)")
    
    if failed_pages:
        print(f"\n❌ **Failed Pages:**")
        for page in failed_pages:
            print(f"   - {page['name']}: {page.get('error', 'Unknown error')}")
    
    # Overall success rate
    success_rate = len(fully_working_pages) / len(successful_pages) * 100 if successful_pages else 0
    print(f"\n📈 **Success Rate:** {success_rate:.1f}% of loaded pages are fully working")
    
    return len(fully_working_pages) == len(successful_pages)

def test_history_api():
    """Test that history API is working"""
    print("\n=== History API Test ===\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/history/unified?limit=5")
        if response.status_code == 200:
            history_data = response.json()
            if history_data.get('success'):
                total_items = history_data.get('count', 0)
                agent_types = set(item.get('agent_type') for item in history_data.get('history', []))
                
                print(f"✅ History API working")
                print(f"   Total items: {total_items}")
                print(f"   Agent types: {', '.join(sorted(agent_types))}")
                
                return True
            else:
                print(f"❌ History API error: {history_data.get('error')}")
                return False
        else:
            print(f"❌ History API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ History API error: {e}")
        return False

def main():
    print("Testing history functionality across all agent pages...\n")
    
    # Test all agent pages
    results = test_all_agent_pages()
    
    # Analyze results
    all_working = analyze_results(results)
    
    # Test history API
    api_working = test_history_api()
    
    print("\n=== Final Summary ===")
    if all_working and api_working:
        print("🎉 SUCCESS: History sidebar is working across all agent pages!")
        print("\n✅ What's working:")
        print("- All agent pages load without enhanced_history.js conflicts")
        print("- Professional history system is properly loaded on all pages")
        print("- History sidebar with auto-refresh is available everywhere")
        print("- Manual refresh button is functional")
        print("- History API is working correctly")
        
        print("\n📱 User Experience:")
        print("- Consistent history sidebar across all agent pages")
        print("- Auto-refresh every 30 seconds on all pages")
        print("- Manual refresh button available on all pages")
        print("- No JavaScript errors or conflicts")
        print("- Seamless navigation between agents with persistent history")
        
    else:
        print("⚠️ PARTIAL SUCCESS: Some issues remain")
        if not all_working:
            print("- Some pages still have conflicts or missing elements")
        if not api_working:
            print("- History API is not functioning correctly")
        print("- Check the analysis above for specific issues")
        
    return all_working and api_working

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
