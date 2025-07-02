"""
Data Encryption
AES-256 encryption for sensitive data protection.
"""

import os
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class DataEncryption:
    """AES-256 encryption for sensitive data."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        # Try to get key from environment
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            try:
                return base64.urlsafe_b64decode(env_key.encode())
            except Exception as e:
                logger.warning(f"Invalid encryption key in environment: {e}")
        
        # Generate new key from secret
        secret = os.getenv('SECRET_KEY', 'autowave-default-secret-change-in-production')
        salt = b'autowave-salt-2025'  # In production, use random salt stored securely
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        try:
            if not data:
                return data
            
            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return data  # Return original data if encryption fails
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        try:
            if not encrypted_data:
                return encrypted_data
            
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return encrypted_data  # Return original data if decryption fails
    
    def encrypt_dict(self, data: dict, fields_to_encrypt: list = None) -> dict:
        """Encrypt specific fields in a dictionary."""
        if not data:
            return data
        
        if fields_to_encrypt is None:
            # Default sensitive fields
            fields_to_encrypt = ['password', 'token', 'secret', 'key', 'api_key']
        
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and isinstance(encrypted_data[field], str):
                encrypted_data[field] = self.encrypt(encrypted_data[field])
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, fields_to_decrypt: list = None) -> dict:
        """Decrypt specific fields in a dictionary."""
        if not data:
            return data
        
        if fields_to_decrypt is None:
            # Default sensitive fields
            fields_to_decrypt = ['password', 'token', 'secret', 'key', 'api_key']
        
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and isinstance(decrypted_data[field], str):
                decrypted_data[field] = self.decrypt(decrypted_data[field])
        
        return decrypted_data
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{base64.b64encode(password_hash).decode()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            salt, password_hash = hashed_password.split(':')
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return base64.b64encode(computed_hash).decode() == password_hash
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self) -> str:
        """Generate secure API key."""
        return f"autowave_{secrets.token_urlsafe(32)}"

# Global encryption instance
data_encryption = DataEncryption()
