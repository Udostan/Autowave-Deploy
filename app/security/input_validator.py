"""
Input Validator
Advanced input validation and sanitization for security.
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional

class InputValidator:
    """Advanced input validation and sanitization."""
    
    def __init__(self):
        # Common attack patterns
        self.sql_patterns = [
            re.compile(r'(\bunion\b|\bselect\b|\binsert\b|\bdelete\b|\bdrop\b|\bupdate\b)', re.IGNORECASE),
            re.compile(r'(\bor\b|\band\b)\s+\d+\s*=\s*\d+', re.IGNORECASE),
            re.compile(r'[\'";]\s*(\bor\b|\band\b)', re.IGNORECASE),
        ]
        
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),
            re.compile(r'<iframe[^>]*>', re.IGNORECASE),
            re.compile(r'<object[^>]*>', re.IGNORECASE),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
        ]
        
        self.path_traversal_patterns = [
            re.compile(r'\.\.[\\/]'),
            re.compile(r'[\\/]etc[\\/]passwd'),
            re.compile(r'[\\/]proc[\\/]'),
            re.compile(r'[\\/]windows[\\/]system32'),
        ]
        
        self.command_injection_patterns = [
            re.compile(r'[;&|`$]'),
            re.compile(r'\b(cat|ls|pwd|whoami|id|uname|rm|del|format)\b'),
            re.compile(r'(\|\||&&)'),
        ]
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 254:
            return False
        
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(email))
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength."""
        if not password:
            return {'valid': False, 'errors': ['Password is required']}
        
        errors = []
        
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        if len(password) > 128:
            errors.append('Password must be less than 128 characters')
        
        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'qwerty', 'abc123', 'password123']
        if password.lower() in weak_passwords:
            errors.append('Password is too common')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> str:
        """Calculate password strength."""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[0-9]', password):
            score += 1
        if re.search(r'[^a-zA-Z0-9]', password):
            score += 1
        
        if score <= 2:
            return 'weak'
        elif score <= 3:
            return 'medium'
        else:
            return 'strong'
    
    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize input data."""
        if isinstance(input_data, str):
            return self._sanitize_string(input_data)
        elif isinstance(input_data, dict):
            return {key: self.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string input."""
        if not text:
            return text
        
        # HTML encode
        text = html.escape(text)
        
        # URL decode to prevent double encoding attacks
        text = urllib.parse.unquote(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        if len(text) > 10000:
            text = text[:10000]
        
        return text
    
    def detect_sql_injection(self, text: str) -> bool:
        """Detect SQL injection attempts."""
        if not text:
            return False
        
        text_lower = text.lower()
        
        for pattern in self.sql_patterns:
            if pattern.search(text_lower):
                return True
        
        return False
    
    def detect_xss(self, text: str) -> bool:
        """Detect XSS attempts."""
        if not text:
            return False
        
        for pattern in self.xss_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def detect_path_traversal(self, text: str) -> bool:
        """Detect path traversal attempts."""
        if not text:
            return False
        
        for pattern in self.path_traversal_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def detect_command_injection(self, text: str) -> bool:
        """Detect command injection attempts."""
        if not text:
            return False
        
        for pattern in self.command_injection_patterns:
            if pattern.search(text):
                return True
        
        return False
    
    def validate_input(self, input_data: Any, input_type: str = 'general') -> Dict[str, Any]:
        """Comprehensive input validation."""
        if isinstance(input_data, str):
            return self._validate_string_input(input_data, input_type)
        elif isinstance(input_data, dict):
            return self._validate_dict_input(input_data)
        else:
            return {'valid': True, 'sanitized': input_data, 'threats': []}
    
    def _validate_string_input(self, text: str, input_type: str) -> Dict[str, Any]:
        """Validate string input."""
        threats = []
        
        if self.detect_sql_injection(text):
            threats.append('SQL Injection')
        
        if self.detect_xss(text):
            threats.append('XSS Attack')
        
        if self.detect_path_traversal(text):
            threats.append('Path Traversal')
        
        if self.detect_command_injection(text):
            threats.append('Command Injection')
        
        # Type-specific validation
        if input_type == 'email':
            if not self.validate_email(text):
                threats.append('Invalid Email Format')
        
        sanitized = self._sanitize_string(text)
        
        return {
            'valid': len(threats) == 0,
            'sanitized': sanitized,
            'threats': threats,
            'original_length': len(text),
            'sanitized_length': len(sanitized)
        }
    
    def _validate_dict_input(self, data: dict) -> Dict[str, Any]:
        """Validate dictionary input."""
        threats = []
        sanitized = {}
        
        for key, value in data.items():
            key_validation = self._validate_string_input(str(key), 'general')
            if not key_validation['valid']:
                threats.extend([f"Key '{key}': {threat}" for threat in key_validation['threats']])
            
            if isinstance(value, str):
                value_validation = self._validate_string_input(value, 'general')
                if not value_validation['valid']:
                    threats.extend([f"Value for '{key}': {threat}" for threat in value_validation['threats']])
                sanitized[key_validation['sanitized']] = value_validation['sanitized']
            else:
                sanitized[key_validation['sanitized']] = value
        
        return {
            'valid': len(threats) == 0,
            'sanitized': sanitized,
            'threats': threats
        }

# Global input validator instance
input_validator = InputValidator()
