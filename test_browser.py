#!/usr/bin/env python3
"""
Test script for the enhanced web browser functionality.
"""

import os
import sys
import time
import traceback
from app.utils.web_browser import WebBrowser

def test_browser():
    """Test the enhanced web browser functionality."""
    # Redirect output to a file
    with open('test_browser_output.txt', 'w') as f:
        try:
            f.write("Testing enhanced web browser functionality...\n")

            # Create a web browser with advanced browser enabled
            browser = WebBrowser(
                cache_dir="test_cache",
                cache_expiry=3600,
                use_advanced_browser=True,
                max_cache_size=100,
                browser_type='auto'
            )

            # Test basic browsing
            f.write("\n1. Testing basic browsing...\n")
            result = browser.browse("https://www.example.com")
            f.write(f"Success: {result.get('success', False)}\n")
            f.write(f"Title: {result.get('title', 'No title')}\n")
            f.write(f"Content length: {len(result.get('content', ''))}\n")
            f.write(f"Screenshot available: {'Yes' if result.get('screenshot') else 'No'}\n")
            f.write(f"Number of images: {len(result.get('images', []))}\n")

            # Test parallel browsing
            f.write("\n2. Testing parallel browsing...\n")
            urls = [
                "https://www.example.com",
                "https://www.python.org",
                "https://www.wikipedia.org"
            ]
            results = browser.browse_multiple(urls, max_workers=3)
            f.write(f"Number of results: {len(results)}\n")
            for i, result in enumerate(results):
                f.write(f"Result {i+1}:\n")
                f.write(f"  URL: {result.get('url', 'Unknown')}\n")
                f.write(f"  Success: {result.get('success', False)}\n")
                f.write(f"  Title: {result.get('title', 'No title')}\n")
                f.write(f"  Screenshot available: {'Yes' if result.get('screenshot') else 'No'}\n")
                f.write(f"  Number of images: {len(result.get('images', []))}\n")

            # Test search functionality
            f.write("\n3. Testing search functionality...\n")
            search_results = browser.search("Python programming language", num_results=3)
            f.write(f"Number of search results: {len(search_results)}\n")
            for i, result in enumerate(search_results):
                f.write(f"Search Result {i+1}:\n")
                f.write(f"  URL: {result.get('url', 'Unknown')}\n")
                f.write(f"  Success: {result.get('success', False)}\n")
                f.write(f"  Title: {result.get('title', 'No title')}\n")
                f.write(f"  Screenshot available: {'Yes' if result.get('screenshot') else 'No'}\n")
                f.write(f"  Number of images: {len(result.get('images', []))}\n")

            # Test cache statistics
            f.write("\n4. Testing cache statistics...\n")
            cache_stats = browser.get_cache_stats()
            f.write(f"Memory cache size: {cache_stats.get('memory_cache_size', 0)}\n")
            f.write(f"Disk cache size: {cache_stats.get('disk_cache_size', 0)}\n")
            f.write(f"Cache hits: {cache_stats.get('cache_hits', 0)}\n")
            f.write(f"Cache misses: {cache_stats.get('cache_misses', 0)}\n")
            f.write(f"Hit rate: {cache_stats.get('hit_rate', '0%')}\n")

            # Clean up
            browser._cleanup_advanced_browser()
            f.write("\nTest completed successfully!\n")
        except Exception as e:
            f.write(f"\nError: {str(e)}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    test_browser()
    print("Test completed. Check test_browser_output.txt for results.")
