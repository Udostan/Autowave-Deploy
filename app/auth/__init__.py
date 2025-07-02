"""
AutoWave Supabase Authentication System
Clean, classic authentication with email/Gmail integration.
"""

from .supabase_auth import SupabaseAuth
from .auth_routes import auth_bp

__all__ = ['SupabaseAuth', 'auth_bp']
