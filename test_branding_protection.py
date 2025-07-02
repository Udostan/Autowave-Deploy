#!/usr/bin/env python3
"""
Test script to verify that Context 7 branding is properly hidden from competitors.
"""

import os
from datetime import datetime

def test_context7_branding_hidden():
    """Test that Context 7 branding is hidden in the history page."""
    
    print("🔒 Testing Context 7 Branding Protection")
    print("=" * 40)
    
    try:
        # Read the history template
        with open('app/templates/history.html', 'r') as f:
            template_content = f.read()
        
        print("✅ History template loaded")
        
        # Check for Context 7 branding that should be hidden
        context7_branding = [
            'Context7 Tools',
            'Context 7 Tools',
            'context7 tools',
            'Context7',
            'Context 7'
        ]
        
        found_branding = []
        for brand in context7_branding:
            if brand in template_content:
                found_branding.append(brand)
        
        # Check for proper replacement with Prime Agent Tools
        prime_agent_branding = [
            'Prime Agent Tools',
            'Use Prime Agent Tools',
            'No Prime Agent Tools usage found'
        ]
        
        found_prime_branding = []
        for brand in prime_agent_branding:
            if brand in template_content:
                found_prime_branding.append(brand)
        
        print(f"🔍 Context 7 branding found: {len(found_branding)}")
        if found_branding:
            print(f"   ⚠️  Found: {found_branding}")
        else:
            print("   ✅ No Context 7 branding found (GOOD)")
        
        print(f"🎯 Prime Agent Tools branding found: {len(found_prime_branding)}")
        if found_prime_branding:
            print(f"   ✅ Found: {found_prime_branding}")
        else:
            print("   ❌ No Prime Agent Tools branding found")
        
        # Check tab structure
        tab_section_found = False
        if 'data-tab="context7">Prime Agent Tools</button>' in template_content:
            print("✅ Tab properly renamed to 'Prime Agent Tools'")
            tab_section_found = True
        else:
            print("❌ Tab not properly renamed")
        
        # Check activity display logic
        activity_logic_found = False
        if "{% if activity.agent_type == 'context7_tools' %}Prime Agent Tools" in template_content:
            print("✅ Activity display logic properly updated")
            activity_logic_found = True
        else:
            print("❌ Activity display logic not updated")
        
        # Overall branding protection score
        protection_score = 0
        if len(found_branding) == 0:  # No Context 7 branding visible
            protection_score += 40
        if len(found_prime_branding) >= 2:  # Prime Agent Tools branding present
            protection_score += 30
        if tab_section_found:  # Tab properly renamed
            protection_score += 15
        if activity_logic_found:  # Activity logic updated
            protection_score += 15
        
        print(f"\n🛡️  Branding Protection Score: {protection_score}/100")
        
        if protection_score >= 90:
            print("🎉 EXCELLENT: Context 7 branding is well hidden")
        elif protection_score >= 70:
            print("✅ GOOD: Context 7 branding is mostly hidden")
        elif protection_score >= 50:
            print("⚠️  FAIR: Some Context 7 branding may be visible")
        else:
            print("❌ POOR: Context 7 branding is still visible")
        
        return protection_score >= 70
        
    except Exception as e:
        print(f"❌ Branding protection test failed: {str(e)}")
        return False

def test_competitor_protection():
    """Test overall competitor protection measures."""
    
    print("\n🔐 Testing Competitor Protection")
    print("=" * 35)
    
    try:
        # Check multiple files for Context 7 references
        files_to_check = [
            'app/templates/history.html',
            'app/templates/context7_tools.html',
            'app/templates/index.html'
        ]
        
        total_files_checked = 0
        files_with_protection = 0
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                total_files_checked += 1
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check if file has protection measures
                protection_measures = [
                    'Prime Agent Tools',
                    'Prime Agent',
                    'AutoWave'
                ]
                
                found_protection = False
                for measure in protection_measures:
                    if measure in content:
                        found_protection = True
                        break
                
                if found_protection:
                    files_with_protection += 1
                    print(f"✅ {file_path}: Protected")
                else:
                    print(f"⚠️  {file_path}: May need protection")
        
        protection_ratio = files_with_protection / total_files_checked if total_files_checked > 0 else 0
        
        print(f"\n📊 Protection Coverage: {files_with_protection}/{total_files_checked} files ({protection_ratio*100:.1f}%)")
        
        return protection_ratio >= 0.8  # 80% of files should have protection
        
    except Exception as e:
        print(f"❌ Competitor protection test failed: {str(e)}")
        return False

def main():
    """Run comprehensive branding protection tests."""
    
    print("🛡️  AutoWave Branding Protection Test")
    print("=" * 40)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Context 7 Branding Hidden
    branding_success = test_context7_branding_hidden()
    
    # Test 2: Competitor Protection
    protection_success = test_competitor_protection()
    
    # Overall Results
    print(f"\n🎯 Branding Protection Results:")
    print("=" * 35)
    print(f"✅ Context 7 Hidden: {'PASS' if branding_success else 'FAIL'}")
    print(f"✅ Competitor Protection: {'PASS' if protection_success else 'FAIL'}")
    
    overall_success = branding_success and protection_success
    
    if overall_success:
        print(f"\n🎉 Branding Protection: SUCCESSFUL!")
        print("   ✅ Context 7 branding is hidden from competitors")
        print("   ✅ Prime Agent Tools branding is prominent")
        print("   ✅ AutoWave brand identity is protected")
        print("   ✅ Competitive advantage maintained")
    else:
        print(f"\n⚠️  Branding Protection: NEEDS IMPROVEMENT")
        print("   Check individual test results above")
    
    print(f"\n🎯 Competitive Benefits:")
    print("   🔒 Context 7 technology hidden from competitors")
    print("   🏷️  Prime Agent Tools as proprietary branding")
    print("   🛡️  AutoWave brand identity protected")
    print("   💼 Competitive advantage maintained")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
