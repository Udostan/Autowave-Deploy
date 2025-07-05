// Super Agent JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Super Agent JS loaded');

    // Check if markdownit is available
    if (window.markdownit) {
        console.log('markdownit is available');
    } else {
        console.error('markdownit is NOT available - this will cause issues with rendering results');
    }

    // Check for task parameter in URL and auto-populate input field
    const urlParams = new URLSearchParams(window.location.search);
    const taskParam = urlParams.get('task');
    if (taskParam) {
        console.log('Task parameter found in URL:', taskParam);

        // Function to wait for elements and populate input
        function waitForElementsAndPopulate() {
            console.log('Waiting for elements to be available...');

            // Check for required elements
            const taskTab = document.querySelector('.tab-button[data-tab="task"]');
            const taskInputContainer = document.getElementById('taskInputContainer');
            const taskDescription = document.getElementById('taskDescription');

            console.log('Element check:');
            console.log('- taskTab:', !!taskTab);
            console.log('- taskInputContainer:', !!taskInputContainer);
            console.log('- taskDescription:', !!taskDescription);

            if (taskTab && taskInputContainer && taskDescription) {
                console.log('All elements found, proceeding with input population...');

                // Activate the Task tab
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('border-white', 'text-white');
                    btn.classList.add('border-transparent', 'text-gray-400');
                });
                taskTab.classList.remove('border-transparent', 'text-gray-400');
                taskTab.classList.add('border-white', 'text-white');

                // Show the task content and hide others
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.add('hidden');
                });
                const taskContent = document.getElementById('task-content');
                if (taskContent) {
                    taskContent.classList.remove('hidden');
                }

                console.log('Task tab activated for URL parameter');

                // Show the fixed input container
                taskInputContainer.style.display = 'block';
                console.log('Task input container made visible for URL parameter');

                // Set the task description field
                taskDescription.value = decodeURIComponent(taskParam);
                console.log('Task description field populated from URL parameter:', taskDescription.value);

                // Focus on the input field to draw user attention
                taskDescription.focus();

                // Scroll to the input field if needed
                taskDescription.scrollIntoView({ behavior: 'smooth', block: 'center' });

                return true; // Success
            } else {
                console.log('Some elements not found yet, will retry...');
                return false; // Not ready yet
            }
        }

        // Try immediately
        if (!waitForElementsAndPopulate()) {
            // If not successful, retry with intervals
            let retryCount = 0;
            const maxRetries = 20; // 10 seconds total

            const retryInterval = setInterval(() => {
                retryCount++;
                console.log(`Retry attempt ${retryCount}/${maxRetries}`);

                if (waitForElementsAndPopulate() || retryCount >= maxRetries) {
                    clearInterval(retryInterval);
                    if (retryCount >= maxRetries) {
                        console.error('Failed to find all required elements after maximum retries');
                    }
                }
            }, 500);
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
                                const screenshotData = this.getAttribute('data-screenshot');
                                const screenshotUrlData = this.getAttribute('data-screenshot-url');
                                const titleData = this.getAttribute('data-title');

                                // Create zoom modal logic here
                                console.log('Zoom button clicked for:', titleData);
                            });
                        }

                        if (button.classList.contains('screenshot-download-btn')) {
                            button.addEventListener('click', function() {
                                // Handle download button click
                                const screenshotData = this.getAttribute('data-screenshot');
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
                use_advanced_browser: useAdvancedBrowser ? useAdvancedBrowser.checked : true  // Always use advanced browser
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
                    // Check if this is a credit-related error
                    const isCreditError = data.error.toLowerCase().includes('credit') ||
                                         data.error.toLowerCase().includes('insufficient') ||
                                         data.error.toLowerCase().includes('payment required');

                    // Track failed activity
                    if (window.trackActivity) {
                        try {
                            const agentType = window.location.pathname === '/agent-wave' ? 'agent_wave' : 'prime_agent';

                            window.trackActivity(agentType, 'task_execution', {
                                task_description: description,
                                use_browser_use: requestData.use_browser_use,
                                use_advanced_browser: requestData.use_advanced_browser
                            }, null, null, false, data.error);
                        } catch (trackError) {
                            console.warn('Error tracking failed activity:', trackError);
                            // Don't throw error, just log it
                        }
                    }

                    // Display error with special handling for credit errors
                    const errorClass = isCreditError ? 'border-yellow-200' : 'border-red-200';
                    const errorBgClass = isCreditError ? 'bg-yellow-50' : 'bg-red-50';
                    const errorTextClass = isCreditError ? 'text-yellow-700' : 'text-red-700';
                    const errorIcon = isCreditError ?
                        `<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                        </svg>` :
                        `<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>`;

                    const upgradeButton = isCreditError ?
                        `<div class="mt-4">
                            <a href="/pricing" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
                                </svg>
                                Upgrade Plan
                            </a>
                        </div>` : '';

                    taskResults.innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm border ${errorClass} overflow-hidden">
                            <div class="${errorBgClass} px-6 py-4 border-b ${errorClass}">
                                <h3 class="text-lg font-semibold ${errorTextClass} flex items-center">
                                    ${errorIcon}
                                    ${isCreditError ? 'Insufficient Credits' : 'Error'}
                                </h3>
                            </div>
                            <div class="p-6 ${errorTextClass}">
                                ${data.error}
                                ${upgradeButton}
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

                    // Extract sources from the task summary for later use
                    let sources = extractSourcesFromSummary(data.task_summary || '');
                    console.log('Extracted sources:', sources);

                    // Clean up the task summary to remove duplicate sources
                    let formattedSummary = cleanupTaskSummary(data.task_summary || '');

                    // Function to extract sources from a summary
                    function extractSourcesFromSummary(summary) {
                        const sources = [];

                        // Extract sources section
                        const sourcesSectionMatch = summary.match(/## Sources\s*\n([\s\S]*?)(\n\n|$)/);
                        if (sourcesSectionMatch && sourcesSectionMatch[1]) {
                            const sourcesText = sourcesSectionMatch[1];

                            // Extract individual sources
                            const sourceRegex = /\d+\.\s*\[(.*?)\]\((.*?)\)/g;
                            let match;
                            while ((match = sourceRegex.exec(sourcesText)) !== null) {
                                sources.push({
                                    title: match[1],
                                    url: match[2]
                                });
                            }
                        }

                        return sources;
                    }

                    // Function to clean up task summary and remove duplicate sources
                    function cleanupTaskSummary(summary) {
                        if (!summary) return '';

                        console.log('Cleaning up task summary...');

                        // Check if there are duplicate Sources sections
                        const sourcesSections = summary.match(/## Sources\s*\n/g);
                        if (sourcesSections && sourcesSections.length > 1) {
                            console.log('Found multiple Sources sections, cleaning up...');

                            // Split the summary by the Sources heading
                            const parts = summary.split(/## Sources\s*\n/);

                            // Keep only the first part and the first Sources section
                            if (parts.length > 1) {
                                // Extract unique sources from all sections
                                const allSources = [];
                                const sourceRegex = /\d+\.\s*\[(.*?)\]\((.*?)\)/g;

                                // Process all parts after the first one (these are the sources sections)
                                for (let i = 1; i < parts.length; i++) {
                                    let match;
                                    while ((match = sourceRegex.exec(parts[i])) !== null) {
                                        const title = match[1];
                                        const url = match[2];

                                        // Check if this source is already in our list
                                        const isDuplicate = allSources.some(source =>
                                            source.url === url || source.title === title);

                                        if (!isDuplicate) {
                                            allSources.push({ title, url });
                                        }
                                    }
                                }

                                // Create a new Sources section with unique sources
                                let newSourcesSection = "## Sources\n\n";
                                allSources.forEach((source, index) => {
                                    newSourcesSection += `${index + 1}. [${source.title}](${source.url})\n`;
                                });

                                // Return the cleaned up summary
                                return parts[0] + newSourcesSection;
                            }
                        }

                        // Also clean up "Screenshots from Web Browsing" section if it appears in the text
                        summary = summary.replace(/Screenshots from Web Browsing\s*\n(.*?)\n\n/gs, '');

                        // If no duplicate Sources sections, return the original summary
                        return summary;
                    }

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
                    const screenshots = [];
                    const webImages = [];

                    console.log('Checking for screenshots and images in results:', data);

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
                            } else if (resultItem.result) {
                                console.log(`No screenshot in result ${idx}. Keys available:`, Object.keys(resultItem.result));
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
                            } else if (resultItem.result) {
                                console.log(`No images in result ${idx} or images array is empty`);
                            }
                        });
                    } else {
                        console.log('No results array found or results is not an array:', data.results);
                    }

                    console.log(`Found ${screenshots.length} screenshots from advanced browser`);
                    console.log(`Found ${webImages.length} images from websites`);

                    // Add screenshots directly to the task results HTML
                    console.log('Adding screenshots directly to task results');

                    // Create a screenshots section that will be added directly to the task results
                    let screenshotsHtml = `
                        <div class="my-8 border-t border-gray-200 pt-6">
                            <h2 class="text-2xl font-bold mb-4">Screenshots from Web Browsing</h2>
                            <div class="screenshot-grid">
                    `;

                    // Add each screenshot
                    screenshots.forEach((screenshot, index) => {
                        screenshotsHtml += `
                            <div class="screenshot-container">
                                <div class="screenshot-header">
                                    <div class="screenshot-title">${screenshot.title || `Screenshot ${index + 1}`}</div>
                                    ${screenshot.url ? `<div class="screenshot-url"><a href="${screenshot.url}" target="_blank">${screenshot.url}</a></div>` : ''}
                                </div>
                                <div class="screenshot-image-container">
                                    ${screenshot.screenshot ?
                                        `<img src="data:image/png;base64,${screenshot.screenshot}" alt="${screenshot.title || `Screenshot ${index + 1}`}" class="screenshot-image" data-screenshot-processed="true">` :
                                        screenshot.screenshot_url ?
                                            `<img src="${screenshot.screenshot_url}" alt="${screenshot.title || `Screenshot ${index + 1}`}" class="screenshot-image" data-screenshot-processed="true">` :
                                            `<div class="p-4 text-center text-gray-500">No screenshot available</div>`
                                    }
                                </div>
                                <div class="screenshot-footer">
                                    <button class="screenshot-btn screenshot-zoom-btn" data-handler-attached="true"
                                        data-screenshot="${screenshot.screenshot || ''}"
                                        data-screenshot-url="${screenshot.screenshot_url || ''}"
                                        data-title="${screenshot.title || `Screenshot ${index + 1}`}">
                                        <i class="fas fa-search-plus"></i> Zoom
                                    </button>
                                    <button class="screenshot-btn screenshot-download-btn" data-handler-attached="true"
                                        data-screenshot="${screenshot.screenshot || ''}"
                                        data-screenshot-url="${screenshot.screenshot_url || ''}"
                                        data-title="${screenshot.title || `Screenshot ${index + 1}`}">
                                        <i class="fas fa-download"></i> Download
                                    </button>
                                </div>
                            </div>
                        `;
                    });

                    screenshotsHtml += `
                            </div>
                        </div>
                    `;

                    // Store the screenshots HTML to be added directly to the task results later
                    window.screenshotsHtml = screenshotsHtml;

                    // Add web images directly to the task results HTML
                    console.log('Adding web images directly to task results');

                    // Sort images by size (larger first) if dimensions are available
                    webImages.sort((a, b) => {
                        const aSize = a.width && a.height ? a.width * a.height : 0;
                        const bSize = b.width && b.height ? b.width * b.height : 0;
                        return bSize - aSize;
                    });

                    // Take top 10 images
                    const topImages = webImages.slice(0, 10);

                    // Create a web images section that will be added directly to the task results
                    let webImagesHtml = `
                        <div class="my-8 border-t border-gray-200 pt-6">
                            <h2 class="text-2xl font-bold mb-4">Images from Web Sources</h2>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    `;

                    // Add each web image
                    topImages.forEach((img) => {
                        webImagesHtml += `
                            <div class="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
                                <div class="p-4">
                                    <h3 class="text-lg font-medium mb-2">Image from ${img.title}</h3>
                                    <p class="text-sm text-gray-500 mb-2"><a href="${img.url}" target="_blank" class="text-blue-600 hover:underline">${img.url}</a></p>
                                </div>
                                <div class="border-t border-gray-200">
                                    <img src="${img.src}" alt="${img.alt}" class="w-full h-auto object-cover" style="max-height: 300px;">
                                </div>
                            </div>
                        `;
                    });

                    webImagesHtml += `
                            </div>
                        </div>
                    `;

                    // Store the web images HTML to be added directly to the task results later
                    window.webImagesHtml = webImagesHtml;

                    // If no image placeholders were found, create some based on the content
                    if (imageMatches.length === 0) {
                        // Extract potential image topics from headings
                        const headingRegex = /#+\s+(.+?)\n/g;
                        let headingMatch;
                        while ((headingMatch = headingRegex.exec(formattedSummary)) !== null) {
                            const heading = headingMatch[1].trim();
                            if (heading.length > 3 && !heading.toLowerCase().includes('summary') && !heading.toLowerCase().includes('conclusion')) {
                                const placeholder = `[IMAGE: ${heading}]`;
                                imageMatches.push({
                                    placeholder: placeholder,
                                    description: heading
                                });
                                // Insert the placeholder after the heading
                                const insertPosition = headingMatch.index + headingMatch[0].length;
                                formattedSummary = formattedSummary.slice(0, insertPosition) + placeholder + '\n\n' + formattedSummary.slice(insertPosition);
                            }
                        }

                        // If still no images, extract key phrases from the content
                        if (imageMatches.length === 0) {
                            const contentWords = formattedSummary.split(/\s+/);
                            const keyPhrases = [];
                            for (let i = 0; i < contentWords.length; i += 30) {
                                if (i + 5 < contentWords.length) {
                                    const phrase = contentWords.slice(i, i + 5).join(' ');
                                    if (phrase.length > 10) {
                                        keyPhrases.push(phrase);
                                    }
                                }
                            }

                            if (keyPhrases.length > 0) {
                                const placeholder = `[IMAGE: ${keyPhrases[0]}]`;
                                imageMatches.push({
                                    placeholder: placeholder,
                                    description: keyPhrases[0]
                                });
                                // Insert the placeholder at the beginning of the content
                                formattedSummary = placeholder + '\n\n' + formattedSummary;
                            }
                        }
                    }

                    console.log('Found image placeholders:', imageMatches);

                    // Extract URLs from the task summary
                    const urlRegex = /(https?:\/\/[^\s]+)/g;
                    const urls = [];
                    let urlMatch;
                    while ((urlMatch = urlRegex.exec(data.task_summary)) !== null) {
                        // Clean up URLs (remove trailing punctuation)
                        let url = urlMatch[1];
                        if (url.endsWith('.') || url.endsWith(',') || url.endsWith(')') || url.endsWith(']')) {
                            url = url.slice(0, -1);
                        }
                        urls.push(url);
                    }
                    console.log('Found URLs:', urls);

                    // Replace image placeholders with actual image HTML
                    if (imageMatches.length > 0) {
                        // First, check if we have actual web images to use
                        if (webImages.length > 0) {
                            console.log('Using actual web images for placeholders');
                            // Use actual images from the web pages
                            imageMatches.forEach((img, i) => {
                                // Get a web image to use
                                const webImage = webImages[i % webImages.length];

                                // Create HTML for the image
                                const imageHtml = `<div class="my-6">
                                    <a href="${webImage.url}" target="_blank" rel="noopener noreferrer" class="block">
                                        <div class="relative overflow-hidden rounded-lg shadow-md">
                                            <img src="${webImage.src}" alt="${img.description}" class="w-full h-auto object-cover">
                                            <div class="absolute inset-0 bg-black bg-opacity-20 opacity-0 hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                                                <div class="text-white font-medium px-4 py-2 rounded-full bg-black bg-opacity-50">
                                                    Visit website <i class="fas fa-external-link-alt ml-1"></i>
                                                </div>
                                            </div>
                                        </div>
                                        <p class="text-sm text-center text-gray-500 mt-2">${img.description}</p>
                                    </a>
                                </div>`;

                                // Replace the placeholder with the HTML
                                // We need to escape the HTML so markdown-it doesn't try to process it
                                const escapedHtml = `<div class="markdown-html-block">${imageHtml}</div>`;
                                formattedSummary = formattedSummary.replace(img.placeholder, escapedHtml);
                            });

                            // Update the task results after all replacements
                            updateTaskResults();

                            // Automatically expand the task summary after execution (desktop only)
                            if (window.innerWidth >= 1024) { // Desktop view check
                                setTimeout(() => {
                                    // Trigger the expand button click
                                    if (expandSummaryBtn) {
                                        expandSummaryBtn.click();
                                        console.log('Auto-expanded task summary');
                                    }
                                }, 1000); // Wait 1 second after task completion
                            }

                            return; // Skip the regular image processing
                        }
                        // If no web images, continue with regular processing
                        imageMatches.forEach((img, index) => {
                            // Prepare the image description for search
                            const searchTerm = img.description.replace(/\s+/g, '+');
                            // Use the MCP server to get an image
                            // We'll use the fetch API to get images instead of direct URL

                            // Get a URL to link to (if available)
                            let linkUrl = '#';
                            if (urls.length > 0) {
                                // Try to find a URL that matches the image description
                                const lowerDesc = img.description.toLowerCase();
                                const matchingUrl = urls.find(url => {
                                    return url.toLowerCase().includes(lowerDesc.split(' ')[0]) ||
                                           lowerDesc.includes(url.toLowerCase().split('/')[2]);
                                });

                                if (matchingUrl) {
                                    linkUrl = matchingUrl;
                                } else if (urls.length > index) {
                                    linkUrl = urls[index];
                                } else if (urls.length > 0) {
                                    linkUrl = urls[0];
                                }
                            }

                            // Analyze the description to improve image search
                            const lowerDesc = img.description.toLowerCase();

                            // Enhance the search term based on the content
                            if (lowerDesc.includes('city') || lowerDesc.includes('skyline') || lowerDesc.includes('building')) {
                                searchTerm += '+cityscape+architecture';
                            } else if (lowerDesc.includes('weather') || lowerDesc.includes('forecast') || lowerDesc.includes('temperature')) {
                                searchTerm += '+weather+sky';
                            } else if (lowerDesc.includes('food') || lowerDesc.includes('restaurant') || lowerDesc.includes('meal')) {
                                searchTerm += '+food+cuisine+gourmet';
                            } else if (lowerDesc.includes('travel') || lowerDesc.includes('vacation') || lowerDesc.includes('trip')) {
                                searchTerm += '+travel+destination';
                            } else if (lowerDesc.includes('hotel') || lowerDesc.includes('accommodation') || lowerDesc.includes('stay')) {
                                searchTerm += '+hotel+luxury';
                            } else if (lowerDesc.includes('car') || lowerDesc.includes('vehicle') || lowerDesc.includes('drive')) {
                                searchTerm += '+automobile+vehicle';
                            } else if (lowerDesc.includes('map') || lowerDesc.includes('location') || lowerDesc.includes('place')) {
                                searchTerm += '+map+location';
                            } else if (lowerDesc.includes('shopping') || lowerDesc.includes('store') || lowerDesc.includes('shop')) {
                                searchTerm += '+retail+shopping';
                            } else if (lowerDesc.includes('money') || lowerDesc.includes('finance') || lowerDesc.includes('bank')) {
                                searchTerm += '+finance+business';
                            } else if (lowerDesc.includes('health') || lowerDesc.includes('medical') || lowerDesc.includes('hospital')) {
                                searchTerm += '+healthcare+medical';
                            } else if (lowerDesc.includes('education') || lowerDesc.includes('school') || lowerDesc.includes('university')) {
                                searchTerm += '+education+campus';
                            } else if (lowerDesc.includes('technology') || lowerDesc.includes('computer') || lowerDesc.includes('device')) {
                                searchTerm += '+technology+digital';
                            } else {
                                // Add a general quality term for better images
                                searchTerm += '+high+quality+professional';
                            }

                            // Make an AJAX request to get the image URL
                            fetch(`/api/mcp/execute`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    tool: 'image_search',
                                    params: {
                                        query: searchTerm, // Use the formatted search term
                                        num_results: 1
                                    }
                                })
                            })
                            .then(response => response.json())
                            .then(data => {
                                console.log('Image search response:', data);
                                if (data && Array.isArray(data) && data.length > 0) {
                                    const imageUrl = data[0].src;
                                    console.log('Using image URL:', imageUrl);
                                    const imageHtml = `<div class="my-6">
                                        <a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="block">
                                            <img src="${imageUrl}" alt="${img.description}" class="rounded-lg shadow-md w-full max-w-2xl mx-auto h-auto object-cover">
                                            <div class="text-sm text-center text-gray-500 mt-2">${img.description}</div>
                                        </a>
                                    </div>`;

                                    // Replace the placeholder with the HTML
                                    // We need to escape the HTML so markdown-it doesn't try to process it
                                    const escapedHtml = `<div class="markdown-html-block">${imageHtml}</div>`;
                                    formattedSummary = formattedSummary.replace(img.placeholder, escapedHtml);

                                    // Update the task results
                                    updateTaskResults();
                                } else {
                                    // Try using Unsplash source directly as a fallback
                                    const unsplashUrl = `https://source.unsplash.com/800x400/?${searchTerm}`;
                                    console.log('No image found, using Unsplash fallback URL:', unsplashUrl);

                                    const imageHtml = `<div class="my-6">
                                        <a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="block">
                                            <img src="${unsplashUrl}" alt="${img.description}" class="rounded-lg shadow-md w-full max-w-2xl mx-auto h-auto object-cover" onerror="this.onerror=null; this.src='https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(img.description)}';">
                                            <div class="text-sm text-center text-gray-500 mt-2">${img.description}</div>
                                        </a>
                                    </div>`;

                                    // Replace the placeholder with the HTML
                                    // We need to escape the HTML so markdown-it doesn't try to process it
                                    const escapedHtml = `<div class="markdown-html-block">${imageHtml}</div>`;
                                    formattedSummary = formattedSummary.replace(img.placeholder, escapedHtml);

                                    // Update the task results
                                    updateTaskResults();
                                }
                            })
                            .catch(error => {
                                console.error('Error fetching image:', error);

                                // Try using Unsplash source directly as a fallback
                                const unsplashUrl = `https://source.unsplash.com/800x400/?${searchTerm}`;
                                console.log('Using Unsplash fallback URL:', unsplashUrl);

                                const imageHtml = `<div class="my-6">
                                    <a href="${linkUrl}" target="_blank" rel="noopener noreferrer" class="block">
                                        <img src="${unsplashUrl}" alt="${img.description}" class="rounded-lg shadow-md w-full max-w-2xl mx-auto h-auto object-cover" onerror="this.onerror=null; this.src='https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(img.description)}';">
                                        <div class="text-sm text-center text-gray-500 mt-2">${img.description}</div>
                                    </a>
                                </div>`;

                                // Replace the placeholder with the HTML
                                // We need to escape the HTML so markdown-it doesn't try to process it
                                const escapedHtml = `<div class="markdown-html-block">${imageHtml}</div>`;
                                formattedSummary = formattedSummary.replace(img.placeholder, escapedHtml);

                                // Update the task results
                                updateTaskResults();
                            });

                            // The placeholder will be replaced in the fetch callback
                        });
                    }

                    // Process the task summary as Markdown and convert it to HTML
                    console.log('Original summary with HTML:', formattedSummary.substring(0, 500));

                    // Define a function to update the task results
                    function updateTaskResults() {
                        console.log('Updating task results...');

                        // We're now directly embedding the HTML for screenshots and images
                        // No need to process placeholders anymore
                        let processedSummary = formattedSummary;

                        // Use our markdown processor to render the content
                        let processedHtml = '';
                        if (window.markdownProcessor && window.markdownProcessor.renderMarkdown) {
                            processedHtml = window.markdownProcessor.renderMarkdown(processedSummary);
                        } else {
                            // Fallback to direct markdown-it if our processor is not available
                            const md = window.markdownit({
                                html: true,  // Enable HTML tags in source
                                breaks: true,  // Convert '\n' in paragraphs into <br>
                                linkify: true,  // Autoconvert URL-like text to links
                                typographer: true  // Enable some language-neutral replacement + quotes beautification
                            });
                            processedHtml = '<div class="task-summary">' + md.render(processedSummary) + '</div>';
                        }

                        console.log('Rendered Markdown to HTML:', processedHtml.substring(0, 500));

                        // Update the initial summary container instead of creating a new one
                        const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');
                        if (summaryContainer) {
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
                                headerElement.textContent = 'Task Summary: ' + taskDescription.value.trim();
                            }

                            console.log('Updated summary container with task results');
                        } else {
                            console.error('Could not find summary container to update');
                        }

                        // No need to update taskResults as we're updating the initial container directly
                    }

                    // Initial update
                    updateTaskResults();

                    // Handle credit consumption if present in response
                    if (data.credits_consumed !== undefined && data.remaining_credits !== undefined) {
                        console.log(`Credits consumed: ${data.credits_consumed}, Remaining: ${data.remaining_credits}`);

                        // Update Universal Credit System if available
                        if (window.creditSystem && window.creditSystem.isInitialized) {
                            console.log('Updating Universal Credit System with new credit info');
                            window.creditSystem.userCredits.remaining = data.remaining_credits;
                            window.creditSystem.updateSidebarCredits();
                        }

                        // Also trigger global credit refresh
                        if (window.refreshCredits) {
                            window.refreshCredits();
                        }

                        // Show credit consumption notification
                        if (window.showNotification) {
                            window.showNotification(`Used ${data.credits_consumed} credits for this task. ${data.remaining_credits} remaining.`, 'success');
                        }
                    }

                    // Track successful activity in enhanced history
                    if (window.trackActivity) {
                        try {
                            const agentType = window.location.pathname === '/agent-wave' ? 'agent_wave' : 'prime_agent';

                            window.trackActivity(agentType, 'task_execution', {
                                task_description: description,
                                use_browser_use: requestData.use_browser_use,
                                use_advanced_browser: requestData.use_advanced_browser
                            }, {
                                task_summary: data.task_summary,
                                summary_length: data.task_summary ? data.task_summary.length : 0,
                                has_screenshots: screenshots.length > 0,
                                screenshot_count: screenshots.length,
                                has_web_images: webImages.length > 0,
                                web_image_count: webImages.length,
                                sources_count: sources.length,
                                credits_consumed: data.credits_consumed,
                                remaining_credits: data.remaining_credits
                            });
                        } catch (trackError) {
                            console.warn('Error tracking activity:', trackError);
                            // Don't throw error, just log it
                        }
                    }
                } else if (data.result && data.result.summary) {
                            const resultsContainer = document.querySelector('#taskResults');

                            if (resultsContainer.classList.contains('expanded')) {
                                // Collapse
                                resultsContainer.classList.remove('expanded');
                                resultsContainer.style.height = '800px';
                                resultsContainer.style.overflowY = 'scroll';

                                // Update button title
                                this.setAttribute('title', 'Expand to full view');
                            } else {
                                // Expand
                                resultsContainer.classList.add('expanded');
                                resultsContainer.style.height = '1500px';
                                resultsContainer.style.overflowY = 'scroll';

                                // Update button title
                                this.setAttribute('title', 'Collapse to normal view');

                                // Scroll to top
                                resultsContainer.scrollTop = 0;
                            }
                        });

                        document.getElementById('copyToClipboardBtn').addEventListener('click', function() {
                            const summaryText = document.querySelector('.task-summary').innerText;
                            navigator.clipboard.writeText(summaryText).then(() => {
                                alert('Summary copied to clipboard!');
                            });
                        });

                        document.getElementById('downloadPdfBtn').addEventListener('click', function() {
                            alert('PDF download functionality will be implemented in a future update.');
                        });

                        // Add event listeners for screenshot buttons
                        // We're now using the screenshot_handler.js to handle these buttons
                        document.querySelectorAll('.screenshot-zoom-btn:not([data-handler-attached])').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const screenshot = this.getAttribute('data-screenshot');
                                const screenshotUrl = this.getAttribute('data-screenshot-url');
                                const title = this.getAttribute('data-title');

                                // Create a modal to display the full-size screenshot
                                const modal = document.createElement('div');
                                modal.className = 'screenshot-modal';

                                // Determine the image source based on what's available
                                let imgSrc = '';
                                if (screenshot && screenshot.length > 0) {
                                    imgSrc = `data:image/png;base64,${screenshot}`;
                                } else if (screenshotUrl && screenshotUrl.length > 0) {
                                    imgSrc = screenshotUrl;
                                } else {
                                    // Fallback to a placeholder if no image is available
                                    imgSrc = `https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(title || 'No image available')}`;
                                }

                                modal.innerHTML = `
                                    <div class="screenshot-modal-content">
                                        <div class="screenshot-modal-close">
                                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <path d="M6 18L18 6M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                            </svg>
                                        </div>
                                        <div class="screenshot-modal-image-container">
                                            <img src="${imgSrc}" class="screenshot-modal-image" alt="${title || 'Full-size screenshot'}">
                                        </div>
                                    </div>
                                `;
                                document.body.appendChild(modal);

                                // Add event listener to close the modal
                                modal.querySelector('.screenshot-modal-close').addEventListener('click', function() {
                                    document.body.removeChild(modal);
                                });

                                // Close modal when clicking outside the image
                                modal.addEventListener('click', function(e) {
                                    if (e.target === modal) {
                                        document.body.removeChild(modal);
                                    }
                                });
                            });

                            // Mark as processed
                            btn.setAttribute('data-handler-attached', 'true');
                        });

                        document.querySelectorAll('.screenshot-download-btn:not([data-handler-attached])').forEach(btn => {
                            btn.addEventListener('click', function() {
                                const screenshot = this.getAttribute('data-screenshot');
                                const screenshotUrl = this.getAttribute('data-screenshot-url');
                                const title = this.getAttribute('data-title') || 'screenshot';

                                if (screenshot && screenshot.length > 0) {
                                    // Download base64 image
                                    const a = document.createElement('a');
                                    a.href = `data:image/png;base64,${screenshot}`;
                                    a.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${new Date().toISOString().slice(0, 10)}.png`;
                                    document.body.appendChild(a);
                                    a.click();

                                    // Clean up
                                    setTimeout(() => {
                                        document.body.removeChild(a);
                                    }, 100);
                                } else if (screenshotUrl && screenshotUrl.length > 0) {
                                    // For direct URLs, we need to fetch the image first
                                    fetch(screenshotUrl)
                                        .then(response => response.blob())
                                        .then(blob => {
                                            const blobUrl = URL.createObjectURL(blob);
                                            const a = document.createElement('a');
                                            a.href = blobUrl;
                                            a.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${new Date().toISOString().slice(0, 10)}.png`;
                                            document.body.appendChild(a);
                                            a.click();

                                            // Clean up
                                            setTimeout(() => {
                                                URL.revokeObjectURL(blobUrl);
                                                document.body.removeChild(a);
                                            }, 100);
                                        })
                                        .catch(error => {
                                            console.error('Error downloading image:', error);
                                            alert('Failed to download image. Please try again.');
                                        });
                                } else {
                                    alert('No image available to download.');
                                }
                            });

                            // Mark as processed
                            btn.setAttribute('data-handler-attached', 'true');
                        });

                        // Also update the modal content
                        if (modalTaskResults) {
                            modalTaskResults.innerHTML = `<div class="html-content task-summary">${processedHtml}</div>`;
                            console.log('Updated modal content with HTML');

                            // Add event listeners to modal content as well
                            const modalZoomButtons = modalTaskResults.querySelectorAll('.screenshot-zoom-btn');
                            if (modalZoomButtons && modalZoomButtons.length > 0) {
                                modalZoomButtons.forEach(btn => {
                                    btn.addEventListener('click', function() {
                                        const screenshot = this.getAttribute('data-screenshot');
                                        const screenshotUrl = this.getAttribute('data-screenshot-url');
                                        const title = this.getAttribute('data-title');

                                        // Create a modal to display the full-size screenshot
                                        const modal = document.createElement('div');
                                        modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50';

                                        // Determine the image source based on what's available
                                        let imgSrc = '';
                                        if (screenshot && screenshot.length > 0) {
                                            imgSrc = `data:image/png;base64,${screenshot}`;
                                        } else if (screenshotUrl && screenshotUrl.length > 0) {
                                            imgSrc = screenshotUrl;
                                        } else {
                                            // Fallback to a placeholder if no image is available
                                            imgSrc = `https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(title || 'No image available')}`;
                                        }

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
                                                    <img src="${imgSrc}" class="max-w-full h-auto" alt="${title || 'Full-size screenshot'}">
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

                            const modalDownloadButtons = modalTaskResults.querySelectorAll('.screenshot-download-btn');
                            if (modalDownloadButtons && modalDownloadButtons.length > 0) {
                                modalDownloadButtons.forEach(btn => {
                                    btn.addEventListener('click', function() {
                                        const screenshot = this.getAttribute('data-screenshot');
                                        const title = this.getAttribute('data-title') || 'screenshot';

                                        // Create a temporary link to download the image
                                        const a = document.createElement('a');
                                        a.href = `data:image/png;base64,${screenshot}`;
                                        a.download = `${title}_${new Date().toISOString().slice(0, 10)}.png`;
                                        document.body.appendChild(a);
                                        a.click();

                                        // Clean up
                                        setTimeout(() => {
                                            document.body.removeChild(a);
                                        }, 100);
                                    });
                                });
                            }
                        }
                    }

                    // Initial update
                    updateTaskResults();
                } else if (data.result && data.result.summary) {
                    // Handle old API response format
                    const md = window.markdownit();
                    const formattedSummary = md.render(data.result.summary || '');

                    // Extract image descriptions for later use
                    const imageDescriptions = [];
                    const imageRegex = /\[IMAGE: ([^\]]+)\]/g;
                    let match;
                    while ((match = imageRegex.exec(formattedSummary)) !== null) {
                        imageDescriptions.push(match[1]);
                    }

                    console.log('Found image placeholders:', imageDescriptions);

                    // For this implementation, we'll use placeholders for all images
                    let allAvailableImages = [];

                    // Create placeholder image objects for each description
                    imageDescriptions.forEach(description => {
                        allAvailableImages.push({
                            src: `https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(description.substring(0, 20))}...`,
                            alt: description,
                            width: 800,
                            height: 400
                        });
                    });

                    console.log('Created image URLs:', allAvailableImages);

                    // Replace image placeholders with actual images
                    let imageCounter = 0;
                    const allImages = allAvailableImages;

                    const summaryWithImages = formattedSummary.replace(imageRegex, (_, description) => {
                        // If we have images, use them
                        if (allImages.length > 0) {
                            const imageIndex = imageCounter % allImages.length;
                            imageCounter++;
                            const image = allImages[imageIndex];
                            return `<div class="my-4">
                                <img src="${image.src}" alt="${description}" class="rounded-lg shadow-md w-full max-w-2xl mx-auto h-auto object-cover">
                                <p class="text-sm text-center text-gray-500 mt-2">${description}</p>
                            </div>`;
                        } else {
                            // If no images are available, use a placeholder
                            const placeholderUrl = `https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(description.substring(0, 20))}...`;
                            return `<div class="my-4">
                                <img src="${placeholderUrl}" alt="${description}" class="rounded-lg shadow-md w-full max-w-2xl mx-auto h-auto object-cover">
                                <p class="text-sm text-center text-gray-500 mt-2">${description}</p>
                            </div>`;
                        }
                    });

                    // Update the initial summary container instead of creating a new one
                    const summaryContainer = document.querySelector('#summary-container-initial .summary-container-content');
                    if (summaryContainer) {
                        summaryContainer.innerHTML = summaryWithImages;

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

                // Track failed activity
                if (window.trackActivity) {
                    try {
                        const agentType = window.location.pathname === '/agent-wave' ? 'agent_wave' : 'prime_agent';

                        window.trackActivity(agentType, 'task_execution', {
                            task_description: description,
                            use_browser_use: requestData.use_browser_use,
                            use_advanced_browser: requestData.use_advanced_browser
                        }, null, null, false, error.message || 'Unknown error');
                    } catch (trackError) {
                        console.warn('Error tracking failed activity:', trackError);
                        // Don't throw error, just log it
                    }
                }

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
    } else {
        console.error('Execute Task button not found');
    }

    // Browse functionality
    const urlInput = document.getElementById('urlInput');
    const browseBtn = document.getElementById('browseBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const browseResults = document.getElementById('browseResults');

    if (browseBtn) {
        console.log('Browse button found');
        browseBtn.addEventListener('click', function() {
            if (!urlInput) {
                console.error('URL input not found');
                return;
            }

            const url = urlInput.value.trim();
            if (!url) {
                alert('Please enter a URL');
                return;
            }

            // Show loading state
            if (browseResults) {
                browseResults.classList.remove('hidden');
                browseResults.innerHTML = '<div class="flex items-center justify-center p-12"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-black"></div><div class="ml-4 text-gray-700">Loading...</div></div>';
            }

            // Disable buttons during request
            browseBtn.disabled = true;
            if (analyzeBtn) analyzeBtn.disabled = true;

            // Make API request
            fetch('/api/super-agent/browse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            })
            .then(response => response.json())
            .then(data => {
                if (!browseResults) {
                    console.error('Browse results element not found');
                    return;
                }

                if (data.success) {
                    browseResults.innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                            <div class="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                                <h3 class="text-lg font-semibold text-gray-900 flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
                                    </svg>
                                    ${data.title || 'Web Page'}
                                </h3>
                                <span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Success</span>
                            </div>
                            <div class="p-6">
                                <div class="mb-4">
                                    <span class="text-sm font-medium text-gray-500">URL:</span>
                                    <a href="${data.url}" target="_blank" class="text-blue-600 hover:underline ml-2">${data.url}</a>
                                </div>
                                <div class="prose max-w-none">
                                    <h4 class="text-lg font-medium mb-2">Page Content:</h4>
                                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-96 overflow-y-auto">
                                        <pre class="whitespace-pre-wrap text-sm">${data.content}</pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    browseResults.innerHTML = `
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
                                ${data.error || 'Failed to browse to the specified URL.'}
                            </div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error browsing:', error);

                if (browseResults) {
                    browseResults.innerHTML = `
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
                                Failed to browse: ${error.message || 'Unknown error'}
                            </div>
                        </div>
                    `;
                }
            })
            .finally(() => {
                // Re-enable buttons
                browseBtn.disabled = false;
                if (analyzeBtn) analyzeBtn.disabled = false;
            });
        });
    } else {
        console.error('Browse button not found');
    }


});
