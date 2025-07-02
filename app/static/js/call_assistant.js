/**
 * Call Assistant JavaScript
 * Handles the call assistant functionality including phone calls and knowledge base management
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const phoneDisplay = document.getElementById('phoneDisplay');
    const callStatus = document.getElementById('callStatus');
    const callTimer = document.getElementById('callTimer');
    const callButton = document.getElementById('callButton');
    const muteButton = document.getElementById('muteButton');
    const speakerButton = document.getElementById('speakerButton');
    const callTranscript = document.getElementById('callTranscript');
    const knowledgeItems = document.getElementById('knowledgeItems');
    const newKnowledgeItem = document.getElementById('newKnowledgeItem');
    const addKnowledgeButton = document.getElementById('addKnowledgeButton');
    const phoneNumberInput = document.getElementById('phoneNumberInput');
    const callLogsList = document.getElementById('callLogsList');
    const clearLogsButton = document.getElementById('clearLogsButton');

    // State variables
    let isCallActive = false;
    let isMuted = false;
    let isSpeakerOn = false;
    let callDuration = 0;
    let callTimerInterval;
    let currentPhoneNumber = '+1 (555) 123-4567';
    let callSessionId = null;
    let callLogs = [];

    // Load knowledge base from server
    loadKnowledgeBase();

    // Load call logs from localStorage
    loadCallLogs();

    // Event Listeners
    callButton.addEventListener('click', toggleCall);
    muteButton.addEventListener('click', toggleMute);
    speakerButton.addEventListener('click', toggleSpeaker);
    addKnowledgeButton.addEventListener('click', addKnowledgeItem);
    newKnowledgeItem.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addKnowledgeItem();
        }
    });

    // Phone number input event listener
    phoneNumberInput.addEventListener('input', function() {
        currentPhoneNumber = this.value;
        phoneDisplay.textContent = currentPhoneNumber;
    });

    // Add Enter key support for phone number input
    phoneNumberInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !isCallActive) {
            toggleCall();
        }
    });

    // Call logs event listeners
    clearLogsButton.addEventListener('click', clearCallLogs);

    /**
     * Toggle call state (start/end call)
     */
    function toggleCall() {
        if (!isCallActive) {
            // Update the current phone number from the input field
            currentPhoneNumber = phoneNumberInput.value;
            phoneDisplay.textContent = currentPhoneNumber;

            // Start call
            startCall();
        } else {
            // End call
            endCall();
        }
    }

    /**
     * Start a call
     */
    function startCall() {
        isCallActive = true;
        callButton.classList.add('active');
        callStatus.textContent = 'Connecting...';
        callTimer.classList.remove('hidden');

        // Enable controls
        muteButton.classList.remove('disabled');
        speakerButton.classList.remove('disabled');

        // Start call timer
        callDuration = 0;
        updateCallTimer();
        callTimerInterval = setInterval(updateCallTimer, 1000);

        // Show call transcript
        callTranscript.classList.remove('hidden');
        callTranscript.innerHTML = '';

        // Create call log entry
        const callStartTime = new Date();
        const callLogEntry = {
            id: Date.now().toString(),
            phoneNumber: currentPhoneNumber,
            startTime: callStartTime.toISOString(),
            endTime: null,
            duration: 0,
            status: 'active'
        };

        // Make API call to start call
        fetch('/api/call-assistant/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone_number: currentPhoneNumber
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                callSessionId = data.session_id;
                callStatus.textContent = 'Connected';

                // Update call log entry
                callLogEntry.sessionId = data.session_id;

                // Store voice synthesis and phone call status
                const voiceSynthesisEnabled = data.voice_synthesis_enabled || false;
                const phoneCallEnabled = data.phone_call_enabled || false;

                // Update UI based on capabilities
                if (voiceSynthesisEnabled) {
                    addSystemMessage("Voice synthesis is enabled");
                }

                if (phoneCallEnabled) {
                    addSystemMessage("Phone call functionality is enabled");
                    if (data.call_sid) {
                        addSystemMessage(`Call initiated with ID: ${data.call_sid}`);
                        callLogEntry.callSid = data.call_sid;
                    }
                }

                // Add initial AI message with audio if available
                addAIMessage(
                    data.initial_message || "Hello, thank you for calling customer service. How can I help you today?",
                    data.audio_url
                );

                // Save call log entry to state
                callLogs.unshift(callLogEntry);
                saveCallLogs();
                updateCallLogsList();
            } else {
                // Update call log entry with error
                callLogEntry.status = 'failed';
                callLogEntry.endTime = new Date().toISOString();
                callLogs.unshift(callLogEntry);
                saveCallLogs();
                updateCallLogsList();

                endCall();
                alert('Failed to start call: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error starting call:', error);

            // Update call log entry with error
            callLogEntry.status = 'failed';
            callLogEntry.endTime = new Date().toISOString();
            callLogs.unshift(callLogEntry);
            saveCallLogs();
            updateCallLogsList();

            endCall();
            alert('Failed to start call. Please try again.');
        });
    }

    /**
     * End the current call
     */
    function endCall() {
        if (!isCallActive) return;

        isCallActive = false;
        callButton.classList.remove('active');
        callStatus.textContent = 'Ending call...';

        // Disable controls
        muteButton.classList.add('disabled');
        speakerButton.classList.add('disabled');

        // Stop call timer
        clearInterval(callTimerInterval);

        // Reset mute and speaker
        isMuted = false;
        isSpeakerOn = false;
        muteButton.style.backgroundColor = '';
        speakerButton.style.backgroundColor = '';

        // Update call log entry
        const callEndTime = new Date();
        const activeCallLog = callLogs.find(log => log.sessionId === callSessionId && log.status === 'active');

        if (activeCallLog) {
            activeCallLog.endTime = callEndTime.toISOString();
            activeCallLog.duration = callDuration;
            activeCallLog.status = 'completed';
            saveCallLogs();
            updateCallLogsList();
        }

        // Make API call to end call
        if (callSessionId) {
            fetch('/api/call-assistant/end', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: callSessionId
                })
            })
            .then(response => response.json())
            .then(data => {
                callStatus.textContent = 'Call ended';

                // Add final AI message if provided
                if (data.final_message) {
                    addAIMessage(data.final_message);
                } else {
                    addAIMessage("Thank you for calling. Is there anything else I can help you with before you go?");
                }

                // Reset call session
                callSessionId = null;

                // Reset call status after delay
                setTimeout(() => {
                    callStatus.textContent = 'Ready to call';
                    callTimer.classList.add('hidden');
                }, 3000);
            })
            .catch(error => {
                console.error('Error ending call:', error);
                callStatus.textContent = 'Call ended with errors';
                callSessionId = null;

                // Update call log status if there was an error
                if (activeCallLog) {
                    activeCallLog.status = 'error';
                    saveCallLogs();
                    updateCallLogsList();
                }

                // Reset call status after delay
                setTimeout(() => {
                    callStatus.textContent = 'Ready to call';
                    callTimer.classList.add('hidden');
                }, 3000);
            });
        } else {
            callStatus.textContent = 'Call ended';
            setTimeout(() => {
                callStatus.textContent = 'Ready to call';
                callTimer.classList.add('hidden');
            }, 3000);
        }
    }

    /**
     * Toggle mute state
     */
    function toggleMute() {
        if (!isCallActive || muteButton.classList.contains('disabled')) return;

        isMuted = !isMuted;

        if (isMuted) {
            muteButton.style.backgroundColor = '#F44336';
            addSystemMessage("Your microphone is muted");
        } else {
            muteButton.style.backgroundColor = '';
            addSystemMessage("Your microphone is unmuted");
        }
    }

    /**
     * Toggle speaker state
     */
    function toggleSpeaker() {
        if (!isCallActive || speakerButton.classList.contains('disabled')) return;

        isSpeakerOn = !isSpeakerOn;

        if (isSpeakerOn) {
            speakerButton.style.backgroundColor = '#4CAF50';
            addSystemMessage("Speaker is on");
        } else {
            speakerButton.style.backgroundColor = '';
            addSystemMessage("Speaker is off");
        }
    }

    /**
     * Update the call timer display
     */
    function updateCallTimer() {
        callDuration++;
        const minutes = Math.floor(callDuration / 60).toString().padStart(2, '0');
        const seconds = (callDuration % 60).toString().padStart(2, '0');
        callTimer.textContent = `${minutes}:${seconds}`;
    }

    /**
     * Add a message from the AI to the call transcript
     * @param {string} message - The message text
     * @param {string} audioUrl - Optional URL to audio file for voice synthesis
     */
    function addAIMessage(message, audioUrl) {
        // Create typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = `
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        `;
        callTranscript.appendChild(typingIndicator);

        // Scroll to bottom
        callTranscript.scrollTop = callTranscript.scrollHeight;

        // Simulate typing delay
        setTimeout(() => {
            // Remove typing indicator
            callTranscript.removeChild(typingIndicator);

            // Add actual message
            const messageElement = document.createElement('div');
            messageElement.className = 'transcript-message ai';
            messageElement.textContent = message;

            // If audio URL is provided, add audio player
            if (audioUrl) {
                const audioElement = document.createElement('audio');
                audioElement.controls = true;
                audioElement.style.marginTop = '8px';
                audioElement.style.width = '100%';
                audioElement.style.height = '30px';

                // Create source element
                const sourceElement = document.createElement('source');
                sourceElement.src = audioUrl;
                sourceElement.type = 'audio/mpeg';

                // Add fallback text
                audioElement.textContent = 'Your browser does not support the audio element.';

                // Append source to audio element
                audioElement.appendChild(sourceElement);

                // Create a container for the message and audio
                const containerElement = document.createElement('div');
                containerElement.className = 'transcript-message ai';
                containerElement.appendChild(document.createTextNode(message));
                containerElement.appendChild(document.createElement('br'));
                containerElement.appendChild(audioElement);

                // Add to transcript
                callTranscript.appendChild(containerElement);

                // Auto-play audio if speaker is on
                if (isSpeakerOn) {
                    audioElement.play().catch(error => {
                        console.error('Error playing audio:', error);
                    });
                }
            } else {
                // No audio, just add the text message
                callTranscript.appendChild(messageElement);
            }

            // Scroll to bottom
            callTranscript.scrollTop = callTranscript.scrollHeight;
        }, 1500);
    }

    /**
     * Add a user message to the call transcript
     * @param {string} message - The message text
     */
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'transcript-message user';
        messageElement.textContent = message;
        callTranscript.appendChild(messageElement);

        // Scroll to bottom
        callTranscript.scrollTop = callTranscript.scrollHeight;

        // Send message to API
        if (callSessionId) {
            fetch('/api/call-assistant/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: callSessionId,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.response) {
                    // Add AI message with audio if available
                    addAIMessage(data.response, data.audio_url);
                }
            })
            .catch(error => console.error('Error sending message:', error));
        }
    }

    /**
     * Add a system message to the call transcript
     * @param {string} message - The message text
     */
    function addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'transcript-message system';
        messageElement.textContent = message;
        messageElement.style.color = '#888';
        messageElement.style.fontStyle = 'italic';
        messageElement.style.textAlign = 'center';
        messageElement.style.backgroundColor = 'transparent';
        callTranscript.appendChild(messageElement);

        // Scroll to bottom
        callTranscript.scrollTop = callTranscript.scrollHeight;
    }

    /**
     * Add a new item to the knowledge base
     */
    function addKnowledgeItem() {
        const text = newKnowledgeItem.value.trim();
        if (!text) return;

        // Make API call to add knowledge item
        fetch('/api/call-assistant/knowledge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add to UI
                addKnowledgeItemToUI({
                    id: data.id,
                    text: text
                });

                // Clear input
                newKnowledgeItem.value = '';

                // Focus input
                newKnowledgeItem.focus();
            } else {
                alert('Failed to add knowledge item: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error adding knowledge item:', error);
            alert('Failed to add knowledge item. Please try again.');
        });
    }

    /**
     * Add a knowledge item to the UI
     * @param {Object} item - The knowledge item
     */
    function addKnowledgeItemToUI(item) {
        const itemElement = document.createElement('div');
        itemElement.className = 'knowledge-item';
        itemElement.dataset.id = item.id;

        itemElement.innerHTML = `
            <div class="knowledge-item-text">${item.text}</div>
            <div class="knowledge-item-actions">
                <button class="knowledge-item-button delete-button" title="Delete">🗑️</button>
            </div>
        `;

        // Add delete event listener
        const deleteButton = itemElement.querySelector('.delete-button');
        deleteButton.addEventListener('click', () => {
            deleteKnowledgeItem(item.id);
        });

        knowledgeItems.appendChild(itemElement);
    }

    /**
     * Delete a knowledge item
     * @param {string} id - The item ID
     */
    function deleteKnowledgeItem(id) {
        // Make API call to delete knowledge item
        fetch(`/api/call-assistant/knowledge/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove from UI
                const itemElement = knowledgeItems.querySelector(`.knowledge-item[data-id="${id}"]`);
                if (itemElement) {
                    knowledgeItems.removeChild(itemElement);
                }
            } else {
                alert('Failed to delete knowledge item: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error deleting knowledge item:', error);
            alert('Failed to delete knowledge item. Please try again.');
        });
    }

    /**
     * Load knowledge base from server
     */
    function loadKnowledgeBase() {
        fetch('/api/call-assistant/knowledge')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear existing items
                    knowledgeItems.innerHTML = '';

                    // Add items to UI
                    data.items.forEach(item => {
                        addKnowledgeItemToUI(item);
                    });
                } else {
                    console.error('Failed to load knowledge base:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading knowledge base:', error);
            });
    }



    /**
     * Load call logs from localStorage
     */
    function loadCallLogs() {
        const savedCallLogs = localStorage.getItem('callAssistantCallLogs');
        if (savedCallLogs) {
            callLogs = JSON.parse(savedCallLogs);
            updateCallLogsList();
        }
    }

    /**
     * Save call logs to localStorage
     */
    function saveCallLogs() {
        localStorage.setItem('callAssistantCallLogs', JSON.stringify(callLogs));
    }

    /**
     * Clear all call logs
     */
    function clearCallLogs() {
        if (confirm('Are you sure you want to clear all call logs?')) {
            callLogs = [];
            saveCallLogs();
            updateCallLogsList();
        }
    }

    /**
     * Update the call logs list in the UI
     */
    function updateCallLogsList() {
        // Clear existing logs
        callLogsList.innerHTML = '';

        if (callLogs.length === 0) {
            // Show empty state
            const emptyItem = document.createElement('div');
            emptyItem.className = 'call-log-item empty-logs';
            emptyItem.textContent = 'No call history yet';
            callLogsList.appendChild(emptyItem);
            return;
        }

        // Add logs to UI
        callLogs.forEach(log => {
            const logItem = document.createElement('div');
            logItem.className = 'call-log-item';
            logItem.dataset.id = log.id;

            // Format date
            const startDate = new Date(log.startTime);
            const formattedDate = startDate.toLocaleString();

            // Format duration
            let durationText = '';
            if (log.duration) {
                const minutes = Math.floor(log.duration / 60);
                const seconds = log.duration % 60;
                durationText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            } else {
                durationText = 'N/A';
            }

            // Status indicator
            let statusClass = '';
            switch (log.status) {
                case 'completed':
                    statusClass = 'text-green-500';
                    break;
                case 'failed':
                    statusClass = 'text-red-500';
                    break;
                case 'error':
                    statusClass = 'text-orange-500';
                    break;
                default:
                    statusClass = 'text-blue-500';
            }

            logItem.innerHTML = `
                <div class="call-log-info">
                    <div class="call-log-number">${log.phoneNumber}</div>
                    <div class="call-log-time">${formattedDate}</div>
                </div>
                <div class="call-log-duration ${statusClass}">${durationText}</div>
            `;

            // Add click event to redial
            logItem.addEventListener('click', () => {
                if (!isCallActive) {
                    phoneNumberInput.value = log.phoneNumber;
                    currentPhoneNumber = log.phoneNumber;
                    phoneDisplay.textContent = currentPhoneNumber;
                    startCall();
                }
            });

            callLogsList.appendChild(logItem);
        });
    }

    // For testing purposes - simulate user input
    window.simulateUserInput = function(message) {
        if (isCallActive && callSessionId) {
            addUserMessage(message);
        }
    };
});
