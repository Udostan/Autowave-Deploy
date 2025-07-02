// Simple Input JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple Input JS loaded');

    // Get elements
    const executeTaskBtn = document.getElementById('executeTaskBtn');
    const taskDescription = document.getElementById('taskDescription');
    const resultsContainer = document.getElementById('resultsContainer');
    const taskProgress = document.getElementById('taskProgress');
    const taskResults = document.getElementById('taskResults');
    const taskSummaryContainer = document.getElementById('taskSummaryContainer');
    const useAdvancedBrowser = document.getElementById('useAdvancedBrowser');
    const thinkingContent = document.getElementById('thinkingContent');
    const progressFill = document.getElementById('progressFill');
    const stepDescription = document.getElementById('stepDescription');
    const processingIndicator = document.getElementById('processingIndicator');

    // Initialize markdown-it
    const md = window.markdownit ? window.markdownit({
        html: true,
        breaks: true,
        linkify: true
    }) : null;

    if (!md) {
        console.error('markdown-it is not available');
    }

    // Execute Task button
    if (executeTaskBtn) {
        console.log('Execute Task button found');
        executeTaskBtn.addEventListener('click', function() {
            console.log('Execute Task button clicked');

            if (!taskDescription) {
                console.error('Task description element not found');
                return;
            }

            const description = taskDescription.value.trim();
            if (!description) {
                alert('Please enter a task description');
                return;
            }

            // Show results container with progress tracking
            if (resultsContainer) resultsContainer.classList.remove('hidden');
            if (taskProgress) taskProgress.classList.remove('hidden');
            if (taskSummaryContainer) taskSummaryContainer.classList.remove('hidden');

            // Start thinking process animation
            simulateThinking();

            // Disable button during request
            executeTaskBtn.disabled = true;
            executeTaskBtn.classList.add('opacity-50', 'cursor-not-allowed');
            executeTaskBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...`;

            // Prepare request data
            const requestData = {
                task_description: description,
                use_advanced_browser: useAdvancedBrowser ? useAdvancedBrowser.checked : true
            };

            console.log('Making API request with data:', requestData);

            // Make API request
            fetch('/api/super-agent/execute-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                console.log('API response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('API response data:', data);

                if (!taskResults) {
                    console.error('Task results element not found');
                    return;
                }

                if (data.error) {
                    // Display error
                    taskResults.innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
                            <div class="bg-red-50 px-6 py-4 border-b border-red-200">
                                <h3 class="text-lg font-semibold text-red-700 flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                    </svg>
                                    Error
                                </h3>
                            </div>
                            <div class="p-6 text-red-700">
                                ${data.error}
                            </div>
                        </div>
                    `;
                } else if (data.task_summary) {
                    // Display result from task_summary field
                    console.log('Found task_summary in response:', data.task_summary);

                    let formattedSummary = data.task_summary || '';
                    console.log('Original summary:', formattedSummary);

                    // Process the task summary as Markdown and convert it to HTML
                    let processedHtml = md.render(formattedSummary);
                    console.log('Rendered Markdown to HTML:', processedHtml.substring(0, 500));

                    // Extract screenshots and images from results
                    let screenshotsHtml = '';
                    let webImagesHtml = '';

                    if (data.results && Array.isArray(data.results)) {
                        // Process screenshots
                        const screenshots = [];
                        data.results.forEach(resultItem => {
                            if (resultItem.result && resultItem.result.screenshot) {
                                screenshots.push({
                                    screenshot: resultItem.result.screenshot,
                                    url: resultItem.result.url || '',
                                    title: resultItem.result.title || 'Screenshot'
                                });
                            }
                        });

                        if (screenshots.length > 0) {
                            screenshotsHtml = `
                                <div class="my-8 border-t border-gray-200 pt-6">
                                    <h2 class="text-2xl font-bold mb-4">Screenshots from Web Browsing</h2>
                                    <div class="grid grid-cols-1 gap-6">
                            `;

                            screenshots.forEach(screenshot => {
                                screenshotsHtml += `
                                    <div class="screenshot-container">
                                        <div class="flex justify-between items-center mb-2">
                                            <a href="${screenshot.url}" target="_blank" class="text-blue-600 hover:underline text-sm">${screenshot.title}</a>
                                            <div class="flex space-x-1">
                                                <button class="screenshot-zoom-btn text-gray-500 hover:text-gray-700"
                                                        data-screenshot="${screenshot.screenshot}"
                                                        data-screenshot-url=""
                                                        data-title="${screenshot.title}">
                                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"></path>
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                        <img src="data:image/png;base64,${screenshot.screenshot}" alt="${screenshot.title}" class="w-full rounded-md">
                                    </div>
                                `;
                            });

                            screenshotsHtml += `
                                    </div>
                                </div>
                            `;
                        }

                        // Process web images
                        const webImages = [];
                        data.results.forEach(resultItem => {
                            if (resultItem.result && resultItem.result.images && resultItem.result.images.length > 0) {
                                resultItem.result.images.forEach(img => {
                                    if (img.src) {
                                        webImages.push({
                                            src: img.src,
                                            alt: img.alt || 'Image from web',
                                            width: img.width,
                                            height: img.height,
                                            url: resultItem.result.url || '',
                                            title: resultItem.result.title || 'Web page'
                                        });
                                    }
                                });
                            }
                        });

                        if (webImages.length > 0) {
                            webImagesHtml = `
                                <div class="my-8 border-t border-gray-200 pt-6">
                                    <h2 class="text-2xl font-bold mb-4">Images from Web</h2>
                                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                            `;

                            webImages.forEach(image => {
                                webImagesHtml += `
                                    <div class="overflow-hidden rounded-lg border border-gray-200">
                                        <a href="${image.url}" target="_blank" class="block">
                                            <img src="${image.src}" alt="${image.alt}" class="w-full h-auto object-cover" style="max-height: 200px;">
                                            <div class="p-2 text-xs text-gray-500 truncate">${image.title}</div>
                                        </a>
                                    </div>
                                `;
                            });

                            webImagesHtml += `
                                    </div>
                                </div>
                            `;
                        }
                    }

                    // Create the task results HTML
                    const taskResultsHtml = `
                        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                            <div class="bg-gray-50 px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                                <h3 class="text-lg font-semibold text-gray-900 flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                    </svg>
                                    Task Summary
                                </h3>
                                <div class="flex space-x-2">
                                    <button id="downloadSummaryBtn" class="text-gray-500 hover:text-gray-700 focus:outline-none" title="Download as PDF">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                                        </svg>
                                    </button>
                                    <button id="copySummaryBtn" class="text-gray-500 hover:text-gray-700 focus:outline-none" title="Copy to Clipboard">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
                                        </svg>
                                    </button>
                                </div>
                            </div>
                            <div class="p-6 prose max-w-none overflow-y-scroll" style="height: 600px;">
                                <div class="html-content task-summary" style="overflow: visible;">
                                    ${processedHtml}
                                    ${screenshotsHtml}
                                    ${webImagesHtml}
                                </div>
                            </div>
                        </div>
                    `;

                    // Update the task results
                    taskResults.innerHTML = taskResultsHtml;

                    // Add event listeners for buttons
                    const downloadSummaryBtn = document.getElementById('downloadSummaryBtn');
                    const copySummaryBtn = document.getElementById('copySummaryBtn');

                    if (downloadSummaryBtn) {
                        downloadSummaryBtn.addEventListener('click', function() {
                            console.log('Download summary button clicked');
                            if (taskResults) {
                                // Create a blob from the HTML content
                                const htmlContent = taskResults.innerHTML;
                                const blob = new Blob([htmlContent], { type: 'text/html' });
                                const url = URL.createObjectURL(blob);

                                // Create a temporary link and trigger download
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = 'task_summary_' + new Date().toISOString().slice(0, 10) + '.html';
                                document.body.appendChild(a);
                                a.click();

                                // Clean up
                                setTimeout(() => {
                                    document.body.removeChild(a);
                                    URL.revokeObjectURL(url);
                                }, 100);
                            }
                        });
                    }

                    if (copySummaryBtn) {
                        copySummaryBtn.addEventListener('click', function() {
                            console.log('Copy summary button clicked');
                            if (taskResults) {
                                // Get the text content
                                const textContent = taskResults.innerText;

                                // Copy to clipboard
                                navigator.clipboard.writeText(textContent)
                                    .then(() => {
                                        // Show success message
                                        copySummaryBtn.classList.add('text-green-500');

                                        // Reset after 2 seconds
                                        setTimeout(() => {
                                            copySummaryBtn.classList.remove('text-green-500');
                                        }, 2000);
                                    })
                                    .catch(err => {
                                        console.error('Failed to copy text: ', err);
                                        alert('Failed to copy text to clipboard');
                                    });
                            }
                        });
                    }

                    // Add event listeners for screenshot zoom buttons
                    document.querySelectorAll('.screenshot-zoom-btn').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const screenshot = this.getAttribute('data-screenshot');
                            const title = this.getAttribute('data-title');

                            // Create a modal to display the full-size screenshot
                            const modal = document.createElement('div');
                            modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';

                            modal.innerHTML = `
                                <div class="relative bg-white rounded-lg overflow-hidden max-w-4xl max-h-screen">
                                    <div class="absolute top-0 right-0 p-4">
                                        <button class="text-gray-500 hover:text-gray-700 focus:outline-none close-modal-btn">
                                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                            </svg>
                                        </button>
                                    </div>
                                    <div class="p-4 overflow-auto" style="max-height: 90vh;">
                                        <img src="data:image/png;base64,${screenshot}" class="max-w-full h-auto" alt="${title || 'Full-size screenshot'}">
                                    </div>
                                </div>
                            `;

                            document.body.appendChild(modal);

                            // Add event listener to close the modal
                            modal.querySelector('.close-modal-btn').addEventListener('click', function() {
                                document.body.removeChild(modal);
                            });

                            // Close modal when clicking outside the image
                            modal.addEventListener('click', function(e) {
                                if (e.target === modal) {
                                    document.body.removeChild(modal);
                                }
                            });
                        });
                    });
                } else {
                    // Display a generic error message
                    taskResults.innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
                            <div class="bg-red-50 px-6 py-4 border-b border-red-200">
                                <h3 class="text-lg font-semibold text-red-700 flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                    </svg>
                                    Error
                                </h3>
                            </div>
                            <div class="p-6 text-red-700">
                                The server returned an unexpected response. Please try again or try a different task.
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error executing task:', error);

                if (taskResults) {
                    taskResults.innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
                            <div class="bg-red-50 px-6 py-4 border-b border-red-200">
                                <h3 class="text-lg font-semibold text-red-700 flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                    </svg>
                                    Error
                                </h3>
                            </div>
                            <div class="p-6 text-red-700">
                                Failed to execute task: ${error.message || 'Unknown error'}
                            </div>
                        </div>
                    `;
                }
            })
            .finally(() => {
                // Re-enable the button
                executeTaskBtn.disabled = false;
                executeTaskBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                executeTaskBtn.innerHTML = `
                    <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Execute Task`;

                // Update the processing indicator to show completion
                if (processingIndicator) {
                    processingIndicator.classList.add('completed');
                }

                // Clear thinking interval
                if (thinkingInterval) {
                    clearInterval(thinkingInterval);

                    // Add a completion message to the thinking process
                    if (thinkingContent) {
                        const completionP = document.createElement('div');
                        completionP.classList.add('text-green-600', 'mt-4', 'thinking-step');
                        completionP.innerHTML = '<strong>✓ Task completed!</strong>';
                        thinkingContent.appendChild(completionP);

                        // Scroll to bottom
                        const thinkingProcess = document.getElementById('thinkingProcess');
                        if (thinkingProcess) {
                            thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
                        }
                    }
                }
            });
        });
    } else {
        console.error('Execute Task button not found');
    }

    // Function to simulate thinking process
    let thinkingInterval = null;
    function simulateThinking() {
        if (!thinkingContent) return;

        // Clear previous content
        thinkingContent.innerHTML = '';

        // Generate thinking steps
        const thinkingSteps = [
            "I need to understand what you're asking for...",
            "Let me break down this task into steps:",
            "1. **Research**: I'll search for relevant information",
            "2. **Analyze**: I'll evaluate the sources and extract key details",
            "3. **Organize**: I'll structure the information in a clear format",
            "4. **Present**: I'll provide a comprehensive response with all requested elements",
            "Let me start by searching for the most reliable sources...",
            "I'll need to find official websites and authoritative information...",
            "Now I'll compile everything into a well-structured response..."
        ];

        let currentStep = 0;

        // Display thinking process step by step - faster animation
        thinkingInterval = setInterval(() => {
            if (currentStep >= thinkingSteps.length) {
                clearInterval(thinkingInterval);
                return;
            }

            // Add multiple steps at once for faster display
            const stepsToAddAtOnce = Math.min(3, thinkingSteps.length - currentStep);

            for (let i = 0; i < stepsToAddAtOnce; i++) {
                const p = document.createElement('div');
                p.className = 'thinking-step mb-2';

                // Use markdown-it if available
                if (md) {
                    p.innerHTML = md.render(thinkingSteps[currentStep + i]);
                } else {
                    p.textContent = thinkingSteps[currentStep + i];
                }

                thinkingContent.appendChild(p);
            }

            // Update progress bar
            if (progressFill) {
                const progress = ((currentStep + stepsToAddAtOnce) / thinkingSteps.length) * 100;
                progressFill.style.width = `${progress}%`;
            }

            // Update step description
            if (stepDescription) {
                stepDescription.textContent = `Processing task: ${Math.round((currentStep + stepsToAddAtOnce) / thinkingSteps.length * 100)}% complete`;
            }

            // Scroll to bottom
            const thinkingProcess = document.getElementById('thinkingProcess');
            if (thinkingProcess) {
                thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
            }

            currentStep += stepsToAddAtOnce;
        }, 300); // Much faster interval
    }
});
