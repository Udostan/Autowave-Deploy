// History functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('History JS loaded');

    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const historyResults = document.getElementById('historyResults');

    // Load history when the history tab is clicked
    const historyTabButton = document.querySelector('[data-tab="history"]');
    if (historyTabButton) {
        historyTabButton.addEventListener('click', loadHistory);
    }

    function loadHistory() {
        if (!historyResults) {
            console.error('History results element not found');
            return;
        }

        // Show loading state
        historyResults.innerHTML = '<div class="loading"><div class="loading-dots"><span></span><span></span><span></span></div></div>';

        // Get session ID from localStorage
        const sessionId = localStorage.getItem('session_id');

        if (!sessionId) {
            historyResults.innerHTML = `
                <div class="empty-state">
                    <p>No session history available. Complete a task to create a session.</p>
                </div>
            `;
            return;
        }

        // Make API request
        fetch(`/api/super-agent/session-history?session_id=${sessionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.history && data.history.length > 0) {
                historyResults.innerHTML = `
                    <div class="session-info">
                        <p>Session ID: ${sessionId}</p>
                        <p>Created: ${new Date(data.created_at).toLocaleString()}</p>
                        <p>Last Activity: ${new Date(data.last_activity).toLocaleString()}</p>
                    </div>
                    <div class="history-list">
                        ${data.history.map((item, index) => `
                            <div class="history-item">
                                <div class="history-header">
                                    <div class="history-action">${item.action}</div>
                                    <div class="history-timestamp">${new Date(item.timestamp).toLocaleString()}</div>
                                </div>
                                ${item.details.task_description ? `<div class="history-task"><strong>Task:</strong> ${item.details.task_description}</div>` : ''}
                                ${item.details.url ? `<div class="history-url"><strong>URL:</strong> ${item.details.url}</div>` : ''}
                                ${item.details.prompt ? `<div class="history-prompt"><strong>Prompt:</strong> ${item.details.prompt}</div>` : ''}
                                ${item.details.user_message ? `<div class="history-message"><strong>Message:</strong> ${item.details.user_message}</div>` : ''}
                                ${item.details.assistant_response ? `<div class="history-response"><strong>Response:</strong> ${item.details.assistant_response.substring(0, 200)}${item.details.assistant_response.length > 200 ? '...' : ''}</div>` : ''}
                                ${item.details.changes_made && item.details.changes_made.length > 0 ? `<div class="history-changes"><strong>Changes:</strong> ${item.details.changes_made.join(', ')}</div>` : ''}
                                <button class="history-replay-btn" data-index="${index}">Replay</button>
                            </div>
                        `).join('')}
                    </div>
                `;

                // Add event listeners to replay buttons
                document.querySelectorAll('.history-replay-btn').forEach(button => {
                    button.addEventListener('click', function() {
                        const index = parseInt(this.getAttribute('data-index'));
                        const item = data.history[index];
                        replayHistoryItem(item);
                    });
                });
            } else {
                historyResults.innerHTML = `
                    <div class="empty-state">
                        <p>No history available for this session</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            historyResults.innerHTML = `
                <div class="result-item error">
                    <div class="result-title">Error</div>
                    <div class="result-content">Failed to load history: ${error.message}</div>
                </div>
            `;
        });
    }

    // Function to replay a history item
    function replayHistoryItem(item) {
        // Switch to the appropriate tab based on the action
        let tabToShow = 'task';

        if (item.action === 'browse_web') {
            tabToShow = 'browse';
            // Set the URL input value
            document.getElementById('urlInput').value = item.details.url || '';
        } else if (item.action === 'generate_code') {
            tabToShow = 'code';
            // Set the code prompt value
            document.getElementById('codePrompt').value = item.details.prompt || '';
            // Set the language if available
            if (item.details.language) {
                document.getElementById('language').value = item.details.language;
            }
        } else if (item.action === 'task_execution') {
            tabToShow = 'task';
            // Set the task description
            document.getElementById('taskDescription').value = item.details.task_description || '';
            // Set the browser options if available
            if (item.details.use_browser_use !== undefined) {
                document.getElementById('useBrowserUse').checked = item.details.use_browser_use;
            }
            if (item.details.use_advanced_browser !== undefined) {
                document.getElementById('useAdvancedBrowser').checked = item.details.use_advanced_browser;
            }
        } else if (item.action === 'code_wave_chat') {
            // Navigate to Code Wave page and restore the chat session
            window.location.href = '/code-ide';
            // Store the session data to restore after page load
            localStorage.setItem('restore_code_wave_session', JSON.stringify({
                code_before: item.details.code_before,
                code_after: item.details.code_after,
                user_message: item.details.user_message,
                assistant_response: item.details.assistant_response,
                changes_made: item.details.changes_made,
                suggestions: item.details.suggestions
            }));
            return; // Don't continue with tab switching since we're navigating away
        }

        // Show the appropriate tab
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
            if (button.getAttribute('data-tab') === tabToShow) {
                button.classList.add('active');
            }
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            if (content.id === tabToShow + '-content') {
                content.classList.add('active');
            }
        });
    }

    // Add event listener to clear history button
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear the session history?')) {
                // Get session ID from localStorage
                const sessionId = localStorage.getItem('session_id');
                if (!sessionId) {
                    alert('No active session to clear.');
                    return;
                }

                // Make API request
                fetch(`/api/super-agent/clear-session?session_id=${sessionId}`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remove session ID from localStorage
                        localStorage.removeItem('session_id');
                        historyResults.innerHTML = `
                            <div class="empty-state">
                                <p>History cleared</p>
                            </div>
                        `;
                    } else {
                        alert('Failed to clear history: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Failed to clear history: ' + error.message);
                });
            }
        });
    }
});
