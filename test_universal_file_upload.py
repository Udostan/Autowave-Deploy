#!/usr/bin/env python3
"""
Test Universal File Upload Implementation
Verifies that file upload functionality has been added to all agent pages.
"""

import requests
import time

def test_file_upload_implementation():
    """Test that file upload functionality is properly implemented across all pages."""
    
    print("🧪 Testing Universal File Upload Implementation\n")
    
    base_url = "http://localhost:5001"
    
    # Test pages that should have file upload functionality
    test_pages = [
        {
            'name': 'Home Page',
            'url': f'{base_url}/',
            'upload_btn_id': 'homeFileUploadBtn',
            'file_input_id': 'homeFileInput',
            'file_preview_id': 'homeFilePreview',
            'requires_auth': True
        },
        {
            'name': 'Prime Agent Tools (Context 7)',
            'url': f'{base_url}/context7-tools',
            'upload_btn_id': 'context7FileUploadBtn',
            'file_input_id': 'context7FileInput',
            'file_preview_id': 'context7FilePreview',
            'requires_auth': False
        },
        {
            'name': 'Research Lab',
            'url': f'{base_url}/deep-research',
            'upload_btn_id': 'researchFileUploadBtn',
            'file_input_id': 'researchFileInput',
            'file_preview_id': 'researchFilePreview',
            'requires_auth': False
        },
        {
            'name': 'Agentic Code',
            'url': f'{base_url}/agentic-code',
            'upload_btn_id': 'fileUploadBtn',
            'file_input_id': 'fileInput',
            'file_preview_id': 'filePreview',
            'requires_auth': False
        },
        {
            'name': 'AutoWave Chat',
            'url': f'{base_url}/dark-chat',
            'upload_btn_id': 'chatFileUploadBtn',
            'file_input_id': 'chatFileInput',
            'file_preview_id': 'chatFilePreview',
            'requires_auth': False
        }
    ]
    
    results = []
    
    for page in test_pages:
        print(f"📄 Testing {page['name']}...")
        
        try:
            # Test if page loads
            response = requests.get(page['url'], timeout=10, allow_redirects=False)

            # Handle authentication redirects
            if response.status_code == 302 and page.get('requires_auth', False):
                print(f"   ⚠️  Page requires authentication (redirected)")
                results.append({
                    'page': page['name'],
                    'url': page['url'],
                    'page_loads': False,
                    'error': 'Authentication required'
                })
                continue
            elif response.status_code == 302:
                # Follow redirect for non-auth pages
                response = requests.get(page['url'], timeout=10)

            page_loads = response.status_code == 200

            if page_loads:
                content = response.text
                
                # Check for file upload elements
                has_upload_btn = page['upload_btn_id'] in content
                has_file_input = page['file_input_id'] in content
                has_file_preview = page['file_preview_id'] in content
                
                # Check for universal file upload script
                has_upload_script = 'universal_file_upload.js' in content
                
                # Check for file upload icon (paperclip SVG)
                has_paperclip_icon = 'M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66L9.64 16.2a2 2 0 0 1-2.83-2.83l8.49-8.49' in content
                
                # Check for file upload CSS
                has_file_css = '.file-preview' in content and '.file-item' in content
                
                result = {
                    'page': page['name'],
                    'url': page['url'],
                    'page_loads': page_loads,
                    'has_upload_btn': has_upload_btn,
                    'has_file_input': has_file_input,
                    'has_file_preview': has_file_preview,
                    'has_upload_script': has_upload_script,
                    'has_paperclip_icon': has_paperclip_icon,
                    'has_file_css': has_file_css
                }
                
                results.append(result)
                
                # Calculate score
                checks = [has_upload_btn, has_file_input, has_file_preview, has_upload_script, has_paperclip_icon, has_file_css]
                score = sum(checks)
                total = len(checks)
                
                status = "✅" if score == total else "⚠️" if score >= total - 1 else "❌"
                print(f"   {status} Score: {score}/{total}")
                print(f"      Upload Button: {'✅' if has_upload_btn else '❌'}")
                print(f"      File Input: {'✅' if has_file_input else '❌'}")
                print(f"      File Preview: {'✅' if has_file_preview else '❌'}")
                print(f"      Upload Script: {'✅' if has_upload_script else '❌'}")
                print(f"      Paperclip Icon: {'✅' if has_paperclip_icon else '❌'}")
                print(f"      File CSS: {'✅' if has_file_css else '❌'}")
                
            else:
                print(f"   ❌ Page failed to load (Status: {response.status_code})")
                results.append({
                    'page': page['name'],
                    'url': page['url'],
                    'page_loads': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"   ❌ Error testing {page['name']}: {str(e)}")
            results.append({
                'page': page['name'],
                'url': page['url'],
                'page_loads': False,
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("📊 Implementation Summary:")
    print("=" * 50)
    
    successful_pages = [r for r in results if r.get('page_loads', False)]
    total_pages = len(test_pages)
    
    print(f"Pages tested: {total_pages}")
    print(f"Pages loading: {len(successful_pages)}")
    
    if successful_pages:
        # Calculate overall implementation score
        total_score = 0
        max_score = 0
        
        for result in successful_pages:
            if all(key in result for key in ['has_upload_btn', 'has_file_input', 'has_file_preview', 'has_upload_script', 'has_paperclip_icon', 'has_file_css']):
                checks = [result['has_upload_btn'], result['has_file_input'], result['has_file_preview'], 
                         result['has_upload_script'], result['has_paperclip_icon'], result['has_file_css']]
                total_score += sum(checks)
                max_score += len(checks)
        
        if max_score > 0:
            overall_percentage = (total_score / max_score) * 100
            print(f"Overall implementation: {total_score}/{max_score} ({overall_percentage:.1f}%)")
            
            if overall_percentage >= 95:
                print("🎉 Excellent! Universal file upload is fully implemented!")
            elif overall_percentage >= 80:
                print("👍 Good! Most file upload features are implemented.")
            elif overall_percentage >= 60:
                print("⚠️  Partial implementation. Some features missing.")
            else:
                print("❌ Poor implementation. Major features missing.")
        
        # Detailed breakdown
        print("\n📋 Feature Breakdown:")
        features = ['has_upload_btn', 'has_file_input', 'has_file_preview', 'has_upload_script', 'has_paperclip_icon', 'has_file_css']
        feature_names = ['Upload Button', 'File Input', 'File Preview', 'Upload Script', 'Paperclip Icon', 'File CSS']
        
        for i, feature in enumerate(features):
            count = sum(1 for r in successful_pages if r.get(feature, False))
            percentage = (count / len(successful_pages)) * 100 if successful_pages else 0
            status = "✅" if percentage == 100 else "⚠️" if percentage >= 80 else "❌"
            print(f"   {status} {feature_names[i]}: {count}/{len(successful_pages)} pages ({percentage:.1f}%)")
    
    print("\n🔧 Next Steps:")
    if len(successful_pages) < total_pages:
        print("   • Fix pages that are not loading")
    
    missing_features = []
    if successful_pages:
        for feature, name in zip(['has_upload_btn', 'has_file_input', 'has_file_preview', 'has_upload_script', 'has_paperclip_icon', 'has_file_css'], 
                                feature_names):
            count = sum(1 for r in successful_pages if r.get(feature, False))
            if count < len(successful_pages):
                missing_features.append(name)
    
    if missing_features:
        print(f"   • Complete implementation of: {', '.join(missing_features)}")
    else:
        print("   • Test file upload functionality in browser")
        print("   • Verify file processing in backend APIs")
    
    return results

def test_file_upload_api_integration():
    """Test that APIs can handle file content properly."""
    
    print("\n🔗 Testing API Integration for File Upload\n")
    
    base_url = "http://localhost:5001"
    
    # Test data with simulated file content
    test_cases = [
        {
            'name': 'Prime Agent with File Content',
            'endpoint': f'{base_url}/api/execute-task',
            'data': {
                'task_description': 'Analyze this code\n\n--- File: test.py ---\nprint("Hello World")\n',
                'use_advanced_browser': True
            }
        },
        {
            'name': 'Context 7 Tools with File Content',
            'endpoint': f'{base_url}/api/context7/execute',
            'data': {
                'task': 'Review this document\n\n--- File: report.txt ---\nThis is a test report.\n'
            }
        },
        {
            'name': 'Research Lab with File Content',
            'endpoint': f'{base_url}/api/search',
            'data': {
                'query': 'Research this topic\n\n--- Image: chart.png (image/png) ---\n[Image uploaded - can be analyzed by AI]\n'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"🔍 Testing {test_case['name']}...")
        
        try:
            response = requests.post(
                test_case['endpoint'],
                json=test_case['data'],
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ API accepts file content (Status: {response.status_code})")
            else:
                print(f"   ⚠️  API response: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"   ⚠️  API timeout (expected for long-running tasks)")
        except Exception as e:
            print(f"   ❌ API error: {str(e)}")
    
    print("\n✅ API integration testing completed!")

if __name__ == "__main__":
    print("🚀 Universal File Upload Test Suite")
    print("=" * 50)
    
    # Test implementation
    results = test_file_upload_implementation()
    
    # Test API integration
    test_file_upload_api_integration()
    
    print("\n🎯 Testing completed!")
    print("You can now test file upload functionality in the browser by:")
    print("1. Opening any agent page")
    print("2. Clicking the paperclip icon next to input boxes")
    print("3. Uploading images, text files, or code files")
    print("4. Verifying file previews appear")
    print("5. Submitting tasks with uploaded files")
