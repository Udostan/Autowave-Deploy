#!/usr/bin/env python3
"""
Simple test script for the web browser.
"""

from app.utils.web_browser import WebBrowser

# Create a web browser without advanced browser
browser = WebBrowser(cache_dir="simple_test_cache")

# Test basic browsing
result = browser.browse("https://www.example.com")

# Print the result
print(f"Success: {result.get('success', False)}")
print(f"Title: {result.get('title', 'No title')}")
print(f"Content length: {len(result.get('content', ''))}")
print(f"Number of images: {len(result.get('images', []))}")

# Clean up
if hasattr(browser, '_cleanup_advanced_browser'):
    browser._cleanup_advanced_browser()

print("Test completed successfully!")
