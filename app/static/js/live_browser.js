/**
 * Live Browser JavaScript
 *
 * This file contains the JavaScript code for the Live Browser tab.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Live Browser JS loaded');

    // Elements
    const liveBrowserContent = document.getElementById('live-browser-content');
    const liveBrowserTask = document.getElementById('live-browser-task');
    const liveBrowserExecuteTask = document.getElementById('live-browser-execute-task');
    const liveBrowserStart = document.getElementById('live-browser-start');
    const liveBrowserStop = document.getElementById('live-browser-stop');
    const liveBrowserUrl = document.getElementById('live-browser-url');
    const liveBrowserNavigate = document.getElementById('live-browser-navigate');
    const liveBrowserStatusText = document.getElementById('live-browser-status-text');
    const liveBrowserCurrentUrl = document.getElementById('live-browser-current-url');
    const liveBrowserProgress = document.getElementById('live-browser-progress');
    const liveBrowserProgressText = document.getElementById('live-browser-progress-text');
    const statusIndicator = document.getElementById('status-indicator');
    const browserFrame = document.getElementById('browser-frame');
    const browserPlaceholder = document.getElementById('browser-placeholder');
    const browserLoading = document.getElementById('browser-loading');

    console.log('Elements found:', {
        liveBrowserContent: !!liveBrowserContent,
        liveBrowserTask: !!liveBrowserTask,
        liveBrowserExecuteTask: !!liveBrowserExecuteTask,
        liveBrowserStart: !!liveBrowserStart,
        liveBrowserStop: !!liveBrowserStop,
        liveBrowserUrl: !!liveBrowserUrl,
        liveBrowserNavigate: !!liveBrowserNavigate,
        liveBrowserStatusText: !!liveBrowserStatusText,
        liveBrowserCurrentUrl: !!liveBrowserCurrentUrl,
        liveBrowserProgress: !!liveBrowserProgress,
        liveBrowserProgressText: !!liveBrowserProgressText,
        statusIndicator: !!statusIndicator,
        browserFrame: !!browserFrame,
        browserPlaceholder: !!browserPlaceholder,
        browserLoading: !!browserLoading
    });

    // Browser state
    let browserState = {
        isRunning: false,
        currentUrl: null,
        isLoading: false,
        taskInProgress: false,
        fallbackDiv: null
    };

    // Update UI based on browser state
    function updateBrowserUI() {
        console.log('Updating UI with state:', browserState);

        // Update status indicator
        if (statusIndicator) {
            if (browserState.isRunning) {
                statusIndicator.classList.remove('bg-red-500');
                statusIndicator.classList.add('bg-green-500');
                if (liveBrowserStatusText) liveBrowserStatusText.textContent = 'Running';
            } else {
                statusIndicator.classList.remove('bg-green-500');
                statusIndicator.classList.add('bg-red-500');
                if (liveBrowserStatusText) liveBrowserStatusText.textContent = 'Not running';
            }
        }

        // Update URL display
        if (liveBrowserCurrentUrl) {
            liveBrowserCurrentUrl.textContent = browserState.currentUrl || 'None';
        }

        // Update button states
        if (liveBrowserStart) liveBrowserStart.disabled = browserState.isRunning;
        if (liveBrowserStop) liveBrowserStop.disabled = !browserState.isRunning;
        if (liveBrowserNavigate) liveBrowserNavigate.disabled = !browserState.isRunning;
        if (liveBrowserExecuteTask) liveBrowserExecuteTask.disabled = !browserState.isRunning;

        // Update button styles
        if (browserState.isRunning) {
            if (liveBrowserStart) liveBrowserStart.classList.add('opacity-50', 'cursor-not-allowed');
            if (liveBrowserStop) liveBrowserStop.classList.remove('opacity-50', 'cursor-not-allowed');
            if (liveBrowserNavigate) liveBrowserNavigate.classList.remove('opacity-50', 'cursor-not-allowed');
            if (liveBrowserExecuteTask) liveBrowserExecuteTask.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            if (liveBrowserStart) liveBrowserStart.classList.remove('opacity-50', 'cursor-not-allowed');
            if (liveBrowserStop) liveBrowserStop.classList.add('opacity-50', 'cursor-not-allowed');
            if (liveBrowserNavigate) liveBrowserNavigate.classList.add('opacity-50', 'cursor-not-allowed');
            if (liveBrowserExecuteTask) liveBrowserExecuteTask.classList.add('opacity-50', 'cursor-not-allowed');
        }

        // Update browser visibility
        const screenshotDisplay = document.getElementById('screenshot-display');
        if (browserPlaceholder && screenshotDisplay) {
            if (browserState.isRunning) {
                browserPlaceholder.classList.add('hidden');
                screenshotDisplay.classList.remove('hidden');
                if (browserFrame) browserFrame.classList.add('hidden'); // Keep iframe hidden
            } else {
                browserPlaceholder.classList.remove('hidden');
                screenshotDisplay.classList.add('hidden');
                if (browserFrame) browserFrame.classList.add('hidden');
            }
        }

        // Update loading state
        if (browserLoading) {
            if (browserState.isLoading) {
                browserLoading.classList.remove('hidden');
            } else {
                browserLoading.classList.add('hidden');
            }
        }
    }

    // Check browser status from server
    function checkBrowserStatus() {
        console.log('Checking browser status...');
        return fetch('/api/live-browser/status')
            .then(response => response.json())
            .then(data => {
                console.log('Browser status response:', data);
                if (data.success) {
                    const wasRunning = browserState.isRunning;
                    const previousUrl = browserState.currentUrl;

                    // Update browser state
                    browserState.isRunning = data.is_running;

                    // Handle the current URL
                    if (data.current_url && data.current_url !== 'about:blank') {
                        browserState.currentUrl = data.current_url;
                    } else if (browserState.isRunning) {
                        // If running but URL is about:blank or null, use Google as default
                        browserState.currentUrl = 'https://www.google.com';
                    }

                    // If browser was running but now it's not, show a message
                    if (wasRunning && !browserState.isRunning) {
                        console.warn('Browser was running but now it\'s not');
                    }

                    // If browser is running, update the screenshot
                    if (browserState.isRunning) {
                        updateScreenshot();
                    }

                    updateBrowserUI();
                    return browserState.isRunning;
                } else {
                    console.error('Error checking browser status:', data.error);

                    // If there's an error, assume browser is not running
                    browserState.isRunning = false;
                    updateBrowserUI();
                    return false;
                }
            })
            .catch(error => {
                console.error('Error checking browser status:', error);

                // If there's an error, assume browser is not running
                browserState.isRunning = false;
                updateBrowserUI();
                return false;
            });
    }

    // Update the screenshot with a timestamp to prevent caching
    function updateScreenshot() {
        const browserScreenshot = document.getElementById('browser-screenshot');
        if (!browserScreenshot) {
            console.error('Browser screenshot element not found');
            return;
        }

        // Add a timestamp to prevent caching
        const timestamp = new Date().getTime();
        browserScreenshot.src = `/api/live-browser/screenshot?t=${timestamp}`;

        // Update the current URL display
        if (liveBrowserCurrentUrl) {
            if (browserState.currentUrl && browserState.currentUrl !== 'about:blank') {
                liveBrowserCurrentUrl.textContent = browserState.currentUrl;
            } else {
                // If no URL or about:blank, use Google as default
                browserState.currentUrl = 'https://www.google.com';
                liveBrowserCurrentUrl.textContent = 'https://www.google.com';
            }
        }
    }

    // Navigate to URL (now using screenshots instead of iframe)
    function navigateIframe(url) {
        console.log('Navigating to:', url);
        browserState.isLoading = true;
        updateBrowserUI();

        // Ensure URL has protocol
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            url = 'https://' + url;
        }

        // Make sure the browser placeholder is hidden
        if (browserPlaceholder) {
            browserPlaceholder.classList.add('hidden');
        }

        // Make sure the screenshot display is visible
        const screenshotDisplay = document.getElementById('screenshot-display');
        if (screenshotDisplay) {
            screenshotDisplay.classList.remove('hidden');
        }

        // Hide the iframe if it exists
        if (browserFrame) {
            browserFrame.classList.add('hidden');
        }

        // Update current URL in state
        browserState.currentUrl = url;
        if (liveBrowserCurrentUrl) {
            liveBrowserCurrentUrl.textContent = url;
        }

        // Update the screenshot after a short delay to allow navigation to complete
        setTimeout(updateScreenshot, 1000);

        // Set loading state to false after a delay
        setTimeout(function() {
            browserState.isLoading = false;
            updateBrowserUI();
        }, 2000);
    }

    // Show error message
    function showErrorMessage(message) {
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'p-4 bg-red-100 text-red-800 text-center rounded';
        errorDiv.innerHTML = `
            <h3 class="text-lg font-bold mb-2">Error</h3>
            <p class="mb-2">${message}</p>
            <button id="error-retry-btn" class="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
                Retry
            </button>
        `;

        // Clear the iframe container and append the message
        if (browserFrame && browserFrame.parentElement) {
            browserFrame.classList.add('hidden');
            browserFrame.parentElement.appendChild(errorDiv);

            // Store reference to the error div for later removal
            browserState.errorDiv = errorDiv;

            // Add event listener to the retry button
            const retryBtn = errorDiv.querySelector('#error-retry-btn');
            if (retryBtn) {
                retryBtn.addEventListener('click', function() {
                    // Remove the error message
                    if (browserState.errorDiv && browserState.errorDiv.parentElement) {
                        browserState.errorDiv.parentElement.removeChild(browserState.errorDiv);
                        browserState.errorDiv = null;
                    }

                    // Show the iframe
                    browserFrame.classList.remove('hidden');

                    // Retry navigation
                    navigateIframe(browserState.currentUrl || 'https://www.google.com');
                });
            }
        }
    }

    // Listen for messages from the Chrome simulation iframe
    window.addEventListener('message', function(event) {
        // Check if the message is from our iframe
        if (browserFrame && event.source === browserFrame.contentWindow) {
            const data = event.data;

            // Handle different message types
            switch (data.type) {
                case 'navigation_complete':
                    console.log('Navigation complete:', data.url);
                    browserState.isLoading = false;
                    browserState.currentUrl = data.url;
                    if (liveBrowserCurrentUrl) {
                        liveBrowserCurrentUrl.textContent = data.url;
                    }
                    updateBrowserUI();
                    break;

                case 'screenshot_update':
                    console.log('Screenshot updated:', data.screenshot);
                    break;

                case 'error':
                    console.error('Error from Chrome simulation:', data.message);
                    showErrorMessage(data.message);
                    break;

                default:
                    console.log('Unknown message from Chrome simulation:', data);
            }
        }
    });

    // Start browser
    if (liveBrowserStart) {
        liveBrowserStart.addEventListener('click', function() {
            console.log('Start browser clicked');
            browserState.isLoading = true;
            updateBrowserUI();

            fetch('/api/live-browser/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    browserState.isLoading = false;

                    if (data.success) {
                        console.log('Browser started successfully');
                        browserState.isRunning = true;
                        updateBrowserUI();

                        // Navigate to Google as default
                        navigateIframe('https://www.google.com');
                        browserState.currentUrl = 'https://www.google.com';
                        if (liveBrowserCurrentUrl) liveBrowserCurrentUrl.textContent = 'https://www.google.com';

                        // Start the screenshot timer
                        startScreenshotTimer();
                    } else {
                        console.error('Error starting browser:', data.error);
                        alert('Error starting browser: ' + data.error);
                    }
                })
                .catch(error => {
                    browserState.isLoading = false;
                    updateBrowserUI();
                    console.error('Error starting browser:', error);
                    alert('Error starting browser: ' + error.message);
                });
        });
    }

    // Stop browser
    if (liveBrowserStop) {
        liveBrowserStop.addEventListener('click', function() {
            console.log('Stop browser clicked');
            browserState.isLoading = true;
            updateBrowserUI();

            fetch('/api/live-browser/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    browserState.isLoading = false;

                    if (data.success) {
                        console.log('Browser stopped successfully');
                        browserState.isRunning = false;
                        browserState.currentUrl = null;
                        if (browserFrame) browserFrame.src = 'about:blank';

                        // Stop the screenshot timer
                        stopScreenshotTimer();

                        updateBrowserUI();
                    } else {
                        console.error('Error stopping browser:', data.error);
                        alert('Error stopping browser: ' + data.error);
                    }
                })
                .catch(error => {
                    browserState.isLoading = false;
                    updateBrowserUI();
                    console.error('Error stopping browser:', error);
                    alert('Error stopping browser: ' + error.message);
                });
        });
    }

    // Navigate to URL
    if (liveBrowserNavigate) {
        liveBrowserNavigate.addEventListener('click', function() {
            if (!liveBrowserUrl) return;

            const url = liveBrowserUrl.value.trim();
            if (!url) {
                alert('Please enter a URL');
                return;
            }

            console.log('Navigate to URL clicked:', url);
            browserState.isLoading = true;
            updateBrowserUI();

            // First ensure browser is running
            ensureBrowserRunning()
                .then(running => {
                    if (!running) {
                        throw new Error('Browser is not running. Please start the browser first.');
                    }

                    // Then navigate to URL
                    return fetch('/api/live-browser/navigate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            url: url
                        })
                    });
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Navigation successful');
                        // Update iframe directly for immediate feedback
                        navigateIframe(url);
                        browserState.currentUrl = url;
                        if (liveBrowserCurrentUrl) liveBrowserCurrentUrl.textContent = url;

                        // No need for fallback to visual browser API since we removed it
                    } else {
                        // Just use the direct iframe navigation as fallback
                        console.log('Primary navigation failed, using direct iframe navigation');
                        navigateIframe(url);
                        browserState.currentUrl = url;
                        if (liveBrowserCurrentUrl) liveBrowserCurrentUrl.textContent = url;
                    }
                })
                .catch(error => {
                    browserState.isLoading = false;
                    updateBrowserUI();
                    console.error('Error navigating to URL:', error);

                    // If there's an error, check browser status
                    checkBrowserStatus();

                    // Try one more approach - update the iframe directly
                    try {
                        console.log('Attempting direct iframe navigation as last resort');
                        navigateIframe(url);
                        browserState.currentUrl = url;
                        if (liveBrowserCurrentUrl) liveBrowserCurrentUrl.textContent = url;
                    } catch (iframeError) {
                        console.error('Direct iframe navigation also failed:', iframeError);
                        // Show error message
                        alert('Error navigating to URL: ' + error.message);
                    }
                });
        });
    }

    // Helper function to ensure browser is running
    function ensureBrowserRunning() {
        return new Promise((resolve, reject) => {
            if (browserState.isRunning) {
                resolve(true);
                return;
            }

            console.log('Browser not running, attempting to start...');

            fetch('/api/live-browser/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Browser started successfully');
                        browserState.isRunning = true;

                        // Set Google as default URL
                        browserState.currentUrl = 'https://www.google.com';
                        if (liveBrowserCurrentUrl) liveBrowserCurrentUrl.textContent = 'https://www.google.com';

                        updateBrowserUI();
                        resolve(true);
                    } else {
                        console.error('Error starting browser:', data.error);
                        resolve(false);
                    }
                })
                .catch(error => {
                    console.error('Error starting browser:', error);
                    resolve(false);
                });
        });
    }

    // URL input enter key handler
    if (liveBrowserUrl) {
        liveBrowserUrl.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && liveBrowserNavigate) {
                liveBrowserNavigate.click();
            }
        });
    }

    // Execute task
    if (liveBrowserExecuteTask) {
        liveBrowserExecuteTask.addEventListener('click', function() {
            if (!liveBrowserTask) return;

            const task = liveBrowserTask.value.trim();
            if (!task) {
                alert('Please enter a task');
                return;
            }

            console.log('Execute task clicked:', task);

            // Show progress container
            if (liveBrowserProgress) {
                liveBrowserProgress.classList.remove('hidden');
            }

            if (liveBrowserProgressText) {
                liveBrowserProgressText.textContent = 'Processing task: ' + task + '\n\nConnecting to AI agent...';
            }

            browserState.taskInProgress = true;

            // First ensure browser is running
            ensureBrowserRunning()
                .then(running => {
                    if (!running) {
                        throw new Error('Browser is not running. Please start the browser first.');
                    }

                    // Send task to backend
                    return fetch('/api/live-browser/execute-task', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            task_type: 'autonomous',
                            task_data: {
                                task: task
                            }
                        })
                    });
                })
                .catch(error => {
                    console.error('Error ensuring browser is running:', error);
                    if (liveBrowserProgressText) {
                        liveBrowserProgressText.textContent += '\n\nError: ' + error.message;
                        liveBrowserProgressText.scrollTop = liveBrowserProgressText.scrollHeight;
                    }
                    browserState.taskInProgress = false;
                    return Promise.reject(error);
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Task submitted successfully');
                        if (liveBrowserProgressText) {
                            liveBrowserProgressText.textContent += '\n\nTask submitted successfully. The browser is now executing your task.';
                        }

                        // If we have a task_id, poll for updates
                        if (data.task_id) {
                            if (liveBrowserProgressText) {
                                liveBrowserProgressText.textContent += `\n\nTask ID: ${data.task_id}`;
                            }
                            pollTaskStatus(data.task_id, task);
                        } else {
                            // Handle immediate response (old API)
                            handleTaskResult(data);
                        }
                    } else {
                        console.error('Error executing task:', data.error);
                        if (liveBrowserProgressText) {
                            liveBrowserProgressText.textContent += '\n\nError: ' + (data.error || 'Unknown error');
                            // Auto-scroll to bottom
                            liveBrowserProgressText.scrollTop = liveBrowserProgressText.scrollHeight;
                        }

                        browserState.taskInProgress = false;
                        updateBrowserUI();
                    }
                })
                .catch(error => {
                    console.error('Error executing task:', error);
                    if (liveBrowserProgressText) {
                        liveBrowserProgressText.textContent += '\n\nError: ' + error.message;
                        // Auto-scroll to bottom
                        liveBrowserProgressText.scrollTop = liveBrowserProgressText.scrollHeight;
                    }

                    browserState.taskInProgress = false;
                });
        });
    }

    // Browser navigation buttons
    const browserBack = document.getElementById('browser-back');
    const browserForward = document.getElementById('browser-forward');
    const browserRefresh = document.getElementById('browser-refresh');
    const browserFullscreen = document.getElementById('browser-fullscreen');

    if (browserBack) {
        browserBack.addEventListener('click', function() {
            if (!browserState.isRunning || !browserFrame) return;
            try {
                browserFrame.contentWindow.history.back();
            } catch (e) {
                console.error('Error navigating back:', e);
            }
        });
    }

    if (browserForward) {
        browserForward.addEventListener('click', function() {
            if (!browserState.isRunning || !browserFrame) return;
            try {
                browserFrame.contentWindow.history.forward();
            } catch (e) {
                console.error('Error navigating forward:', e);
            }
        });
    }

    if (browserRefresh) {
        browserRefresh.addEventListener('click', function() {
            if (!browserState.isRunning || !browserFrame) return;
            try {
                browserFrame.contentWindow.location.reload();
            } catch (e) {
                console.error('Error refreshing:', e);
            }
        });
    }

    if (browserFullscreen) {
        browserFullscreen.addEventListener('click', function() {
            if (!browserState.isRunning || !browserFrame) return;

            try {
                if (browserFrame.requestFullscreen) {
                    browserFrame.requestFullscreen();
                } else if (browserFrame.webkitRequestFullscreen) {
                    browserFrame.webkitRequestFullscreen();
                } else if (browserFrame.msRequestFullscreen) {
                    browserFrame.msRequestFullscreen();
                }
            } catch (e) {
                console.error('Error entering fullscreen:', e);
            }
        });
    }

    // Handle iframe load events
    if (browserFrame) {
        browserFrame.addEventListener('load', function() {
            console.log('Iframe loaded event');
            browserState.isLoading = false;
            updateBrowserUI();

            // Update URL display
            try {
                const currentUrl = browserFrame.contentWindow.location.href;
                if (currentUrl !== 'about:blank') {
                    browserState.currentUrl = currentUrl;
                    if (liveBrowserCurrentUrl) {
                        liveBrowserCurrentUrl.textContent = currentUrl;
                    }
                } else {
                    // If about:blank, use Google as default
                    if (!browserState.currentUrl || browserState.currentUrl === 'about:blank') {
                        browserState.currentUrl = 'https://www.google.com';
                        if (liveBrowserCurrentUrl) {
                            liveBrowserCurrentUrl.textContent = 'https://www.google.com';
                        }
                    }
                }
            } catch (e) {
                // Cross-origin restrictions may prevent access
                console.log('Could not access iframe location due to security restrictions');

                // Ensure we have a valid URL displayed
                if (!browserState.currentUrl || browserState.currentUrl === 'about:blank') {
                    browserState.currentUrl = 'https://www.google.com';
                    if (liveBrowserCurrentUrl) {
                        liveBrowserCurrentUrl.textContent = 'https://www.google.com';
                    }
                }
            }
        });
    }

    // Poll for task status
    function pollTaskStatus(taskId, originalTask) {
        console.log(`Polling for task status: ${taskId}`);

        // Function to check task status
        function checkTaskStatus() {
            fetch(`/api/live-browser/task-status/${taskId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update progress
                    if (data.progress && data.progress.length > 0 && liveBrowserProgressText) {
                        // Clear existing progress text and add new progress
                        let progressText = `Processing task: ${originalTask}\n\nTask submitted successfully. The browser is now executing your task.\n\nTask ID: ${taskId}\n\nProgress:`;

                        data.progress.forEach(progress => {
                            progressText += `\n- ${progress.message}`;
                        });

                        liveBrowserProgressText.textContent = progressText;

                        // Auto-scroll to bottom
                        liveBrowserProgressText.scrollTop = liveBrowserProgressText.scrollHeight;
                    }

                    // Check if task is completed
                    if (data.status === 'completed') {
                        console.log('Task completed');

                        // Handle the result
                        if (data.result) {
                            handleTaskResult(data.result);
                        } else if (liveBrowserProgressText) {
                            liveBrowserProgressText.textContent += '\n\nTask completed, but no result was returned.';
                            browserState.taskInProgress = false;
                            updateBrowserUI();
                        }

                        return; // Stop polling
                    } else if (data.status === 'error') {
                        console.log('Task failed');

                        if (liveBrowserProgressText) {
                            liveBrowserProgressText.textContent += '\n\nTask failed: ' + (data.result?.error || 'Unknown error');
                            browserState.taskInProgress = false;
                            updateBrowserUI();
                        }

                        return; // Stop polling
                    }

                    // Continue polling if task is still in progress
                    setTimeout(checkTaskStatus, 1000);
                } else if (liveBrowserProgressText) {
                    liveBrowserProgressText.textContent += '\n\nError checking task status: ' + (data.error || 'Unknown error');
                    browserState.taskInProgress = false;
                    updateBrowserUI();
                    console.error('Error checking task status:', data.error);
                }
            })
            .catch(error => {
                if (liveBrowserProgressText) {
                    liveBrowserProgressText.textContent += '\n\nError checking task status: ' + error.message;
                    browserState.taskInProgress = false;
                    updateBrowserUI();
                }
                console.error('Error checking task status:', error);
            });
        }

        // Start polling
        checkTaskStatus();
    }

    // Handle task result
    function handleTaskResult(result) {
        console.log('Handling task result:', result);

        if (!liveBrowserProgressText) return;

        // Update with task result
        if (result.message) {
            liveBrowserProgressText.textContent += '\n\n' + result.message;
        }

        // Display execution log if available
        if (result.execution_log && result.execution_log.length > 0) {
            liveBrowserProgressText.textContent += '\n\nStep-by-step execution:';

            result.execution_log.forEach((step, index) => {
                const stepNumber = index + 1;
                const action = step.action || 'unknown';
                const success = step.success ? 'Success' : 'Failed';
                const message = step.message || '';

                liveBrowserProgressText.textContent += `\n\nStep ${stepNumber}: ${action} - ${success}`;
                if (message) {
                    liveBrowserProgressText.textContent += `\n${message}`;
                }
            });
        }

        // Mark task as complete
        liveBrowserProgressText.textContent += '\n\nTask execution completed!';
        browserState.taskInProgress = false;
        updateBrowserUI();

        // Auto-scroll to bottom
        liveBrowserProgressText.scrollTop = liveBrowserProgressText.scrollHeight;

        // Check browser status to update UI
        checkBrowserStatus();

        // Clear the task input
        if (liveBrowserTask) {
            liveBrowserTask.value = '';
        }
    }

    // Set up a timer to update screenshots regularly
    let screenshotTimer = null;

    function startScreenshotTimer() {
        // Clear existing timer if any
        if (screenshotTimer) {
            clearInterval(screenshotTimer);
        }

        // Set up a new timer to update screenshots every 500ms
        screenshotTimer = setInterval(updateScreenshot, 500);
        console.log('Screenshot timer started');
    }

    function stopScreenshotTimer() {
        // Clear the timer
        if (screenshotTimer) {
            clearInterval(screenshotTimer);
            screenshotTimer = null;
            console.log('Screenshot timer stopped');
        }
    }

    // Check status periodically
    setInterval(checkBrowserStatus, 5000);

    // Initial status check and UI update
    checkBrowserStatus();
    updateBrowserUI();

    console.log('Live Browser JS initialization complete');
});
