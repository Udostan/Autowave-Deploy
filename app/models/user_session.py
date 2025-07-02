"""
User Session Model for Super Agent.

This module provides a model for user sessions.
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta


class UserSession:
    """Model for user sessions."""

    def __init__(self, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        Initialize a user session.

        Args:
            user_id (Optional[str]): The user ID. Default is None.
            session_id (Optional[str]): The session ID. Default is None.
        """
        self.user_id = user_id or str(uuid.uuid4())
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.data = {}
        self.history = []
        self.preferences = {}

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.now()

    def is_expired(self, expiry_minutes: int = 60) -> bool:
        """
        Check if the session is expired.

        Args:
            expiry_minutes (int): The session expiry time in minutes. Default is 60.

        Returns:
            bool: Whether the session is expired.
        """
        expiry_time = self.last_activity + timedelta(minutes=expiry_minutes)
        return datetime.now() > expiry_time

    def set_data(self, key: str, value: Any) -> None:
        """
        Set a data value.

        Args:
            key (str): The data key.
            value (Any): The data value.
        """
        self.data[key] = value
        self.update_activity()

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get a data value.

        Args:
            key (str): The data key.
            default (Any): The default value if the key is not found. Default is None.

        Returns:
            Any: The data value.
        """
        self.update_activity()
        return self.data.get(key, default)

    def has_data(self, key: str) -> bool:
        """
        Check if a data key exists.

        Args:
            key (str): The data key.

        Returns:
            bool: Whether the key exists.
        """
        self.update_activity()
        return key in self.data

    def delete_data(self, key: str) -> None:
        """
        Delete a data value.

        Args:
            key (str): The data key.
        """
        if key in self.data:
            del self.data[key]
        self.update_activity()

    def clear_data(self) -> None:
        """Clear all data."""
        self.data = {}
        self.update_activity()

    def add_to_history(self, action: str, details: Dict[str, Any]) -> None:
        """
        Add an action to the history.

        Args:
            action (str): The action name.
            details (Dict[str, Any]): The action details.
        """
        self.history.append({
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self.update_activity()

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the session history.

        Args:
            limit (int): The maximum number of history items to return. Default is 10.

        Returns:
            List[Dict[str, Any]]: The session history.
        """
        self.update_activity()
        return self.history[-limit:] if limit > 0 else self.history

    def clear_history(self) -> None:
        """Clear the session history."""
        self.history = []
        self.update_activity()

    def set_preference(self, key: str, value: Any) -> None:
        """
        Set a preference value.

        Args:
            key (str): The preference key.
            value (Any): The preference value.
        """
        self.preferences[key] = value
        self.update_activity()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a preference value.

        Args:
            key (str): The preference key.
            default (Any): The default value if the key is not found. Default is None.

        Returns:
            Any: The preference value.
        """
        self.update_activity()
        return self.preferences.get(key, default)

    def delete_preference(self, key: str) -> None:
        """
        Delete a preference value.

        Args:
            key (str): The preference key.
        """
        if key in self.preferences:
            del self.preferences[key]
        self.update_activity()

    def clear_preferences(self) -> None:
        """Clear all preferences."""
        self.preferences = {}
        self.update_activity()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the session to a dictionary.

        Returns:
            Dict[str, Any]: The session as a dictionary.
        """
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "data": self.data,
            "history": self.history,
            "preferences": self.preferences
        }

    def to_json(self) -> str:
        """
        Convert the session to a JSON string.

        Returns:
            str: The session as a JSON string.
        """
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """
        Create a session from a dictionary.

        Args:
            data (Dict[str, Any]): The session data.

        Returns:
            UserSession: The session.
        """
        session = cls(user_id=data.get("user_id"), session_id=data.get("session_id"))
        session.created_at = datetime.fromisoformat(data.get("created_at"))
        session.last_activity = datetime.fromisoformat(data.get("last_activity"))
        session.data = data.get("data", {})
        session.history = data.get("history", [])
        session.preferences = data.get("preferences", {})
        return session

    @classmethod
    def from_json(cls, json_str: str) -> 'UserSession':
        """
        Create a session from a JSON string.

        Args:
            json_str (str): The session data as a JSON string.

        Returns:
            UserSession: The session.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
