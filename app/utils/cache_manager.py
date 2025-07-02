"""
Cache manager for the Super Agent.
This module provides caching functionality for booking search results.
"""

import os
import json
import time
import hashlib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    """A cache manager for booking search results."""

    def __init__(self, cache_dir=None, cache_expiry=3600):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir (str, optional): Directory to store cache files. Defaults to 'cache' in current directory.
            cache_expiry (int, optional): Cache expiry time in seconds. Defaults to 3600 (1 hour).
        """
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), 'cache')
        self.cache_expiry = cache_expiry
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")
    
    def get_cache_key(self, data):
        """
        Generate a cache key for the given data.
        
        Args:
            data (dict): The data to generate a key for
            
        Returns:
            str: The cache key
        """
        # Create a string representation of the data
        data_str = json.dumps(data, sort_keys=True)
        
        # Generate a hash of the data
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def get_cached_data(self, key):
        """
        Get cached data for the given key.
        
        Args:
            key (str): The cache key
            
        Returns:
            dict: The cached data, or None if not found or expired
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        # Check if cache file exists and is not expired
        if os.path.exists(cache_file):
            try:
                # Get file modification time
                mod_time = os.path.getmtime(cache_file)
                current_time = time.time()
                
                # Check if cache is expired
                if current_time - mod_time <= self.cache_expiry:
                    # Cache is still valid, load it
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    logger.info(f"Using cached data for key: {key}")
                    return cache_data
                else:
                    logger.info(f"Cache expired for key: {key}")
            except Exception as e:
                logger.warning(f"Error reading cache: {str(e)}")
        
        return None
    
    def cache_data(self, key, data):
        """
        Cache data for the given key.
        
        Args:
            key (str): The cache key
            data (dict): The data to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            # Create cache data with timestamp
            cache_data = {
                'data': data,
                'timestamp': time.time()
            }
            
            # Write cache data to file
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
            
            logger.info(f"Cached data for key: {key}")
        except Exception as e:
            logger.warning(f"Error writing cache: {str(e)}")
    
    def clear_cache(self, key=None):
        """
        Clear cache for the given key or all cache if no key is provided.
        
        Args:
            key (str, optional): The cache key to clear. Defaults to None.
        """
        if key:
            # Clear specific cache
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logger.info(f"Cleared cache for key: {key}")
                except Exception as e:
                    logger.warning(f"Error clearing cache for key {key}: {str(e)}")
        else:
            # Clear all cache
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.cache_dir, filename))
                logger.info("Cleared all cache")
            except Exception as e:
                logger.warning(f"Error clearing all cache: {str(e)}")
