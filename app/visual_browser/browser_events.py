"""
Browser Events Module

This module provides WebSocket functionality to send real-time browser events
to the frontend.
"""

import json
import logging
import threading
import time
from typing import Dict, Any, List, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Global variables
clients = set()
client_lock = threading.Lock()

def register_client(client):
    """Register a new WebSocket client."""
    with client_lock:
        clients.add(client)
        logger.info(f"New client registered. Total clients: {len(clients)}")

def unregister_client(client):
    """Unregister a WebSocket client."""
    with client_lock:
        clients.remove(client)
        logger.info(f"Client unregistered. Total clients: {len(clients)}")

def broadcast_event(event_type: str, data: Dict[str, Any]):
    """Broadcast an event to all connected clients."""
    message = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": time.time()
    })
    
    with client_lock:
        disconnected_clients = set()
        for client in clients:
            try:
                client.send(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {str(e)}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            clients.remove(client)
    
    logger.debug(f"Broadcast {event_type} event to {len(clients)} clients")

def send_navigation_event(url: str, title: str = None, status: str = "loading"):
    """Send a navigation event to all clients."""
    broadcast_event("navigation", {
        "url": url,
        "title": title or "",
        "status": status
    })

def send_search_event(query: str, results: List[Dict[str, str]] = None):
    """Send a search event to all clients."""
    broadcast_event("search", {
        "query": query,
        "results": results or []
    })

def send_status_event(status: str, details: str = None):
    """Send a status update event to all clients."""
    broadcast_event("status", {
        "status": status,
        "details": details or ""
    })

def send_error_event(error: str, details: str = None):
    """Send an error event to all clients."""
    broadcast_event("error", {
        "error": error,
        "details": details or ""
    })

def send_screenshot_event(screenshot_url: str):
    """Send a screenshot event to all clients."""
    broadcast_event("screenshot", {
        "url": screenshot_url
    })
