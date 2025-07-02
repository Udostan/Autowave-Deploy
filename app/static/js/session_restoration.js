/**
 * Session Restoration Utility
 * Automatically restores session data when users click on history items
 * Similar to how Genspark and ChatGPT handle conversation restoration
 */

class SessionRestoration {
    constructor() {
        this.init();
    }

    init() {
        // Check for session restoration data on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.checkForSessionRestoration();
        });

        // Also check immediately if DOM is already loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.checkForSessionRestoration();
            });
        } else {
            this.checkForSessionRestoration();
        }
    }

    checkForSessionRestoration() {
        console.log('Checking for session restoration data...');
        
        // Check URL parameters first
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');
        
        if (sessionId) {
            console.log('Session ID found in URL:', sessionId);
            this.restoreSessionFromUrl(sessionId);
        }

        // Check localStorage for continuation data
        const continuationData = this.getContinuationData();
        const sessionData = this.getSessionData();

        if (continuationData || sessionData) {
            console.log('Found stored session data, attempting restoration...');
            this.restoreSessionFromStorage(continuationData, sessionData);
        }
    }

    getContinuationData() {
        try {
            const data = localStorage.getItem('history_continuation_data');
            if (data) {
                const parsed = JSON.parse(data);
                // Check if data is not too old (max 5 minutes)
                if (Date.now() - parsed.timestamp < 300000) {
                    return parsed;
                }
                // Clean up old data
                localStorage.removeItem('history_continuation_data');
            }
        } catch (error) {
            console.error('Error getting continuation data:', error);
        }
        return null;
    }

    getSessionData() {
        try {
            const data = localStorage.getItem('restore_session_data');
            if (data) {
                const parsed = JSON.parse(data);
                // Check if data is not too old (max 5 minutes)
                if (Date.now() - parsed.timestamp < 300000) {
                    return parsed;
                }
                // Clean up old data
                localStorage.removeItem('restore_session_data');
            }
        } catch (error) {
            console.error('Error getting session data:', error);
        }
        return null;
    }

    async restoreSessionFromUrl(sessionId) {
        try {
            console.log('Restoring session from URL:', sessionId);
            
            // Fetch session details from API
            const response = await fetch(`/api/history/session/${sessionId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    console.log('Session data loaded from API:', data);
                    this.applySessionRestoration(data.session, data.activities);
                }
            }
        } catch (error) {
            console.error('Error restoring session from URL:', error);
        }
    }

    restoreSessionFromStorage(continuationData, sessionData) {
        try {
            console.log('Restoring session from storage:', { continuationData, sessionData });
            
            // Apply the restoration based on available data
            if (continuationData && continuationData.data) {
                this.applySessionRestoration(continuationData.data.session, continuationData.data.activities);
            } else if (sessionData) {
                this.applyBasicSessionRestoration(sessionData);
            }

            // Clear the stored data after use
            this.clearStoredData();
        } catch (error) {
            console.error('Error restoring session from storage:', error);
        }
    }

    applySessionRestoration(session, activities) {
        console.log('Applying session restoration:', { session, activities });
        
        // Show restoration notification
        this.showRestorationNotification(session);

        // Apply restoration based on agent type
        const agentType = session.agent_type;
        
        switch (agentType) {
            case 'autowave_chat':
                this.restoreAutowaveChat(session, activities);
                break;
            case 'prime_agent':
                this.restorePrimeAgent(session, activities);
                break;
            case 'agentic_code':
                this.restoreAgenticCode(session, activities);
                break;
            case 'research_lab':
                this.restoreResearchLab(session, activities);
                break;
            case 'agent_wave':
                this.restoreAgentWave(session, activities);
                break;
            default:
                console.log('Unknown agent type for restoration:', agentType);
        }
    }

    applyBasicSessionRestoration(sessionData) {
        console.log('Applying basic session restoration:', sessionData);
        
        // Show basic restoration notification
        this.showBasicRestorationNotification(sessionData);
        
        // Set session ID in relevant inputs or forms
        this.setSessionId(sessionData.sessionId);
    }

    restoreAutowaveChat(session, activities) {
        console.log('Restoring AutoWave Chat session');
        
        // Restore chat history if available
        if (activities && activities.length > 0) {
            const chatContainer = document.getElementById('chat-container') || 
                                document.getElementById('messages-container') ||
                                document.querySelector('.chat-messages');
            
            if (chatContainer) {
                activities.forEach(activity => {
                    if (activity.input_data && activity.output_data) {
                        this.addChatMessage(chatContainer, activity.input_data, 'user');
                        this.addChatMessage(chatContainer, activity.output_data, 'assistant');
                    }
                });
            }
        }
        
        this.setSessionId(session.id);
    }

    restorePrimeAgent(session, activities) {
        console.log('Restoring Prime Agent session');
        
        // Restore task input if available
        if (activities && activities.length > 0) {
            const lastActivity = activities[activities.length - 1];
            const taskInput = document.getElementById('task-input') || 
                            document.getElementById('user-input') ||
                            document.querySelector('textarea[name="task"]');
            
            if (taskInput && lastActivity.input_data) {
                taskInput.value = lastActivity.input_data;
            }
        }
        
        this.setSessionId(session.id);
    }

    restoreAgenticCode(session, activities) {
        console.log('Restoring Agentic Code session');
        
        // Restore code and conversation if available
        if (activities && activities.length > 0) {
            const lastActivity = activities[activities.length - 1];
            
            // Restore code in editor
            const codeEditor = document.getElementById('code-editor') ||
                             document.querySelector('.code-editor textarea');
            
            if (codeEditor && lastActivity.output_data) {
                codeEditor.value = lastActivity.output_data;
            }
            
            // Restore conversation
            const messageInput = document.getElementById('message-input') ||
                               document.querySelector('input[name="message"]');
            
            if (messageInput && lastActivity.input_data) {
                messageInput.value = lastActivity.input_data;
            }
        }
        
        this.setSessionId(session.id);
    }

    restoreResearchLab(session, activities) {
        console.log('Restoring Research Lab session');
        
        // Restore research query if available
        if (activities && activities.length > 0) {
            const lastActivity = activities[activities.length - 1];
            const queryInput = document.getElementById('research-query') ||
                             document.getElementById('query-input') ||
                             document.querySelector('input[name="query"]');
            
            if (queryInput && lastActivity.input_data) {
                queryInput.value = lastActivity.input_data;
            }
        }
        
        this.setSessionId(session.id);
    }

    restoreAgentWave(session, activities) {
        console.log('Restoring Agent Wave session');
        
        // Restore document content if available
        if (activities && activities.length > 0) {
            const lastActivity = activities[activities.length - 1];
            const contentInput = document.getElementById('content-input') ||
                               document.querySelector('textarea[name="content"]');
            
            if (contentInput && lastActivity.input_data) {
                contentInput.value = lastActivity.input_data;
            }
        }
        
        this.setSessionId(session.id);
    }

    addChatMessage(container, content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="message-timestamp">${new Date().toLocaleTimeString()}</div>
        `;
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    setSessionId(sessionId) {
        // Set session ID in hidden inputs or data attributes
        const sessionInputs = document.querySelectorAll('input[name="session_id"]');
        sessionInputs.forEach(input => {
            input.value = sessionId;
        });
        
        // Set as data attribute on body for global access
        document.body.dataset.sessionId = sessionId;
        
        console.log('Session ID set:', sessionId);
    }

    showRestorationNotification(session) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                </svg>
                Session restored: ${session.session_name || 'Previous activity'}
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showBasicRestorationNotification(sessionData) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #2196F3;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                Continuing: ${sessionData.agentDisplayName}
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    clearStoredData() {
        try {
            localStorage.removeItem('history_continuation_data');
            localStorage.removeItem('restore_session_data');
            console.log('Cleared stored session data');
        } catch (error) {
            console.error('Error clearing stored data:', error);
        }
    }
}

// Initialize session restoration
new SessionRestoration();

// Export for use in other scripts
window.SessionRestoration = SessionRestoration;
