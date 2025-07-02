/**
 * Browser Events JavaScript
 * 
 * This file handles browser events for the Live Browser.
 */

// Initialize socket connection
let socket = null;
let isConnected = false;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// Browser state
let browserState = {
    url: null,
    title: null,
    status: 'idle',
    screenshot: null,
    searchQuery: null,
    searchResults: [],
    error: null
};

// DOM elements
let statusElement = null;
let screenshotElement = null;
let searchResultsElement = null;
let urlElement = null;
let titleElement = null;

// Initialize browser events
function initBrowserEvents() {
    console.log('Initializing browser events...');
    
    // Find DOM elements
    statusElement = document.getElementById('status-text');
    screenshotElement = document.getElementById('browser-screenshot');
    searchResultsElement = document.getElementById('search-results');
    urlElement = document.getElementById('browser-url');
    titleElement = document.getElementById('browser-title');
    
    // Connect to WebSocket server
    connectSocket();
    
    // Add event listeners
    window.addEventListener('beforeunload', () => {
        if (socket) {
            socket.close();
        }
    });
}

// Connect to WebSocket server
function connectSocket() {
    try {
        // Create socket connection
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = 5010; // WebSocket server port
        
        // Create socket URL
        const socketUrl = `${protocol}//${host}:${port}`;
        
        console.log(`Connecting to WebSocket server at ${socketUrl}...`);
        
        // Create socket
        socket = io(socketUrl);
        
        // Add event listeners
        socket.on('connect', handleConnect);
        socket.on('disconnect', handleDisconnect);
        socket.on('error', handleError);
        socket.on('screenshot', handleScreenshot);
        socket.on('navigation', handleNavigation);
        socket.on('search', handleSearch);
        socket.on('status', handleStatus);
        socket.on('browser_event', handleBrowserEvent);
        
        // Start ping interval
        setInterval(sendPing, 30000);
    } catch (error) {
        console.error('Error connecting to WebSocket server:', error);
        handleConnectionError(error);
    }
}

// Handle socket connection
function handleConnect() {
    console.log('Connected to WebSocket server');
    isConnected = true;
    reconnectAttempts = 0;
    
    // Update status
    updateStatus('connected', 'Connected to browser');
    
    // Register session
    socket.emit('register_session', {
        session_id: 'live_browser_session'
    });
}

// Handle socket disconnection
function handleDisconnect() {
    console.log('Disconnected from WebSocket server');
    isConnected = false;
    
    // Update status
    updateStatus('disconnected', 'Disconnected from browser');
    
    // Try to reconnect
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
        setTimeout(connectSocket, 2000 * reconnectAttempts);
    }
}

// Handle socket error
function handleError(error) {
    console.error('WebSocket error:', error);
    
    // Update status
    updateStatus('error', error.message || 'Error connecting to browser');
    
    // Update browser state
    browserState.error = error.message || 'Unknown error';
    
    // Update UI
    updateUI();
}

// Handle connection error
function handleConnectionError(error) {
    console.error('Connection error:', error);
    
    // Update status
    updateStatus('error', 'Error connecting to browser server');
    
    // Update browser state
    browserState.error = error.message || 'Connection error';
    
    // Update UI
    updateUI();
    
    // Try to reconnect
    if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
        setTimeout(connectSocket, 2000 * reconnectAttempts);
    }
}

// Handle screenshot event
function handleScreenshot(data) {
    console.log('Received screenshot:', data);
    
    // Update browser state
    browserState.screenshot = data.screenshot;
    if (data.url) browserState.url = data.url;
    if (data.title) browserState.title = data.title;
    
    // Update UI
    updateUI();
}

// Handle navigation event
function handleNavigation(data) {
    console.log('Received navigation event:', data);
    
    // Update browser state
    browserState.url = data.url;
    browserState.title = data.title || '';
    browserState.status = data.status || 'idle';
    
    // Update UI
    updateUI();
}

// Handle search event
function handleSearch(data) {
    console.log('Received search event:', data);
    
    // Update browser state
    browserState.searchQuery = data.query;
    browserState.searchResults = data.results || [];
    
    // Update UI
    updateUI();
    
    // Update search results
    updateSearchResults();
}

// Handle status event
function handleStatus(data) {
    console.log('Received status event:', data);
    
    // Update browser state
    browserState.status = data.status;
    
    // Update UI
    updateStatus(data.status, data.details || '');
}

// Handle browser event
function handleBrowserEvent(data) {
    console.log('Received browser event:', data);
    
    // Handle different event types
    switch (data.type) {
        case 'screenshot_update':
            handleScreenshot(data);
            break;
        case 'navigation':
            handleNavigation(data);
            break;
        case 'search':
            handleSearch(data);
            break;
        case 'status':
            handleStatus(data);
            break;
        case 'error':
            handleError(data);
            break;
        default:
            console.log('Unknown browser event type:', data.type);
    }
}

// Update status
function updateStatus(status, details) {
    // Update browser state
    browserState.status = status;
    
    // Update status element
    if (statusElement) {
        statusElement.textContent = details || status;
        
        // Add appropriate class
        statusElement.className = 'status-text';
        statusElement.classList.add(`status-${status}`);
    }
}

// Update search results
function updateSearchResults() {
    // Check if search results element exists
    if (!searchResultsElement) return;
    
    // Clear search results
    searchResultsElement.innerHTML = '';
    
    // Check if we have search results
    if (!browserState.searchResults || browserState.searchResults.length === 0) {
        // No search results
        if (browserState.searchQuery) {
            searchResultsElement.innerHTML = `<p class="no-results">No results found for "${browserState.searchQuery}"</p>`;
        }
        return;
    }
    
    // Add search results
    browserState.searchResults.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.className = 'search-result';
        resultElement.innerHTML = `
            <a href="${result.url}" class="result-title" target="_blank">${result.title}</a>
            <div class="result-url">${result.url}</div>
            <div class="result-snippet">${result.snippet}</div>
        `;
        searchResultsElement.appendChild(resultElement);
    });
}

// Update UI
function updateUI() {
    // Update URL
    if (urlElement && browserState.url) {
        urlElement.textContent = browserState.url;
    }
    
    // Update title
    if (titleElement && browserState.title) {
        titleElement.textContent = browserState.title;
    }
    
    // Update screenshot
    if (screenshotElement && browserState.screenshot) {
        screenshotElement.src = browserState.screenshot;
        screenshotElement.classList.remove('hidden');
    }
    
    // Update search results
    updateSearchResults();
}

// Send ping to keep connection alive
function sendPing() {
    if (socket && isConnected) {
        socket.emit('ping', {
            timestamp: Date.now()
        });
    }
}

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize browser events
    initBrowserEvents();
});
