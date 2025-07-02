// Super Agent JavaScript

document.addEventListener('DOMContentLoaded', function() {
    "use strict";
    console.log('Super Agent JS loaded');

    // Check if markdownit is available
    if (window.markdownit) {
        console.log('markdownit is available');
    } else {
        console.error('markdownit is NOT available - this will cause issues with rendering results');
    }

    // Check for task parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const taskParam = urlParams.get('task');
    if (taskParam) {
        console.log('Task parameter found in URL:', taskParam);
        // Set the task description field
        const taskDescription = document.getElementById('taskDescription');
        if (taskDescription) {
            taskDescription.value = taskParam;
            console.log('Task description field populated from URL parameter');

            // Auto-execute the task after a short delay
            setTimeout(() => {
                const executeTaskBtn = document.getElementById('executeTaskBtn');
                if (executeTaskBtn) {
                    console.log('Auto-executing task from URL parameter');
                    executeTaskBtn.click();
                }
            }, 500); // Short delay to ensure everything is loaded
        }
    }

    // Get elements
    const executeTaskBtn = document.getElementById('executeTaskBtn');
    const taskDescription = document.getElementById('taskDescription');
    const resultsContainer = document.getElementById('resultsContainer');
    const taskProgress = document.getElementById('taskProgress');
    const taskResults = document.getElementById('taskResults');
    const taskSummaryContainer = document.getElementById('taskSummaryContainer');
    const useBrowserUse = document.getElementById('useBrowserUse');
    const useAdvancedBrowser = document.getElementById('useAdvancedBrowser');
    const thinkingContent = document.getElementById('thinkingContent');

    // Modal elements
    const summaryModal = document.getElementById('summaryModal');
    const modalTaskResults = document.getElementById('modalTaskResults');
    const expandSummaryBtn = document.getElementById('expandSummaryBtn');
    const closeSummaryModal = document.getElementById('closeSummaryModal');
    const downloadSummaryBtn = document.getElementById('downloadSummaryBtn');
    const copySummaryBtn = document.getElementById('copySummaryBtn');

    // Thinking process variables
    let thinkingInterval = null;
    let thinkingSteps = [
        "I need to understand what the user is asking for...",
        "Let me break down this task into steps:",
        "1. **Research**: I'll need to search for relevant information",
        "2. **Analyze**: I'll evaluate the sources and extract key details",
        "3. **Organize**: I'll structure the information in a clear format",
        "4. **Present**: I'll provide a comprehensive response with all requested elements",
        "Let me start by searching for the most reliable sources...",
        "I'll need to find official websites and authoritative information...",
        "I should also look for high-quality images to include...",
        "Now I'll compile everything into a well-structured response..."
    ];

    // Function to generate thinking steps based on task description
    function generateThinkingSteps(taskDesc) {
        const lowerTaskDesc = taskDesc.toLowerCase();
        const customSteps = [
            `I need to understand what the user is asking about ${taskDesc.substring(0, 30)}...`,
            "Let me break down this task into steps:"
        ];

        // Add research step based on task type
        if (lowerTaskDesc.includes('compare') || lowerTaskDesc.includes('vs') || lowerTaskDesc.includes('versus')) {
            customSteps.push("1. **Research**: I'll gather information about all items to compare");
            customSteps.push("2. **Analyze**: I'll identify key comparison points and differences");
            customSteps.push("3. **Organize**: I'll create a structured comparison with pros and cons");
        } else if (lowerTaskDesc.includes('recipe') || lowerTaskDesc.includes('cook') || lowerTaskDesc.includes('food')) {
            customSteps.push("1. **Research**: I'll find authentic recipes from reliable sources");
            customSteps.push("2. **Analyze**: I'll identify key ingredients and preparation steps");
            customSteps.push("3. **Organize**: I'll structure the recipe in a clear, step-by-step format");
        } else if (lowerTaskDesc.includes('travel') || lowerTaskDesc.includes('vacation') || lowerTaskDesc.includes('trip') || lowerTaskDesc.includes('itinerary')) {
            customSteps.push("1. **Research**: I'll find information about destinations, attractions, and logistics");
            customSteps.push("2. **Analyze**: I'll evaluate options based on popularity, reviews, and accessibility");
            customSteps.push("3. **Organize**: I'll create a detailed itinerary with recommendations");
        } else if (lowerTaskDesc.includes('explain') || lowerTaskDesc.includes('how') || lowerTaskDesc.includes('what is')) {
            customSteps.push("1. **Research**: I'll gather authoritative information on this topic");
            customSteps.push("2. **Analyze**: I'll break down complex concepts into understandable parts");
            customSteps.push("3. **Organize**: I'll structure the explanation from basic to advanced");
        } else {
            customSteps.push("1. **Research**: I'll search for comprehensive information on this topic");
            customSteps.push("2. **Analyze**: I'll evaluate sources and extract key details");
            customSteps.push("3. **Organize**: I'll structure the information logically");
        }

        // Add common final steps
        customSteps.push("4. **Present**: I'll provide a comprehensive response with all requested elements");
        customSteps.push("Let me start by searching for the most reliable sources...");

        // Add task-specific search steps
        if (lowerTaskDesc.includes('image') || lowerTaskDesc.includes('picture') || lowerTaskDesc.includes('photo')) {
            customSteps.push("I'll prioritize finding high-quality images as requested...");
        }
        if (lowerTaskDesc.includes('website') || lowerTaskDesc.includes('link') || lowerTaskDesc.includes('url')) {
            customSteps.push("I'll make sure to include official websites and reliable links...");
        }

        customSteps.push("Now I'll compile everything into a well-structured response...");
        return customSteps;
    }

    // Function to simulate thinking process
    function simulateThinking() {
        if (!thinkingContent || !taskDescription) return;

        // Initialize markdown-it
        const md = window.markdownit ? window.markdownit() : null;
        if (!md) {
            console.error('markdown-it is not available');
        }

        // Generate custom thinking steps based on task description
        thinkingSteps = generateThinkingSteps(taskDescription.value.trim());

        // Clear previous content
        thinkingContent.innerHTML = '';
        let currentStep = 0;
        let currentWord = 0;
        let currentStepWords = [];
        let currentStepText = '';

        // Display thinking process word by word
        thinkingInterval = setInterval(() => {
            if (currentStep >= thinkingSteps.length) {
                clearInterval(thinkingInterval);
                return;
            }

            // Split current step into words if not already done
            if (currentStepWords.length === 0) {
                currentStepWords = thinkingSteps[currentStep].split(' ');
                currentStepText = '';
                // Add paragraph element for new step
                const p = document.createElement('div');
                p.className = 'thinking-step';
                thinkingContent.appendChild(p);
            }

            // Get current paragraph
            const currentP = thinkingContent.lastElementChild;

            // Add next word and update the full text
            currentStepText += currentStepWords[currentWord] + ' ';

            // Render the current step with markdown
            if (md) {
                currentP.innerHTML = md.render(currentStepText);
            } else {
                currentP.textContent = currentStepText;
            }

            // Add typing cursor at the end
            const cursor = document.createElement('span');
            cursor.className = 'typing-cursor';
            cursor.innerHTML = '&nbsp;';
            currentP.appendChild(cursor);

            // Move to next word
            currentWord++;

            // If reached end of current step, move to next step
            if (currentWord >= currentStepWords.length) {
                // Remove the cursor from the completed step
                if (cursor && cursor.parentNode) {
                    cursor.parentNode.removeChild(cursor);
                }

                currentStep++;
                currentWord = 0;
                currentStepWords = [];
            }

            // Scroll to bottom
            const thinkingProcess = document.getElementById('thinkingProcess');
            if (thinkingProcess) {
                thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
            }
        }, 100); // Adjust speed as needed
    }

    // Tab switching is now handled by tab_switcher.js

    // Test button code removed

    // Modal and button functionality
    if (expandSummaryBtn) {
        expandSummaryBtn.addEventListener('click', function() {
            console.log('Expand summary button clicked');

            // Find the summary container
            const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');

            if (summaryModal && summaryContainer) {
                // Get the modal content element
                const modalTaskResults = document.getElementById('modalTaskResults');

                if (modalTaskResults) {
                    // Copy content from summary container to modal
                    modalTaskResults.innerHTML = summaryContainer.innerHTML;

                    // Add animation class to modal
                    summaryModal.classList.add('animate-fade-in');

                    // Show modal with animation
                    summaryModal.classList.remove('hidden');

                    // Prevent scrolling on body
                    document.body.style.overflow = 'hidden';

                    console.log('Expanded summary to full screen');

                    // Add event listeners to any buttons in the modal
                    const modalButtons = modalTaskResults.querySelectorAll('button');
                    modalButtons.forEach(button => {
                        if (button.classList.contains('screenshot-zoom-btn')) {
                            button.addEventListener('click', function() {
                                // Handle zoom button click
                                // const screenshotData = this.getAttribute('data-screenshot');
                                // const screenshotUrlData = this.getAttribute('data-screenshot-url');
                                const titleData = this.getAttribute('data-title');

                                // Create zoom modal logic here
                                console.log('Zoom button clicked for:', titleData);
                            });
                        }

                        if (button.classList.contains('screenshot-download-btn')) {
                            button.addEventListener('click', function() {
                                // Handle download button click
                                // const screenshotData = this.getAttribute('data-screenshot');
                                const titleData = this.getAttribute('data-title');

                                // Download logic here
                                console.log('Download button clicked for:', titleData);
                            });
                        }
                    });

                    // Remove animation class after animation completes
                    setTimeout(() => {
                        summaryModal.classList.remove('animate-fade-in');
                    }, 500);
                }
            } else {
                console.error('Modal or summary container not found');
            }
        });
    }

    if (closeSummaryModal) {
        closeSummaryModal.addEventListener('click', function() {
            console.log('Close summary modal button clicked');
            if (summaryModal) {
                summaryModal.classList.add('hidden');
                // Restore scrolling on body
                document.body.style.overflow = '';
            }
        });
    }

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
                        const originalTitle = copySummaryBtn.getAttribute('title');
                        copySummaryBtn.setAttribute('title', 'Copied!');
                        copySummaryBtn.classList.add('text-green-500');

                        // Reset after 2 seconds
                        setTimeout(() => {
                            copySummaryBtn.setAttribute('title', originalTitle);
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

    // Close modal when clicking outside the content
    if (summaryModal) {
        summaryModal.addEventListener('click', function(e) {
            if (e.target === summaryModal) {
                summaryModal.classList.add('hidden');
                document.body.style.overflow = '';
            }
        });
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

            // Get the thinking icon
            const thinkingIcon = document.getElementById('thinkingIcon');
            if (thinkingIcon) {
                // Make sure the animation is running
                thinkingIcon.style.animation = 'spin 1.5s linear infinite';
            }

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
                use_browser_use: useBrowserUse ? useBrowserUse.checked : false,
                use_advanced_browser: useAdvancedBrowser ? useAdvancedBrowser.checked : true,  // Always use advanced browser
                use_simple_orchestrator: true  // Use simple orchestrator to ensure real-time data
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
                console.log('API response headers:', response.headers);
                return response.json();
            })
            .then(data => {
                console.log('API response data:', data);
                console.log('API response data type:', typeof data);
                console.log('API response data keys:', Object.keys(data));

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
                    // Initialize markdown-it with HTML enabled
                    const md = window.markdownit({
                        html: true,  // Enable HTML tags in source
                        breaks: true,  // Convert '\n' in paragraphs into <br>
                        linkify: true  // Autoconvert URL-like text to links
                    });
                    console.log('markdownit initialized with HTML enabled:', md);
                    let formattedSummary = data.task_summary || '';

                    // Always use the original summary without processing
                    console.log('Original summary:', formattedSummary);

                    // Process image placeholders
                    const imageRegex = /\[IMAGE: ([^\]]+)\]/g;
                    const imageMatches = [];

                    console.log('Processing image placeholders...');
                    let match;
                    while ((match = imageRegex.exec(formattedSummary)) !== null) {
                        imageMatches.push({
                            placeholder: match[0],
                            description: match[1]
                        });
                    }

                    // Check if we have screenshots from advanced browser
                    let screenshots = [];
                    let webImages = [];

                    console.log('Checking for screenshots and images in results:', data);

                    // Check if screenshots are directly in the data object
                    if (data.screenshots && Array.isArray(data.screenshots) && data.screenshots.length > 0) {
                        console.log(`Found ${data.screenshots.length} screenshots directly in data object`);
                        screenshots = data.screenshots;
                    }

                    // We'll use real data from the API response instead of hardcoded examples
                    if (data.results && Array.isArray(data.results)) {
                        // Extract screenshots and images from results
                        data.results.forEach((resultItem, idx) => {
                            console.log(`Checking result item ${idx}:`, resultItem);

                            if (resultItem.result && resultItem.result.screenshot) {
                                console.log(`Found screenshot in result ${idx}:`, resultItem.result.url);
                                screenshots.push({
                                    screenshot: resultItem.result.screenshot,
                                    url: resultItem.result.url || '',
                                    title: resultItem.result.title || 'Screenshot'
                                });
                            }

                            // Also collect actual images from the websites
                            if (resultItem.result && resultItem.result.images && resultItem.result.images.length > 0) {
                                console.log(`Found ${resultItem.result.images.length} images in result ${idx}`);
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
                    }

                    console.log(`Total screenshots: ${screenshots.length}, Total web images: ${webImages.length}`);

                    // Prepare HTML for screenshots section
                    let screenshotsHtml = '';
                    if (screenshots.length > 0) {
                        screenshotsHtml = `
                            <div class="screenshots-section mt-8">
                                <h3 class="text-xl font-semibold mb-4">Screenshots</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        `;

                        screenshots.forEach((screenshot, idx) => {
                            screenshotsHtml += `
                                <div class="screenshot-item bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                                    <div class="bg-gray-50 px-4 py-2 border-b border-gray-200 flex items-center justify-between">
                                        <h4 class="text-sm font-medium text-gray-700 truncate">${screenshot.title || 'Screenshot'}</h4>
                                        <div class="flex space-x-2">
                                            <button class="screenshot-zoom-btn text-blue-600 hover:text-blue-800"
                                                    data-screenshot="${screenshot.screenshot || ''}"
                                                    data-screenshot-url="${screenshot.url || ''}"
                                                    data-title="${screenshot.title || 'Screenshot'}"
                                                    title="Zoom">
                                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"></path>
                                                </svg>
                                            </button>
                                            <button class="screenshot-download-btn text-green-600 hover:text-green-800"
                                                    data-screenshot="${screenshot.screenshot || ''}"
                                                    data-title="${screenshot.title || 'Screenshot'}"
                                                    title="Download">
                                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                    <div class="p-4">
                                        <img src="data:image/png;base64,${screenshot.screenshot || ''}"
                                             alt="${screenshot.title || 'Screenshot'}"
                                             class="w-full h-auto rounded shadow-sm">
                                        <div class="mt-2 text-xs text-gray-500">
                                            <a href="${screenshot.url || '#'}" target="_blank" class="text-blue-600 hover:underline">${screenshot.url || 'No URL'}</a>
                                        </div>
                                    </div>
                                </div>
                            `;
                        });

                        screenshotsHtml += `
                                </div>
                            </div>
                        `;
                    }

                    // Prepare HTML for web images section
                    let webImagesHtml = '';
                    if (webImages.length > 0) {
                        webImagesHtml = `
                            <div class="web-images-section mt-8">
                                <h3 class="text-xl font-semibold mb-4">Images</h3>
                                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                        `;

                        webImages.forEach((image, idx) => {
                            webImagesHtml += `
                                <div class="image-item bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                                    <div class="p-2">
                                        <img src="${image.src}"
                                             alt="${image.alt || 'Image'}"
                                             class="w-full h-48 object-cover rounded">
                                        <div class="mt-2 text-xs text-gray-500 truncate">
                                            ${image.alt || 'Image from web'}
                                        </div>
                                    </div>
                                </div>
                            `;
                        });

                        webImagesHtml += `
                                </div>
                            </div>
                        `;
                    }

                    // Process the task summary as Markdown and convert it to HTML
                    console.log('Original summary with HTML:', formattedSummary.substring(0, 500));

                    // Define a function to update the task results
                    function updateTaskResults() {
                        console.log('Updating task results with real-time data...');
                        console.log('Using task summary from API response:', formattedSummary.substring(0, 200) + '...');

                        // We're now directly embedding the HTML for screenshots and images
                        // No need to process placeholders anymore
                        let processedSummary = formattedSummary;

                        // Use our markdown processor to render the content
                        let processedHtml = '';
                        if (window.markdownProcessor && window.markdownProcessor.renderMarkdown) {
                            processedHtml = window.markdownProcessor.renderMarkdown(processedSummary);
                            console.log('Used markdownProcessor to render HTML');
                        } else {
                            // Fallback to direct markdown-it if our processor is not available
                            const md = window.markdownit({
                                html: true,  // Enable HTML tags in source
                                breaks: true,  // Convert '\n' in paragraphs into <br>
                                linkify: true,  // Autoconvert URL-like text to links
                                typographer: true  // Enable some language-neutral replacement + quotes beautification
                            });
                            processedHtml = '<div class="task-summary">' + md.render(processedSummary) + '</div>';
                            console.log('Used fallback markdown-it to render HTML');
                        }

                        console.log('Rendered Markdown to HTML:', processedHtml.substring(0, 200) + '...');

                        // Update the initial summary container instead of creating a new one
                        const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');
                        if (summaryContainer) {
                            // Clear any existing content first to ensure we're not appending to old content
                            summaryContainer.innerHTML = '';

                            // Now add the new content
                            summaryContainer.innerHTML = `
                                <div class="html-content task-summary" style="overflow: visible;">
                                    ${processedHtml}

                                    <!-- Insert screenshots section -->
                                    ${screenshotsHtml || ''}

                                    <!-- Insert web images section -->
                                    ${webImagesHtml || ''}
                                </div>
                            `;

                            // Update the header to include the task description
                            const headerElement = document.querySelector('#summary-container-initial h4');
                            if (headerElement) {
                                // Make sure we use the actual task description from the input field
                                const taskDesc = document.getElementById('taskDescription');
                                const taskText = taskDesc ? taskDesc.value.trim() : description;
                                headerElement.textContent = 'Task Summary: ' + taskText;
                                console.log('Updated task summary header with: ' + taskText);
                            }

                            console.log('Updated summary container with real-time task results');
                        } else {
                            console.error('Could not find summary container to update');
                        }

                        // Also update the taskResults element for compatibility
                        if (taskResults) {
                            taskResults.innerHTML = processedHtml;
                            console.log('Also updated taskResults element for compatibility');
                        }
                    }

                    // Initial update
                    updateTaskResults();
                } else if (data.result && data.result.summary) {
                    // Handle old API response format
                    const md = window.markdownit();
                    const formattedSummary = md.render(data.result.summary || '');

                    // Update the initial summary container instead of creating a new one
                    const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');
                    if (summaryContainer) {
                        summaryContainer.innerHTML = formattedSummary;

                        // Update the header to include the task description
                        const headerElement = document.querySelector('#summary-container-initial h4');
                        if (headerElement) {
                            headerElement.textContent = 'Task Summary: ' + taskDescription.value.trim();
                        }

                        console.log('Updated summary container with task results');
                    } else {
                        console.error('Could not find summary container to update');
                    }
                } else {
                    // Fallback for unexpected response
                    const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');
                    if (summaryContainer) {
                        summaryContainer.innerHTML = `
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
                }
            })
            .catch(error => {
                console.error('Error executing task:', error);

                const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');
                if (summaryContainer) {
                    summaryContainer.innerHTML = `
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
                const processingIndicator = document.getElementById('processingIndicator');
                if (processingIndicator) {
                    processingIndicator.classList.add('completed');
                }

                // Clear thinking interval
                if (thinkingInterval) {
                    clearInterval(thinkingInterval);
                    thinkingInterval = null;

                    // Add a completion message to the thinking process
                    const thinkingContent = document.querySelector('.thinking-process');
                    if (thinkingContent) {
                        // Initialize markdown-it if not already done
                        const md = window.markdownit ? window.markdownit() : null;

                        const completionP = document.createElement('div');
                        completionP.classList.add('text-green-600', 'mt-4', 'thinking-step');

                        if (md) {
                            completionP.innerHTML = md.render('**✓ Task completed!**');
                        } else {
                            completionP.innerHTML = '<strong>✓ Task completed!</strong>';
                        }

                        thinkingContent.appendChild(completionP);

                        // Scroll to bottom
                        const thinkingProcess = document.getElementById('thinkingProcess');
                        if (thinkingProcess) {
                            thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
                        }
                    }
                }

                // Keep the thinking icon animation running for subsequent tasks
                const thinkingIcon = document.getElementById('thinkingIcon');
                if (thinkingIcon) {
                    // Ensure the animation is running
                    thinkingIcon.style.animation = 'spin 1.5s linear infinite';
                }
            });
        });
    }
});
