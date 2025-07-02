"""
Session Manager for Super Agent.

This module provides a manager for user sessions.
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading
import sqlite3

from app.models.user_session import UserSession


class SessionManager:
    """Manager for user sessions."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance of the session manager."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SessionManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None, cleanup_interval: int = 3600):
        """
        Initialize the session manager.

        Args:
            db_path (Optional[str]): The path to the SQLite database. Default is None.
            cleanup_interval (int): The interval for cleaning up expired sessions in seconds. Default is 3600.
        """
        if self._initialized:
            return
        
        self.db_path = db_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "sessions.db")
        self.cleanup_interval = cleanup_interval
        self.sessions = {}
        self.last_cleanup = time.time()
        
        # Create the database directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize the database
        self._init_db()
        
        # Load sessions from the database
        self._load_sessions()
        
        self._initialized = True

    def _init_db(self) -> None:
        """Initialize the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the sessions table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_activity TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()

    def _load_sessions(self) -> None:
        """Load sessions from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all sessions
        cursor.execute('SELECT session_id, user_id, data, created_at, last_activity FROM sessions')
        rows = cursor.fetchall()
        
        for row in rows:
            session_id, user_id, data_json, created_at, last_activity = row
            try:
                data = json.loads(data_json)
                session = UserSession(user_id=user_id, session_id=session_id)
                session.created_at = datetime.fromisoformat(created_at)
                session.last_activity = datetime.fromisoformat(last_activity)
                session.data = data.get("data", {})
                session.history = data.get("history", [])
                session.preferences = data.get("preferences", {})
                
                # Only load non-expired sessions
                if not session.is_expired():
                    self.sessions[session_id] = session
            except Exception as e:
                print(f"Error loading session {session_id}: {str(e)}")
        
        conn.close()

    def _save_session(self, session: UserSession) -> None:
        """
        Save a session to the database.

        Args:
            session (UserSession): The session to save.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save the session
        cursor.execute(
            'INSERT OR REPLACE INTO sessions (session_id, user_id, data, created_at, last_activity) VALUES (?, ?, ?, ?, ?)',
            (
                session.session_id,
                session.user_id,
                session.to_json(),
                session.created_at.isoformat(),
                session.last_activity.isoformat()
            )
        )
        
        conn.commit()
        conn.close()

    def _delete_session(self, session_id: str) -> None:
        """
        Delete a session from the database.

        Args:
            session_id (str): The session ID.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete the session
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        
        conn.commit()
        conn.close()

    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        current_time = time.time()
        
        # Only clean up if the cleanup interval has passed
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        
        # Find expired sessions
        expired_session_ids = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_session_ids.append(session_id)
        
        # Delete expired sessions
        for session_id in expired_session_ids:
            self.delete_session(session_id)

    def create_session(self, user_id: Optional[str] = None) -> UserSession:
        """
        Create a new session.

        Args:
            user_id (Optional[str]): The user ID. Default is None.

        Returns:
            UserSession: The new session.
        """
        self._cleanup_expired_sessions()
        
        session = UserSession(user_id=user_id)
        self.sessions[session.session_id] = session
        self._save_session(session)
        
        return session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Get a session by ID.

        Args:
            session_id (str): The session ID.

        Returns:
            Optional[UserSession]: The session, or None if not found.
        """
        self._cleanup_expired_sessions()
        
        session = self.sessions.get(session_id)
        
        if session and session.is_expired():
            self.delete_session(session_id)
            return None
        
        return session

    def update_session(self, session: UserSession) -> None:
        """
        Update a session.

        Args:
            session (UserSession): The session to update.
        """
        self._cleanup_expired_sessions()
        
        self.sessions[session.session_id] = session
        self._save_session(session)

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session.

        Args:
            session_id (str): The session ID.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        self._delete_session(session_id)

    def get_sessions_by_user(self, user_id: str) -> List[UserSession]:
        """
        Get all sessions for a user.

        Args:
            user_id (str): The user ID.

        Returns:
            List[UserSession]: The user's sessions.
        """
        self._cleanup_expired_sessions()
        
        return [session for session in self.sessions.values() if session.user_id == user_id]

    def get_all_sessions(self) -> List[UserSession]:
        """
        Get all sessions.

        Returns:
            List[UserSession]: All sessions.
        """
        self._cleanup_expired_sessions()
        
        return list(self.sessions.values())

    def clear_all_sessions(self) -> None:
        """Clear all sessions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete all sessions
        cursor.execute('DELETE FROM sessions')
        
        conn.commit()
        conn.close()
        
        self.sessions = {}
