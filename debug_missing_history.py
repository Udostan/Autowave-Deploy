#!/usr/bin/env python3
"""
Debug why history elements are missing on some pages
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:5001"

def debug_page_history(url, name):
    """Debug history elements on a specific page"""
    try:
        response = requests.get(f"{BASE_URL}{url}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for history elements
            history_toggle = soup.find(id='history-toggle')
            history_sidebar = soup.find(id='history-sidebar')
            refresh_button = soup.find(id='refresh-history')
            
            # Check for scripts
            professional_history_script = any('professional_history.js' in str(script) for script in soup.find_all('script'))
            enhanced_history_script = any('enhanced_history.js' in str(script) for script in soup.find_all('script'))
            
            # Check if page extends layout
            extends_layout = '{% extends "layout.html" %}' in response.text
            
            print(f"\n=== {name} ({url}) ===")
            print(f"Extends layout.html: {'✅' if extends_layout else '❌'}")
            print(f"History toggle element: {'✅' if history_toggle else '❌'}")
            print(f"History sidebar element: {'✅' if history_sidebar else '❌'}")
            print(f"Refresh button element: {'✅' if refresh_button else '❌'}")
            print(f"Professional history JS: {'✅' if professional_history_script else '❌'}")
            print(f"Enhanced history JS: {'⚠️' if enhanced_history_script else '✅ (removed)'}")
            
            if history_toggle:
                # Check if toggle is hidden by CSS
                style = history_toggle.get('style', '')
                classes = history_toggle.get('class', [])
                print(f"Toggle style: {style}")
                print(f"Toggle classes: {classes}")
            else:
                print("❌ History toggle not found in HTML")
                
            if history_sidebar:
                print("✅ History sidebar found in HTML")
            else:
                print("❌ History sidebar not found in HTML")
                
            # Check for layout structure
            main_content = soup.find(id='main-content')
            sidebar = soup.find('aside') or soup.find(class_='sidebar')
            
            print(f"Main content element: {'✅' if main_content else '❌'}")
            print(f"Sidebar element: {'✅' if sidebar else '❌'}")
            
            return {
                'extends_layout': extends_layout,
                'has_toggle': bool(history_toggle),
                'has_sidebar': bool(history_sidebar),
                'has_refresh': bool(refresh_button),
                'has_professional_js': professional_history_script,
                'has_enhanced_js': enhanced_history_script
            }
            
        else:
            print(f"\n❌ {name}: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n❌ {name}: Error - {e}")
        return None

def main():
    print("Debugging missing history elements...\n")
    
    # Test pages that should have history but are reported as missing
    problem_pages = [
        ('/', 'Homepage'),
        ('/autowave', 'Prime Agent'),
        ('/dark-chat', 'AutoWave Chat')
    ]
    
    # Test working pages for comparison
    working_pages = [
        ('/document-generator', 'Agent Wave'),
        ('/agentic-code', 'Agent Alpha'),
        ('/deep-research', 'Research Lab')
    ]
    
    print("🔍 PROBLEM PAGES (missing history elements):")
    problem_results = []
    for url, name in problem_pages:
        result = debug_page_history(url, name)
        if result:
            problem_results.append((name, result))
    
    print("\n\n✅ WORKING PAGES (for comparison):")
    working_results = []
    for url, name in working_pages:
        result = debug_page_history(url, name)
        if result:
            working_results.append((name, result))
    
    print("\n\n=== ANALYSIS ===")
    
    # Analyze patterns
    problem_extends = [r[1]['extends_layout'] for r in problem_results]
    working_extends = [r[1]['extends_layout'] for r in working_results]
    
    print(f"\nLayout Extension Pattern:")
    print(f"Problem pages extending layout: {sum(problem_extends)}/{len(problem_extends)}")
    print(f"Working pages extending layout: {sum(working_extends)}/{len(working_extends)}")
    
    # Check for pages that extend layout but don't have history elements
    layout_but_no_history = []
    for name, result in problem_results:
        if result['extends_layout'] and not result['has_toggle']:
            layout_but_no_history.append(name)
    
    if layout_but_no_history:
        print(f"\n⚠️ Pages that extend layout.html but missing history elements:")
        for page in layout_but_no_history:
            print(f"   - {page}")
        print("\nThis suggests a template rendering issue or CSS hiding the elements.")
    
    # Check for standalone pages
    standalone_pages = []
    for name, result in problem_results:
        if not result['extends_layout']:
            standalone_pages.append(name)
    
    if standalone_pages:
        print(f"\n📄 Standalone pages (don't extend layout.html):")
        for page in standalone_pages:
            print(f"   - {page}")
        print("\nThese pages need history sidebar added manually.")
    
    print(f"\n📊 Summary:")
    print(f"   Total problem pages: {len(problem_results)}")
    print(f"   Pages extending layout but missing history: {len(layout_but_no_history)}")
    print(f"   Standalone pages: {len(standalone_pages)}")
    
    if layout_but_no_history:
        print(f"\n🔧 Recommended fixes:")
        print(f"   1. Check if layout.html is being rendered correctly")
        print(f"   2. Check for CSS that might be hiding history elements")
        print(f"   3. Verify professional_history.js is loading properly")
        print(f"   4. Check browser console for JavaScript errors")
    
    if standalone_pages:
        print(f"\n🔧 For standalone pages:")
        print(f"   1. Add history sidebar HTML manually")
        print(f"   2. Include professional_history.js")
        print(f"   3. Or convert to extend layout.html")

if __name__ == "__main__":
    main()
