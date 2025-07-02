"""
Advanced Rate Limiter
Sophisticated rate limiting with multiple algorithms and adaptive thresholds.
"""

import time
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify
import os
import logging

# Optional Redis import
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)

class RateLimiter:
    """Advanced rate limiter with multiple algorithms."""
    
    def __init__(self):
        self.use_redis = os.getenv('USE_REDIS_RATE_LIMIT', 'false').lower() == 'true' and REDIS_AVAILABLE
        self.redis_client = None

        if self.use_redis and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("Connected to Redis for rate limiting")
            except:
                logger.warning("Redis not available, using in-memory rate limiting")
                self.use_redis = False
        elif not REDIS_AVAILABLE:
            logger.info("Redis module not installed, using in-memory rate limiting")
        
        # In-memory storage for non-Redis mode
        self.request_counts = defaultdict(lambda: defaultdict(int))
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        self.sliding_windows = defaultdict(lambda: defaultdict(list))
        
        # Rate limit configurations
        self.limits = {
            'per_second': int(os.getenv('RATE_LIMIT_PER_SECOND', 10)),
            'per_minute': int(os.getenv('RATE_LIMIT_PER_MINUTE', 60)),
            'per_hour': int(os.getenv('RATE_LIMIT_PER_HOUR', 1000)),
            'per_day': int(os.getenv('RATE_LIMIT_PER_DAY', 10000))
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/prime-agent/execute-task': {'per_minute': 20, 'per_hour': 200},
            '/api/agentic-code/generate': {'per_minute': 15, 'per_hour': 150},
            '/api/context7-tools/execute-task': {'per_minute': 30, 'per_hour': 300},
            '/api/memory/test': {'per_minute': 5, 'per_hour': 50}
        }
    
    def _get_client_id(self, request_obj):
        """Get unique client identifier."""
        # Try to get user ID from auth data
        if hasattr(request_obj, 'auth_data') and request_obj.auth_data:
            if 'user_id' in request_obj.auth_data:
                return f"user:{request_obj.auth_data['user_id']}"
            elif 'name' in request_obj.auth_data:
                return f"api:{request_obj.auth_data['name']}"
        
        # Fall back to IP address
        return f"ip:{request_obj.environ.get('HTTP_X_FORWARDED_FOR', request_obj.remote_addr)}"
    
    def _get_time_windows(self):
        """Get current time windows for different periods."""
        now = time.time()
        return {
            'second': int(now),
            'minute': int(now // 60),
            'hour': int(now // 3600),
            'day': int(now // 86400)
        }
    
    def _check_redis_limit(self, client_id, endpoint, limits):
        """Check rate limits using Redis."""
        if not self.redis_client:
            return True, None
        
        pipe = self.redis_client.pipeline()
        now = time.time()
        
        for period, limit in limits.items():
            if period == 'per_second':
                window = int(now)
                ttl = 1
            elif period == 'per_minute':
                window = int(now // 60)
                ttl = 60
            elif period == 'per_hour':
                window = int(now // 3600)
                ttl = 3600
            elif period == 'per_day':
                window = int(now // 86400)
                ttl = 86400
            else:
                continue
            
            key = f"rate_limit:{client_id}:{endpoint}:{period}:{window}"
            pipe.incr(key)
            pipe.expire(key, ttl)
        
        results = pipe.execute()
        
        # Check if any limit is exceeded
        i = 0
        for period, limit in limits.items():
            if period.startswith('per_'):
                count = results[i]
                if count > limit:
                    return False, f"Rate limit exceeded: {count}/{limit} {period}"
                i += 2  # Skip expire result
        
        return True, None
    
    def _check_memory_limit(self, client_id, endpoint, limits):
        """Check rate limits using in-memory storage."""
        windows = self._get_time_windows()
        
        for period, limit in limits.items():
            if period == 'per_second':
                window_key = f"{client_id}:{endpoint}:second:{windows['second']}"
            elif period == 'per_minute':
                window_key = f"{client_id}:{endpoint}:minute:{windows['minute']}"
            elif period == 'per_hour':
                window_key = f"{client_id}:{endpoint}:hour:{windows['hour']}"
            elif period == 'per_day':
                window_key = f"{client_id}:{endpoint}:day:{windows['day']}"
            else:
                continue
            
            # Increment counter
            self.request_counts[window_key] += 1
            count = self.request_counts[window_key]
            
            if count > limit:
                return False, f"Rate limit exceeded: {count}/{limit} {period}"
        
        # Clean old entries periodically
        if len(self.request_counts) > 10000:
            self._cleanup_memory()
        
        return True, None
    
    def _cleanup_memory(self):
        """Clean up old rate limit entries from memory."""
        current_time = time.time()
        windows = self._get_time_windows()
        
        keys_to_remove = []
        for key in self.request_counts:
            try:
                parts = key.split(':')
                if len(parts) >= 4:
                    period = parts[2]
                    window = int(parts[3])
                    
                    # Remove old windows
                    if period == 'second' and window < windows['second'] - 60:
                        keys_to_remove.append(key)
                    elif period == 'minute' and window < windows['minute'] - 60:
                        keys_to_remove.append(key)
                    elif period == 'hour' and window < windows['hour'] - 24:
                        keys_to_remove.append(key)
                    elif period == 'day' and window < windows['day'] - 7:
                        keys_to_remove.append(key)
            except:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]
    
    def check_rate_limit(self, request_obj, endpoint=None):
        """Check if request is within rate limits."""
        client_id = self._get_client_id(request_obj)
        endpoint = endpoint or request_obj.endpoint or request_obj.path
        
        # Get applicable limits
        limits = self.limits.copy()
        if endpoint in self.endpoint_limits:
            limits.update(self.endpoint_limits[endpoint])
        
        # Check limits
        if self.use_redis:
            return self._check_redis_limit(client_id, endpoint, limits)
        else:
            return self._check_memory_limit(client_id, endpoint, limits)
    
    def get_rate_limit_info(self, request_obj, endpoint=None):
        """Get current rate limit status for client."""
        client_id = self._get_client_id(request_obj)
        endpoint = endpoint or request_obj.endpoint or request_obj.path
        
        limits = self.limits.copy()
        if endpoint in self.endpoint_limits:
            limits.update(self.endpoint_limits[endpoint])
        
        info = {
            'client_id': client_id,
            'endpoint': endpoint,
            'limits': limits,
            'current_usage': {}
        }
        
        if self.use_redis and self.redis_client:
            windows = self._get_time_windows()
            for period, limit in limits.items():
                if period == 'per_second':
                    key = f"rate_limit:{client_id}:{endpoint}:{period}:{windows['second']}"
                elif period == 'per_minute':
                    key = f"rate_limit:{client_id}:{endpoint}:{period}:{windows['minute']}"
                elif period == 'per_hour':
                    key = f"rate_limit:{client_id}:{endpoint}:{period}:{windows['hour']}"
                elif period == 'per_day':
                    key = f"rate_limit:{client_id}:{endpoint}:{period}:{windows['day']}"
                else:
                    continue
                
                current = self.redis_client.get(key) or 0
                info['current_usage'][period] = int(current)
        else:
            windows = self._get_time_windows()
            for period, limit in limits.items():
                if period == 'per_second':
                    key = f"{client_id}:{endpoint}:second:{windows['second']}"
                elif period == 'per_minute':
                    key = f"{client_id}:{endpoint}:minute:{windows['minute']}"
                elif period == 'per_hour':
                    key = f"{client_id}:{endpoint}:hour:{windows['hour']}"
                elif period == 'per_day':
                    key = f"{client_id}:{endpoint}:day:{windows['day']}"
                else:
                    continue
                
                current = self.request_counts.get(key, 0)
                info['current_usage'][period] = current
        
        return info

# Rate limiting decorator
def rate_limit(per_second=None, per_minute=None, per_hour=None, per_day=None):
    """Decorator to apply rate limiting to endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rate_limiter = RateLimiter()
            
            # Override default limits if specified
            custom_limits = {}
            if per_second is not None:
                custom_limits['per_second'] = per_second
            if per_minute is not None:
                custom_limits['per_minute'] = per_minute
            if per_hour is not None:
                custom_limits['per_hour'] = per_hour
            if per_day is not None:
                custom_limits['per_day'] = per_day
            
            # Temporarily override limits
            original_limits = rate_limiter.limits.copy()
            rate_limiter.limits.update(custom_limits)
            
            try:
                # Check rate limit
                allowed, reason = rate_limiter.check_rate_limit(request)
                
                if not allowed:
                    # Get rate limit info for headers
                    info = rate_limiter.get_rate_limit_info(request)
                    
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': reason,
                        'retry_after': 60  # Suggest retry after 1 minute
                    })
                    
                    # Add rate limit headers
                    for period, limit in info['limits'].items():
                        current = info['current_usage'].get(period, 0)
                        response.headers[f'X-RateLimit-{period.replace("per_", "").title()}'] = str(limit)
                        response.headers[f'X-RateLimit-{period.replace("per_", "").title()}-Remaining'] = str(max(0, limit - current))
                    
                    response.status_code = 429
                    return response
                
                # Add rate limit info to successful responses
                result = f(*args, **kwargs)
                if hasattr(result, 'headers'):
                    info = rate_limiter.get_rate_limit_info(request)
                    for period, limit in info['limits'].items():
                        current = info['current_usage'].get(period, 0)
                        result.headers[f'X-RateLimit-{period.replace("per_", "").title()}'] = str(limit)
                        result.headers[f'X-RateLimit-{period.replace("per_", "").title()}-Remaining'] = str(max(0, limit - current))
                
                return result
                
            finally:
                # Restore original limits
                rate_limiter.limits = original_limits
        
        return decorated_function
    return decorator

# Global rate limiter instance
rate_limiter = RateLimiter()
