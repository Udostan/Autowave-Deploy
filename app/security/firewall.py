"""
Enterprise Security Firewall
Advanced threat protection, IP filtering, and request monitoring.
"""

import re
import time
import ipaddress
from collections import defaultdict, deque
from flask import request, jsonify, abort
from functools import wraps
import logging
import os

logger = logging.getLogger(__name__)

class SecurityFirewall:
    """Enterprise-grade security firewall with threat detection."""
    
    def __init__(self):
        self.blocked_ips = set()
        self.allowed_ips = self._load_allowed_ips()
        self.suspicious_patterns = self._load_threat_patterns()
        self.request_history = defaultdict(lambda: deque(maxlen=100))
        self.threat_scores = defaultdict(int)
        
        # Configuration
        self.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', 60))
        self.max_requests_per_hour = int(os.getenv('MAX_REQUESTS_PER_HOUR', 1000))
        self.threat_threshold = int(os.getenv('THREAT_THRESHOLD', 50))
        self.auto_block_enabled = os.getenv('AUTO_BLOCK_ENABLED', 'true').lower() == 'true'
        
    def _load_allowed_ips(self):
        """Load allowed IP addresses and ranges."""
        allowed_ips = set()
        
        # Load from environment
        allowed_list = os.getenv('ALLOWED_IPS', '').split(',')
        for ip_str in allowed_list:
            ip_str = ip_str.strip()
            if ip_str:
                try:
                    # Support both single IPs and CIDR ranges
                    allowed_ips.add(ipaddress.ip_network(ip_str, strict=False))
                except ValueError:
                    logger.warning(f"Invalid IP address format: {ip_str}")
        
        # Default: allow localhost and private networks
        if not allowed_ips:
            allowed_ips.update([
                ipaddress.ip_network('127.0.0.0/8'),    # Localhost
                ipaddress.ip_network('10.0.0.0/8'),     # Private Class A
                ipaddress.ip_network('172.16.0.0/12'),  # Private Class B
                ipaddress.ip_network('192.168.0.0/16'), # Private Class C
            ])
        
        return allowed_ips
    
    def _load_threat_patterns(self):
        """Load patterns that indicate potential threats."""
        return [
            # SQL Injection patterns
            re.compile(r'(\bunion\b|\bselect\b|\binsert\b|\bdelete\b|\bdrop\b|\bupdate\b)', re.IGNORECASE),
            re.compile(r'(\bor\b|\band\b)\s+\d+\s*=\s*\d+', re.IGNORECASE),
            re.compile(r'[\'";]\s*(\bor\b|\band\b)', re.IGNORECASE),
            
            # XSS patterns
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),
            
            # Path traversal
            re.compile(r'\.\.[\\/]'),
            re.compile(r'[\\/]etc[\\/]passwd'),
            re.compile(r'[\\/]proc[\\/]'),
            
            # Command injection
            re.compile(r'[;&|`$]'),
            re.compile(r'\b(cat|ls|pwd|whoami|id|uname)\b'),
            
            # Common attack tools
            re.compile(r'(sqlmap|nmap|nikto|dirb|gobuster)', re.IGNORECASE),
        ]
    
    def is_ip_allowed(self, ip_address):
        """Check if IP address is in allowed list."""
        if not self.allowed_ips:
            return True  # No restrictions if no allowed IPs configured
        
        try:
            ip = ipaddress.ip_address(ip_address)
            return any(ip in network for network in self.allowed_ips)
        except ValueError:
            return False
    
    def is_ip_blocked(self, ip_address):
        """Check if IP address is blocked."""
        return ip_address in self.blocked_ips
    
    def block_ip(self, ip_address, reason="Security violation"):
        """Block an IP address."""
        self.blocked_ips.add(ip_address)
        logger.warning(f"Blocked IP {ip_address}: {reason}")
    
    def unblock_ip(self, ip_address):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip_address)
        logger.info(f"Unblocked IP {ip_address}")
    
    def analyze_request_content(self, content):
        """Analyze request content for threats."""
        threat_score = 0
        detected_threats = []
        
        if not content:
            return threat_score, detected_threats
        
        content_str = str(content).lower()
        
        for i, pattern in enumerate(self.suspicious_patterns):
            if pattern.search(content_str):
                threat_score += 10
                threat_types = [
                    'SQL Injection', 'SQL Injection', 'SQL Injection',
                    'XSS Attack', 'XSS Attack', 'XSS Attack',
                    'Path Traversal', 'Path Traversal', 'Path Traversal',
                    'Command Injection', 'Command Injection',
                    'Attack Tool'
                ]
                detected_threats.append(threat_types[min(i, len(threat_types) - 1)])
        
        return threat_score, detected_threats
    
    def check_rate_limits(self, ip_address):
        """Check if IP address exceeds rate limits."""
        current_time = time.time()
        
        # Clean old requests
        self.request_history[ip_address] = deque(
            [req_time for req_time in self.request_history[ip_address] 
             if current_time - req_time < 3600],  # Keep last hour
            maxlen=100
        )
        
        # Add current request
        self.request_history[ip_address].append(current_time)
        
        # Check limits
        recent_requests = [req_time for req_time in self.request_history[ip_address] 
                          if current_time - req_time < 60]  # Last minute
        
        if len(recent_requests) > self.max_requests_per_minute:
            return False, f"Rate limit exceeded: {len(recent_requests)} requests per minute"
        
        if len(self.request_history[ip_address]) > self.max_requests_per_hour:
            return False, f"Rate limit exceeded: {len(self.request_history[ip_address])} requests per hour"
        
        return True, None
    
    def process_request(self, request_obj):
        """Process incoming request through firewall."""
        client_ip = request_obj.environ.get('HTTP_X_FORWARDED_FOR', request_obj.remote_addr)
        
        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            return False, "IP address is blocked"
        
        # Check if IP is allowed (if whitelist is configured)
        if not self.is_ip_allowed(client_ip):
            return False, "IP address not in allowed list"
        
        # Check rate limits
        rate_ok, rate_msg = self.check_rate_limits(client_ip)
        if not rate_ok:
            if self.auto_block_enabled:
                self.block_ip(client_ip, rate_msg)
            return False, rate_msg
        
        # Analyze request content for threats
        content_to_analyze = []
        
        # Check URL parameters
        if request_obj.args:
            content_to_analyze.extend(request_obj.args.values())
        
        # Check form data
        if request_obj.form:
            content_to_analyze.extend(request_obj.form.values())
        
        # Check JSON data
        if request_obj.is_json:
            try:
                json_data = request_obj.get_json()
                if json_data:
                    content_to_analyze.append(str(json_data))
            except:
                pass
        
        # Check headers for suspicious content
        suspicious_headers = ['user-agent', 'referer', 'x-forwarded-for']
        for header in suspicious_headers:
            value = request_obj.headers.get(header)
            if value:
                content_to_analyze.append(value)
        
        # Analyze all content
        total_threat_score = 0
        all_threats = []
        
        for content in content_to_analyze:
            score, threats = self.analyze_request_content(content)
            total_threat_score += score
            all_threats.extend(threats)
        
        # Update threat score for IP
        self.threat_scores[client_ip] += total_threat_score
        
        # Check if threat threshold exceeded
        if total_threat_score > self.threat_threshold:
            threat_msg = f"High threat score: {total_threat_score}, Threats: {', '.join(set(all_threats))}"
            if self.auto_block_enabled:
                self.block_ip(client_ip, threat_msg)
            return False, threat_msg
        
        return True, None

# Firewall decorator
def firewall_protection():
    """Decorator to apply firewall protection to endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            firewall = SecurityFirewall()
            
            # Process request through firewall
            allowed, reason = firewall.process_request(request)
            
            if not allowed:
                logger.warning(f"Firewall blocked request from {request.remote_addr}: {reason}")
                return jsonify({
                    'error': 'Request blocked by security firewall',
                    'reason': 'Security policy violation'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Global firewall instance
security_firewall = SecurityFirewall()
