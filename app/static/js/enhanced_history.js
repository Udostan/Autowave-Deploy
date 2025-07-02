/**
 * Enhanced History JavaScript
 * Provides client-side activity tracking and history management
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced History JS loaded');
    
    // Initialize the enhanced history system
    initializeEnhancedHistory();
});

function initializeEnhancedHistory() {
    // Make trackActivity function globally available
    window.trackActivity = trackActivity;
    
    console.log('Enhanced History system initialized');
}

/**
 * Track user activity across all agents
 * @param {string} agentType - Type of agent (e.g., 'autowave_chat', 'prime_agent', 'super_agent')
 * @param {string} activityType - Type of activity (e.g., 'chat', 'task', 'research')
 * @param {object} inputData - Input data for the activity
 * @param {object} outputData - Output data from the activity
 * @param {number} processingTimeMs - Processing time in milliseconds
 * @param {boolean} success - Whether the activity was successful
 * @param {string} errorMessage - Error message if activity failed
 */
function trackActivity(agentType, activityType, inputData, outputData = null, processingTimeMs = null, success = true, errorMessage = null) {
    try {
        // Get user ID from session storage or generate a temporary one
        let userId;
        try {
            // Check if we're in a secure context and sessionStorage is available
            if (typeof Storage !== "undefined" && window.sessionStorage && window.isSecureContext !== false) {
                try {
                    userId = sessionStorage.getItem('user_id');
                    if (!userId) {
                        // Try to get from global variable or generate temporary ID
                        userId = window.currentUserId || 'anonymous_' + Date.now();
                        sessionStorage.setItem('user_id', userId);
                    }
                } catch (storageAccessError) {
                    // Storage access denied, use fallback
                    userId = window.currentUserId || 'anonymous_' + Date.now();
                }
            } else {
                // Fallback if sessionStorage is not available or not in secure context
                userId = window.currentUserId || 'anonymous_' + Date.now();
            }
        } catch (storageError) {
            // Fallback if storage access is denied
            userId = window.currentUserId || 'anonymous_' + Date.now();
        }
        
        // Prepare activity data
        const activityData = {
            user_id: userId,
            agent_type: agentType,
            activity_type: activityType,
            input_data: inputData,
            output_data: outputData,
            processing_time_ms: processingTimeMs,
            success: success,
            error_message: errorMessage
        };
        
        // Send to enhanced history API
        fetch('/api/history/track', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(activityData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Activity tracked successfully:', data.activity_id);
            } else {
                console.warn('Failed to track activity:', data.error);
            }
        })
        .catch(error => {
            console.warn('Error tracking activity:', error);
            // Don't throw error to avoid breaking the main functionality
        });
        
    } catch (error) {
        console.warn('Error in trackActivity:', error);
        // Don't throw error to avoid breaking the main functionality
    }
}

// Create a safe wrapper for trackActivity to prevent any errors from propagating
const originalTrackActivity = trackActivity;
window.trackActivity = function(...args) {
    try {
        return originalTrackActivity(...args);
    } catch (error) {
        // Silently fail to prevent any errors from propagating
        console.warn('Activity tracking wrapper caught error:', error.message || error);
        return null;
    }
};

/**
 * Get user's activity history
 * @param {number} limit - Number of items to retrieve
 * @param {string} agentType - Filter by agent type (optional)
 * @param {string} query - Search query (optional)
 * @returns {Promise} Promise that resolves to history data
 */
function getHistory(limit = 50, agentType = null, query = '') {
    const params = new URLSearchParams({
        limit: limit.toString()
    });
    
    if (agentType) {
        params.append('agent_type', agentType);
    }
    
    if (query) {
        params.append('query', query);
    }
    
    return fetch(`/api/history/search?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data.history;
            } else {
                throw new Error(data.error || 'Failed to get history');
            }
        });
}

/**
 * Get unified history across all agents
 * @param {number} limit - Number of items to retrieve
 * @returns {Promise} Promise that resolves to unified history data
 */
function getUnifiedHistory(limit = 50) {
    return fetch(`/api/history/unified?limit=${limit}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data.history;
            } else {
                throw new Error(data.error || 'Failed to get unified history');
            }
        });
}

/**
 * Restore a session by redirecting to the appropriate agent page
 * @param {string} sessionId - Session ID to restore
 * @param {string} agentType - Type of agent for the session
 */
function restoreSession(sessionId, agentType) {
    try {
        // Map agent types to their respective URLs
        const agentUrls = {
            'autowave_chat': '/dark-chat',
            'prime_agent': '/prime-agent-tools',
            'super_agent': '/super-agent',
            'agent_alpha': '/agentic-code',
            'research_lab': '/research-lab'
        };
        
        const baseUrl = agentUrls[agentType] || '/';
        const url = `${baseUrl}?session_id=${sessionId}`;
        
        // Redirect to the agent page with session ID
        window.location.href = url;
        
    } catch (error) {
        console.error('Error restoring session:', error);
        alert('Failed to restore session. Please try again.');
    }
}

// Make functions globally available
window.getHistory = getHistory;
window.getUnifiedHistory = getUnifiedHistory;
window.restoreSession = restoreSession;
