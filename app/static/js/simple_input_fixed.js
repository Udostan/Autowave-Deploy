// Simple Input JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple Input JS loaded');

    // Get elements
    const executeTaskBtn = document.getElementById('executeTaskBtn');
    const taskDescription = document.getElementById('taskDescription');
    const resultsContainer = document.getElementById('resultsContainer');
    const taskProgress = document.getElementById('taskProgress');
    const taskSummaryContainer = document.getElementById('taskSummaryContainer');
    const useAdvancedBrowser = document.getElementById('useAdvancedBrowser');
    const progressFill = document.getElementById('progressFill');
    const stepDescription = document.getElementById('stepDescription');
    const processingIndicator = document.getElementById('processingIndicator');

    // Ensure advanced browser is always checked (hidden from UI but functionality remains)
    if (useAdvancedBrowser) {
        useAdvancedBrowser.checked = true;
        console.log('Advanced browser option is enabled by default');
    }

    // Container elements
    const thinkingContainers = document.getElementById('thinkingContainers');
    const summaryContainers = document.getElementById('summaryContainers');

    // Add event listener for toggle thinking buttons
    document.addEventListener('click', function(e) {
        if (e.target && e.target.closest('.toggle-thinking-btn')) {
            const toggleBtn = e.target.closest('.toggle-thinking-btn');
            const containerId = toggleBtn.getAttribute('data-container-id');
            const container = document.getElementById(containerId);
            const thinkingProcess = container.querySelector('.thinking-process');
            const arrowIcon = toggleBtn.querySelector('svg');

            // Toggle the thinking process visibility
            if (thinkingProcess.style.display === 'none') {
                // Show the thinking process
                thinkingProcess.style.display = 'block';
                arrowIcon.classList.remove('rotate-180');
                arrowIcon.classList.add('rotate-0');
            } else {
                // Hide the thinking process
                thinkingProcess.style.display = 'none';
                arrowIcon.classList.remove('rotate-0');
                arrowIcon.classList.add('rotate-180');
            }
        }
    });

    // Task counter for unique IDs
    let taskCounter = 0;

    // Task polling variables
    let taskPollingInterval = null;
    const POLLING_INTERVAL = 2000; // 2 seconds

    // Function to poll for task status
    function pollTaskStatus(sessionId) {
        console.log('Polling for task status with session ID:', sessionId);

        // Clear any existing polling interval
        if (taskPollingInterval) {
            clearInterval(taskPollingInterval);
        }

        // Start polling
        taskPollingInterval = setInterval(() => {
            // Make API request to get task status (using super-agent endpoint for backward compatibility)
            fetch(`/api/super-agent/task-status?session_id=${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Task status:', data);

                    // If the task is complete, update the UI and stop polling
                    if (data.status === 'complete') {
                        clearInterval(taskPollingInterval);

                        // Stop the enhanced thinking process if available
                        if (window.stopThinkingProcess) {
                            console.log('Stopping enhanced thinking process');
                            // Pass the current thinking container ID
                            window.stopThinkingProcess(true, currentThinkingContainer.id); // Show completion message
                        } else {
                            // Fallback to basic completion message
                            console.log('Enhanced thinking process not available, using fallback completion');

                            // Update the thinking process
                            if (currentThinkingContent) {
                                const completionP = document.createElement('div');
                                completionP.classList.add('text-green-600', 'mt-4', 'thinking-step');
                                completionP.innerHTML = '<strong>✓ Task completed!</strong>';
                                currentThinkingContent.appendChild(completionP);
                            }
                        }

                        // Update the task summary
                        if (currentSummaryContainer && data.result) {
                            const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
                            if (summaryContentDiv && data.result.task_summary) {
                                // Process the task summary as Markdown and convert it to HTML
                                let processedHtml = md.render(data.result.task_summary);

                                // Update the summary container
                                summaryContentDiv.innerHTML = processedHtml;
                            }
                        }

                        // Update the processing indicator
                        if (processingIndicator) {
                            processingIndicator.classList.add('completed');
                        }
                    }

                    // Check for progress updates
                    if (data.progress && data.progress.length > 0) {
                        // Get the latest progress message
                        const latestProgress = data.progress[data.progress.length - 1];

                        // If this is a thinking step, update the thinking process
                        if (latestProgress.status === 'thinking') {
                            // Check if we already have this message
                            const message = latestProgress.message;
                            const existingSteps = Array.from(currentThinkingContent.querySelectorAll('.thinking-step'))
                                .map(step => step.textContent.trim());

                            // If this is a new message, add it to the thinking process
                            if (!existingSteps.includes(message) && currentWords.length === 0) {
                                updateThinkingProcess(message);
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('Error polling for task status:', error);
                });
        }, POLLING_INTERVAL);
    }

    // Current active containers
    let currentThinkingContainer = document.getElementById('thinking-container-initial');
    let currentThinkingContent = document.querySelector('#thinking-container-initial .prose');
    let currentSummaryContainer = document.getElementById('summary-container-initial');

    // Flag to track if this is the first task
    let isFirstTask = true;

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
        executeTaskBtn.addEventListener('click', async function() {
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

            // Check credits before executing task
            if (window.creditSystem) {
                const canProceed = await window.creditSystem.enforceCredits('prime_agent_task');
                if (!canProceed) {
                    console.log('Insufficient credits for Prime Agent task');
                    return;
                }
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

            // Store the task description before clearing it
            const taskDescriptionValue = description;

            // Clear the input text immediately
            taskDescription.value = '';

            // Clear uploaded files
            if (window.universalFileUpload) {
                window.universalFileUpload.clearFiles('task');
            }

            // Update button to show processing state with a simple spinner
            executeTaskBtn.innerHTML = `
                <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>`;

            // Check if this is a request for one of our LLM-powered tools
            console.log('Checking for LLM tool detection with description:', description);
            const llmToolResult = detectAndHandleLLMTool(description);
            console.log('LLM tool detection result:', llmToolResult);
            if (llmToolResult) {
                console.log('✅ Detected LLM tool request, handling with dedicated endpoint');
                console.log('Tool:', llmToolResult.tool, 'Params:', llmToolResult.params);
                handleLLMToolRequest(llmToolResult.tool, llmToolResult.params, description);
                return;
            } else {
                console.log('❌ No LLM tool detected, using regular super-agent endpoint');
            }

            // Get uploaded files if available
            let fileContent = '';
            if (window.universalFileUpload) {
                fileContent = window.universalFileUpload.getFileContentForAI('task');
            }

            // Prepare request data - always use advanced browser
            const requestData = {
                task_description: description + fileContent,
                use_advanced_browser: true // Always use advanced browser
            };

            console.log('Making API request with data:', requestData);

            // Make API request
            // Use the super-agent API endpoint for backward compatibility
            const apiUrl = '/api/super-agent/execute-task';
            console.log('Using API URL:', apiUrl);

            fetch(apiUrl, {
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

                // Store the session ID for polling
                const sessionId = data.session_id;
                if (sessionId) {
                    console.log('Starting task status polling with session ID:', sessionId);
                    // Start polling for task status
                    pollTaskStatus(sessionId);
                }

                return data;
            })
            .then(data => {
                console.log('API response data:', data);

                // We don't need to check for taskResults anymore since we're using the summary container
                // directly instead

                if (data.error) {
                    // Track API error in enhanced history
                    if (window.trackActivity) {
                        try {
                            // Get uploaded files if available
                            let currentUploadedFiles = [];
                            if (window.universalFileUpload) {
                                currentUploadedFiles = window.universalFileUpload.getFiles('task') || [];
                            }

                            window.trackActivity('agent_wave', 'task_execution', {
                                task_description: taskDescriptionValue,
                                files: currentUploadedFiles,
                                use_advanced_browser: true
                            }, null, null, false, `API error: ${data.error}`);
                        } catch (trackError) {
                            console.warn('Error tracking API error activity:', trackError);
                        }
                    }

                    // Display error in the current summary container
                    if (currentSummaryContainer) {
                        const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
                        if (summaryContentDiv) {
                            summaryContentDiv.innerHTML = `
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
                        }
                    }
                } else if (data.task_summary) {
                    // Display result from task_summary field
                    console.log('Found task_summary in response:', data.task_summary);

                    // Check if the task summary contains an API error message
                    let formattedSummary = '';

                    // Extract sources from the task summary for later use
                    let sources = extractSourcesFromSummary(data.task_summary || '');
                    console.log('Extracted sources:', sources);

                    // Check if the task summary contains an API error message
                    if (data.task_summary && data.task_summary.includes("Error with Groq API") ||
                        data.task_summary && data.task_summary.includes("Error with Gemini API")) {

                        console.log('API error detected in task summary, generating fallback summary');

                        // Generate a fallback summary
                        formattedSummary = generateFallbackSummary(taskDescription.value, sources);
                    } else {
                        // Clean up the task summary to remove duplicate sources
                        formattedSummary = cleanupTaskSummary(data.task_summary || '');
                    }

                    console.log('Processed summary:', formattedSummary);

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

                    // Function to generate a fallback summary
                    function generateFallbackSummary(taskDescription, sources) {
                        // Create a basic summary based on the task description
                        let summary = `# ${taskDescription}\n\n`;

                        // Add a note about the API error
                        summary += "[IMAGE: Information Analysis]\n\n";
                        summary += "## Analysis\n\n";
                        summary += "I've gathered information from multiple sources about your query. ";
                        summary += "While I couldn't generate a detailed analysis due to a temporary API limitation, ";
                        summary += "I've compiled the relevant sources for you to explore.\n\n";

                        // Add key points based on the task description
                        summary += "[IMAGE: Key Information Points]\n\n";
                        summary += "## Key Points\n\n";

                        // Check if this is a stock-related query
                        if (taskDescription.toLowerCase().includes("stock") ||
                            taskDescription.toLowerCase().includes("market") ||
                            taskDescription.toLowerCase().includes("invest")) {

                            summary += "- Stock prices and market conditions change frequently, so it's important to check the latest data\n";
                            summary += "- Consider consulting financial news sources for the most current analysis\n";
                            summary += "- Look at historical performance trends to understand market patterns\n";
                            summary += "- Expert predictions should be considered alongside your own research\n";
                            summary += "- Multiple factors can influence stock performance including company news, industry trends, and broader economic conditions\n\n";

                            // Add specific stock-related content
                            if (taskDescription.toLowerCase().includes("amazon")) {
                                summary += "[IMAGE: Amazon Stock Chart]\n\n";
                                summary += "## Amazon Stock Information\n\n";
                                summary += "Amazon (AMZN) is a major technology company listed on the NASDAQ. ";
                                summary += "As one of the world's largest online retailers and cloud service providers, ";
                                summary += "its stock performance is influenced by factors such as:\n\n";

                                summary += "[IMAGE: Amazon Business Factors]\n\n";
                                summary += "- E-commerce market growth and competition\n";
                                summary += "- AWS (Amazon Web Services) performance\n";
                                summary += "- Consumer spending trends\n";
                                summary += "- Regulatory developments\n";
                                summary += "- Innovation and new product launches\n\n";

                                summary += "For the most current price and detailed analysis, please check financial websites like Yahoo Finance, Bloomberg, or MarketWatch.\n\n";
                            }
                        }
                        // Check if this is a travel-related query
                        else if (taskDescription.toLowerCase().includes("travel") ||
                                 taskDescription.toLowerCase().includes("trip") ||
                                 taskDescription.toLowerCase().includes("vacation")) {

                            summary += "[IMAGE: Travel Planning]\n\n";
                            summary += "- Consider the best time of year to visit your destination based on weather and tourist seasons\n";
                            summary += "- Research local customs, currency, and language basics before traveling\n";
                            summary += "- Look into accommodation options that fit your budget and preferences\n\n";

                            summary += "[IMAGE: Transportation Options]\n\n";
                            summary += "- Plan your transportation both to your destination and within the area\n";
                            summary += "- Create a flexible itinerary that allows for both planned activities and spontaneous exploration\n";
                            summary += "- Consider local transportation options like public transit, rental cars, or guided tours\n\n";
                        }
                        // Default key points for other types of queries
                        else {
                            summary += "[IMAGE: Research Methods]\n\n";
                            summary += "- Research from multiple sources provides a more comprehensive understanding\n";
                            summary += "- Consider both expert opinions and factual data in your analysis\n";
                            summary += "- Recent information is generally more relevant than older sources\n\n";

                            summary += "[IMAGE: Information Analysis]\n\n";
                            summary += "- Look for consensus across multiple sources to identify reliable information\n";
                            summary += "- Consider exploring the sources below for more detailed information\n";
                            summary += "- Evaluate the credibility of each source based on expertise and reputation\n\n";
                        }

                        // Add recommendations
                        summary += "[IMAGE: Recommendations]\n\n";
                        summary += "## Recommendations\n\n";
                        summary += "I recommend exploring the sources listed below for more detailed information. ";
                        summary += "Each source provides valuable insights that can help you make informed decisions.\n\n";

                        // Add specific recommendations based on the query type
                        if (taskDescription.toLowerCase().includes("stock") ||
                            taskDescription.toLowerCase().includes("market") ||
                            taskDescription.toLowerCase().includes("invest")) {

                            summary += "[IMAGE: Financial Resources]\n\n";
                            summary += "For the most accurate and up-to-date financial information:\n\n";
                            summary += "1. Check real-time stock prices on financial platforms like Yahoo Finance or Bloomberg\n";
                            summary += "2. Read recent analyst reports from reputable financial institutions\n";
                            summary += "3. Review the company's latest quarterly earnings reports\n";
                            summary += "4. Monitor news about industry trends and regulatory changes\n\n";
                        }
                        else if (taskDescription.toLowerCase().includes("travel") ||
                                 taskDescription.toLowerCase().includes("trip") ||
                                 taskDescription.toLowerCase().includes("vacation")) {

                            summary += "[IMAGE: Travel Resources]\n\n";
                            summary += "To plan your trip effectively:\n\n";
                            summary += "1. Visit official tourism websites for your destination\n";
                            summary += "2. Check travel advisories and entry requirements\n";
                            summary += "3. Compare prices on multiple booking platforms\n";
                            summary += "4. Read recent reviews from other travelers\n\n";
                        }

                        // Add sources section
                        if (sources && sources.length > 0) {
                            summary += "[IMAGE: Information Sources]\n\n";
                            summary += "## Sources\n\n";
                            sources.forEach((source, index) => {
                                summary += `${index + 1}. [${source.title}](${source.url})\n`;
                            });
                        }

                        return summary;
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

                        // Don't remove the "Screenshots from Web Browsing" section, just clean up duplicate instances
                        const screenshotSections = summary.match(/## Screenshots from Web Browsing\s*\n/g);
                        if (screenshotSections && screenshotSections.length > 1) {
                            console.log('Found multiple Screenshots sections, keeping only the first one');

                            // Split the summary by the Screenshots heading
                            const parts = summary.split(/## Screenshots from Web Browsing\s*\n/);

                            // Keep only the first part and the first Screenshots section
                            if (parts.length > 1) {
                                // Extract the first Screenshots section
                                const firstScreenshotSection = parts[1].split(/\n## /)[0];

                                // Remove all Screenshots sections from the original summary
                                let newSummary = summary.replace(/## Screenshots from Web Browsing\s*\n([\s\S]*?)(?=\n## |$)/g, '');

                                // Add the first Screenshots section back at the end (before Sources if present)
                                if (newSummary.includes('## Sources')) {
                                    newSummary = newSummary.replace(/## Sources/, `## Screenshots from Web Browsing\n${firstScreenshotSection}\n\n## Sources`);
                                } else {
                                    newSummary += `\n\n## Screenshots from Web Browsing\n${firstScreenshotSection}`;
                                }

                                return newSummary;
                            }
                        }

                        // If no duplicate Sources sections, return the original summary
                        return summary;
                    }

                    // Process image placeholders before rendering markdown
                    console.log('Processing image placeholders in summary...');

                    // Find all image placeholders in the format [IMAGE: description]
                    const imageRegex = /\[IMAGE: ([^\]]+)\]/g;
                    let imageMatches = [];
                    let match;

                    while ((match = imageRegex.exec(formattedSummary)) !== null) {
                        imageMatches.push({
                            placeholder: match[0],
                            description: match[1]
                        });
                    }

                    console.log(`Found ${imageMatches.length} image placeholders in summary`);

                    // If we have sources with URLs, use them to create images for the placeholders
                    if (sources && sources.length > 0 && imageMatches.length > 0) {
                        // Create a mapping of sources to use for images
                        const sourceImages = sources.map(source => ({
                            title: source.title,
                            url: source.url,
                            // Create a placeholder image URL based on the source title
                            imageUrl: `https://placehold.co/800x400/f5f5f5/333333?text=${encodeURIComponent(source.title.substring(0, 20))}`
                        }));

                        // Replace each image placeholder with an HTML image
                        imageMatches.forEach((imgMatch, index) => {
                            // Use a source image if available, otherwise use a placeholder
                            const sourceIndex = index % sourceImages.length;
                            const source = sourceImages[sourceIndex];

                            // Create HTML for the image
                            const imageHtml = `<div class="image-container">
                                <img src="${source.imageUrl}" alt="${imgMatch.description}" style="max-width: 100%; height: auto; border-radius: 0.5rem; margin: 1.5rem auto; display: block; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
                                <div class="image-caption">${imgMatch.description}</div>
                            </div>`;

                            // Replace the placeholder with the HTML
                            formattedSummary = formattedSummary.replace(imgMatch.placeholder, imageHtml);
                        });
                    }

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

                    // Consume credits after successful task completion
                    if (window.creditSystem) {
                        window.creditSystem.consumeCredits('prime_agent_task').then(result => {
                            if (result.success) {
                                console.log('Credits consumed successfully for Prime Agent task:', result.consumed);
                            } else {
                                console.warn('Failed to consume credits for Prime Agent task:', result.error);
                            }
                        }).catch(error => {
                            console.error('Error consuming credits for Prime Agent task:', error);
                        });
                    }

                    // Track successful activity in enhanced history
                    if (window.trackActivity) {
                        try {
                            // Get uploaded files if available
                            let currentUploadedFiles = [];
                            if (window.universalFileUpload) {
                                currentUploadedFiles = window.universalFileUpload.getFiles('task') || [];
                            }

                            window.trackActivity('agent_wave', 'task_execution', {
                                task_description: taskDescriptionValue,
                                files: currentUploadedFiles,
                                use_advanced_browser: true
                            }, {
                                task_summary: data.task_summary ? data.task_summary.substring(0, 500) + '...' : '',
                                has_screenshots: data.results && data.results.some(r => r.result && r.result.screenshot),
                                results_count: data.results ? data.results.length : 0
                            });
                        } catch (trackError) {
                            console.warn('Error tracking successful task activity:', trackError);
                        }
                    }

                    // Update the current summary container content
                    if (currentSummaryContainer) {
                        const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
                        if (summaryContentDiv) {
                            // Enhanced image processing for task summary
                            let combinedHtml = `${processedHtml}${screenshotsHtml}${webImagesHtml}`;

                            // Create a temporary div to hold the content
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = combinedHtml;

                            // Function to process HTML content in text nodes
                            const processHtmlInText = (element) => {
                                // Process all text nodes first
                                const walker = document.createTreeWalker(
                                    element,
                                    NodeFilter.SHOW_TEXT,
                                    null,
                                    false
                                );

                                const nodesToProcess = [];
                                let node;
                                while (node = walker.nextNode()) {
                                    if (node.textContent.includes('<div class="image-container"') ||
                                        node.textContent.includes('<img src=')) {
                                        nodesToProcess.push(node);
                                    }
                                }

                                // Now process the collected nodes
                                nodesToProcess.forEach(textNode => {
                                    const text = textNode.textContent;
                                    if (text.includes('<div class="image-container"') || text.includes('<img src=')) {
                                        // Create a temporary element
                                        const tempEl = document.createElement('div');
                                        tempEl.innerHTML = text;

                                        // Replace the text node with the parsed content
                                        const fragment = document.createDocumentFragment();
                                        while (tempEl.firstChild) {
                                            fragment.appendChild(tempEl.firstChild);
                                        }

                                        if (textNode.parentNode) {
                                            textNode.parentNode.replaceChild(fragment, textNode);
                                        }
                                    }
                                });

                                // Process all child elements recursively
                                Array.from(element.children).forEach(processHtmlInText);
                            };

                            // Process the temporary div
                            processHtmlInText(tempDiv);

                            // Now handle any elements that might contain HTML as text
                            const processElementContent = (element) => {
                                // Skip processing for script and style elements
                                if (element.tagName === 'SCRIPT' || element.tagName === 'STYLE') {
                                    return;
                                }

                                // Check if this element's innerHTML contains image HTML
                                const html = element.innerHTML;
                                if (html.includes('<div class="image-container"') ||
                                    (html.includes('<img src=') && html.includes('style='))) {

                                    // Only process if it looks like HTML in text, not actual elements
                                    if (element.querySelector('img') === null &&
                                        !element.innerHTML.includes('<div class="image-container"></div>')) {

                                        // Create a temporary element with the HTML content
                                        const tempEl = document.createElement('div');
                                        tempEl.innerHTML = html;

                                        // Replace the element's content
                                        element.innerHTML = '';
                                        while (tempEl.firstChild) {
                                            element.appendChild(tempEl.firstChild);
                                        }
                                    }
                                }

                                // Process all child elements recursively
                                Array.from(element.children).forEach(processElementContent);
                            };

                            // Process the temporary div again for element content
                            processElementContent(tempDiv);

                            // Clear the summary content div and append the processed content
                            summaryContentDiv.innerHTML = '';
                            while (tempDiv.firstChild) {
                                summaryContentDiv.appendChild(tempDiv.firstChild);
                            }

                            // Final pass to ensure all image containers are properly rendered
                            setTimeout(() => {
                                // Find any remaining unprocessed image containers
                                const textWithImages = Array.from(summaryContentDiv.querySelectorAll('p, div, span'))
                                    .filter(el => el.textContent.includes('<div class="image-container"') ||
                                                 el.textContent.includes('<img src='));

                                textWithImages.forEach(el => {
                                    if (el.innerHTML.includes('&lt;div class="image-container"') ||
                                        el.innerHTML.includes('&lt;img src=')) {
                                        // Handle HTML entities
                                        el.innerHTML = el.innerHTML
                                            .replace(/&lt;/g, '<')
                                            .replace(/&gt;/g, '>')
                                            .replace(/&quot;/g, '"')
                                            .replace(/&#39;/g, "'")
                                            .replace(/&amp;/g, '&');
                                    } else if (el.textContent.includes('<div class="image-container"') ||
                                              el.textContent.includes('<img src=')) {
                                        // Replace the element with its parsed content
                                        const tempEl = document.createElement('div');
                                        tempEl.innerHTML = el.textContent;
                                        el.parentNode.replaceChild(tempEl, el);
                                    }
                                });

                                // Track processed images to prevent duplicates
                                const processedImageSrcs = new Set();

                                // First, remove any duplicate image containers with the same image source
                                const allImageContainers = summaryContentDiv.querySelectorAll('.image-container');
                                allImageContainers.forEach(container => {
                                    const img = container.querySelector('img');
                                    if (img && img.src) {
                                        if (processedImageSrcs.has(img.src)) {
                                            // This is a duplicate, remove it
                                            container.parentNode.removeChild(container);
                                        } else {
                                            processedImageSrcs.add(img.src);
                                        }
                                    }
                                });

                                // Process remaining image containers - extract images from containers
                                const imageContainers = summaryContentDiv.querySelectorAll('.image-container');
                                console.log(`Found ${imageContainers.length} image containers to process in simple_input_fixed.js`);

                                imageContainers.forEach(container => {
                                    // Extract the image from the container
                                    const img = container.querySelector('img');
                                    if (!img) {
                                        // If no image found, just remove the empty container
                                        if (container.parentNode) {
                                            container.parentNode.removeChild(container);
                                        }
                                        return;
                                    }

                                    console.log(`Processing image: ${img.src ? img.src.substring(0, 30) + '...' : 'no src'}`);

                                    // Skip if already processed by image_processor.js
                                    if (img.hasAttribute('data-processed-by-image-processor')) {
                                        console.log('Image already processed by image_processor.js, skipping');
                                        return;
                                    }

                                    // Skip if we've already processed this image source
                                    if (img.src && processedImageSrcs.has(img.src)) {
                                        // Remove duplicate container
                                        container.parentNode.removeChild(container);
                                        return;
                                    }

                                    // Add to processed set
                                    if (img.src) {
                                        processedImageSrcs.add(img.src);
                                    }

                                    // Mark as processed
                                    img.setAttribute('data-processed-by-simple-input', 'true');

                                    // Extract caption if it exists
                                    const caption = container.querySelector('.image-caption');

                                    // Style the image directly with !important to override any other styles
                                    img.style.cssText = `
                                        max-width: 100% !important;
                                        height: auto !important;
                                        border-radius: 0.5rem !important;
                                        margin: 1.5rem auto !important;
                                        display: block !important;
                                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
                                        object-fit: contain !important;
                                    `;
                                    img.setAttribute('loading', 'lazy');

                                    // Insert the image before the container
                                    container.parentNode.insertBefore(img, container);

                                    // Check if there's already a caption after the image
                                    let existingCaption = img.nextElementSibling;
                                    if (existingCaption && existingCaption.classList.contains('image-caption')) {
                                        // There's already a caption, don't add another one
                                        console.log('Caption already exists, skipping');
                                    } else if (caption) {
                                        // Style the caption
                                        caption.style.cssText = `
                                            margin-top: 0.5rem !important;
                                            margin-bottom: 1.5rem !important;
                                            font-size: 0.9rem !important;
                                            color: #666 !important;
                                            font-style: italic !important;
                                            text-align: center !important;
                                            max-width: 90% !important;
                                            margin-left: auto !important;
                                            margin-right: auto !important;
                                        `;

                                        // Remove the caption from the container
                                        if (caption.parentNode === container) {
                                            container.removeChild(caption);
                                        }

                                        // Insert the caption after the image
                                        img.parentNode.insertBefore(caption, img.nextSibling);
                                    }

                                    // Remove the now-empty container
                                    container.parentNode.removeChild(container);

                                    console.log('Successfully extracted image from container');
                                });

                                // Process standalone images (not in containers)
                                const standaloneImages = Array.from(summaryContentDiv.querySelectorAll('img'))
                                    .filter(img => !img.closest('.image-container'));

                                console.log(`Found ${standaloneImages.length} standalone images to process in simple_input_fixed.js`);

                                standaloneImages.forEach(img => {
                                    // Skip if already processed by image_processor.js
                                    if (img.hasAttribute('data-processed-by-image-processor')) {
                                        console.log('Standalone image already processed by image_processor.js, skipping');
                                        return;
                                    }

                                    // Skip if we've already processed this image source
                                    if (img.src && processedImageSrcs.has(img.src)) {
                                        // Remove duplicate image
                                        img.parentNode.removeChild(img);
                                        return;
                                    }

                                    console.log(`Processing standalone image: ${img.src ? img.src.substring(0, 30) + '...' : 'no src'}`);

                                    // Add to processed set
                                    if (img.src) {
                                        processedImageSrcs.add(img.src);
                                    }

                                    // Mark as processed
                                    img.setAttribute('data-processed-by-simple-input', 'true');

                                    // Style the image directly with !important to override any other styles
                                    img.style.cssText = `
                                        max-width: 100% !important;
                                        height: auto !important;
                                        border-radius: 0.5rem !important;
                                        margin: 1.5rem auto !important;
                                        display: block !important;
                                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
                                        object-fit: contain !important;
                                    `;
                                    img.setAttribute('loading', 'lazy');

                                    // Check if there's already a caption after the image
                                    let existingCaption = img.nextElementSibling;
                                    if (existingCaption && existingCaption.classList.contains('image-caption')) {
                                        // There's already a caption, don't add another one
                                        console.log('Caption already exists for standalone image, skipping');
                                    } else if (img.alt && img.alt.trim() !== '') {
                                        // Create a caption from alt text if available
                                        const caption = document.createElement('div');
                                        caption.className = 'image-caption';
                                        caption.textContent = img.alt;

                                        // Style the caption
                                        caption.style.cssText = `
                                            margin-top: 0.5rem !important;
                                            margin-bottom: 1.5rem !important;
                                            font-size: 0.9rem !important;
                                            color: #666 !important;
                                            font-style: italic !important;
                                            text-align: center !important;
                                            max-width: 90% !important;
                                            margin-left: auto !important;
                                            margin-right: auto !important;
                                        `;

                                        // Insert the caption after the image
                                        if (img.nextSibling) {
                                            img.parentNode.insertBefore(caption, img.nextSibling);
                                        } else {
                                            img.parentNode.appendChild(caption);
                                        }
                                    }

                                    console.log('Successfully styled standalone image');
                                });
                            }, 100);
                        }
                    }

                    // Add event listeners for screenshot zoom buttons
                    document.querySelectorAll('.screenshot-zoom-btn').forEach(btn => {
                        if (!btn.hasAttribute('data-event-attached')) {
                            btn.setAttribute('data-event-attached', 'true');
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
                        }
                    });


                } else {
                    // Track unexpected response in enhanced history
                    if (window.trackActivity) {
                        try {
                            // Get uploaded files if available
                            let currentUploadedFiles = [];
                            if (window.universalFileUpload) {
                                currentUploadedFiles = window.universalFileUpload.getFiles('task') || [];
                            }

                            window.trackActivity('agent_wave', 'task_execution', {
                                task_description: taskDescriptionValue,
                                files: currentUploadedFiles,
                                use_advanced_browser: true
                            }, null, null, false, 'Server returned unexpected response');
                        } catch (trackError) {
                            console.warn('Error tracking unexpected response activity:', trackError);
                        }
                    }

                    // Display a generic error message in the current summary container
                    if (currentSummaryContainer) {
                        const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
                        if (summaryContentDiv) {
                            summaryContentDiv.innerHTML = `
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
                }
            })
            .catch(error => {
                console.error('Error executing task:', error);

                // Track failed activity in enhanced history
                if (window.trackActivity) {
                    try {
                        // Get uploaded files if available
                        let currentUploadedFiles = [];
                        if (window.universalFileUpload) {
                            currentUploadedFiles = window.universalFileUpload.getFiles('task') || [];
                        }

                        window.trackActivity('agent_wave', 'task_execution', {
                            task_description: taskDescriptionValue,
                            files: currentUploadedFiles,
                            use_advanced_browser: true
                        }, null, null, false, error.message || 'Network error during task execution');
                    } catch (trackError) {
                        console.warn('Error tracking failed task activity:', trackError);
                    }
                }

                if (currentSummaryContainer) {
                    const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
                    if (summaryContentDiv) {
                        summaryContentDiv.innerHTML = `
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
                }
            })
            .finally(() => {
                // Re-enable the button
                executeTaskBtn.disabled = false;
                executeTaskBtn.classList.remove('opacity-50', 'cursor-not-allowed');

                // Restore the button to its original state with the paper plane arrow icon
                executeTaskBtn.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>`;

                // Update the processing indicator to show completion
                if (processingIndicator) {
                    processingIndicator.classList.add('completed');
                }

                // Stop the thinking process
                if (window.stopThinkingProcess) {
                    console.log('Stopping enhanced thinking process in finally block');
                    // Pass the current thinking container ID
                    window.stopThinkingProcess(true, currentThinkingContainer.id); // Show completion message
                } else if (thinkingInterval) {
                    // Fallback to basic completion
                    clearInterval(thinkingInterval);

                    // Add a completion message to the current thinking process
                    if (currentThinkingContent) {
                        const completionP = document.createElement('div');
                        completionP.classList.add('text-green-600', 'mt-4', 'thinking-step');
                        completionP.innerHTML = '<strong>✓ Task completed!</strong>';
                        currentThinkingContent.appendChild(completionP);

                        // Scroll to bottom
                        const thinkingProcess = currentThinkingContainer.querySelector('.thinking-process');
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

    // Function to create a new thinking container
    function createThinkingContainer(taskDesc) {
        // For the first task, use the existing containers
        if (isFirstTask) {
            isFirstTask = false;

            // Update the initial container with the task description
            const shortDesc = taskDesc.length > 60 ? taskDesc.substring(0, 57) + '...' : taskDesc;

            // Update the thinking container header
            const thinkingHeader = currentThinkingContainer.querySelector('h4');
            if (thinkingHeader) {
                thinkingHeader.textContent = `Task: ${shortDesc}`;
            }

            // Update the summary container header
            const summaryHeader = currentSummaryContainer.querySelector('h4');
            if (summaryHeader) {
                summaryHeader.textContent = `Task Summary: ${shortDesc}`;
            }

            // Clear the thinking content
            if (currentThinkingContent) {
                currentThinkingContent.innerHTML = '<p class="typing-cursor">Starting analysis and planning process...</p>';
            }

            // Clear the summary content
            const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
            if (summaryContentDiv) {
                summaryContentDiv.innerHTML = '<p class="text-center text-gray-500">Processing task...</p>';
            }

            // Reset the processing indicator for the first task
            if (processingIndicator) {
                processingIndicator.classList.remove('completed');
            }

            return {
                thinkingContainer: currentThinkingContainer,
                thinkingContent: currentThinkingContent,
                summaryContainer: currentSummaryContainer
            };
        }

        // For subsequent tasks, create new containers
        // Increment task counter
        taskCounter++;

        // Create container IDs
        const thinkingId = `thinking-container-${taskCounter}`;
        const summaryId = `summary-container-${taskCounter}`;

        // Create new thinking container
        const thinkingContainer = document.createElement('div');
        thinkingContainer.className = 'thinking-container';
        thinkingContainer.id = thinkingId;

        // Create header with task description (truncated if needed)
        const shortDesc = taskDesc.length > 60 ? taskDesc.substring(0, 57) + '...' : taskDesc;

        thinkingContainer.innerHTML = `
            <div class="bg-gray-50 px-4 py-3 rounded-t-md border border-gray-200 flex justify-between items-center">
                <div class="flex items-center">
                    <button class="toggle-thinking-btn p-1 mr-2 rounded-md text-gray-500 hover:text-black hover:bg-gray-100" title="Toggle thinking process" data-container-id="${thinkingId}">
                        <svg class="w-4 h-4 transform rotate-0 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                    </button>
                    <h4 class="font-medium text-gray-700">Task: ${shortDesc}</h4>
                </div>
                <div class="flex space-x-1">
                    <button class="goto-summary-btn p-1 rounded-md text-gray-500 hover:text-black hover:bg-gray-100" title="Go to summary" data-task-id="${summaryId}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="thinking-process bg-gray-50 p-4 rounded-b-md border-l border-r border-b border-gray-200 h-64 overflow-auto">
                <div class="prose prose-sm max-w-none text-sm text-gray-500">
                    <p class="typing-cursor">Starting analysis and planning process...</p>
                </div>
            </div>
        `;

        // Create new summary container
        const summaryContainer = document.createElement('div');
        summaryContainer.className = 'summary-container';
        summaryContainer.id = summaryId;

        // Reset the processing indicator for subsequent tasks
        if (processingIndicator) {
            processingIndicator.classList.remove('completed');
        }

        // Reset the progress fill
        if (progressFill) {
            progressFill.style.width = '0%';
        }

        // Reset the step description
        if (stepDescription) {
            stepDescription.textContent = 'Analyzing your request and preparing execution plan';
        }

        summaryContainer.innerHTML = `
            <div class="bg-gray-50 px-4 py-3 rounded-t-md border border-gray-200 flex justify-between items-center summary-container-header">
                <h4 class="font-medium text-gray-700">Task Summary: ${shortDesc}</h4>
                <div class="flex space-x-1">
                    <!-- Download Icon -->
                    <button class="download-summary-btn p-1 rounded-md text-gray-500 hover:text-black hover:bg-gray-100" title="Download summary" data-task-id="${summaryId}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                        </svg>
                    </button>
                    <!-- Copy Icon -->
                    <button class="copy-summary-btn p-1 rounded-md text-gray-500 hover:text-black hover:bg-gray-100" title="Copy to clipboard" data-task-id="${summaryId}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
                        </svg>
                    </button>
                    <!-- Share Icon -->
                    <button class="share-summary-btn p-1 rounded-md text-gray-500 hover:text-black hover:bg-gray-100" title="Share summary" data-task-id="${summaryId}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path>
                        </svg>
                    </button>
                    <!-- Mobile Menu Button (only visible on small screens) -->
                    <button class="mobile-menu-btn md:hidden p-1 rounded-md text-gray-500 hover:text-black hover:bg-gray-100" data-task-id="${summaryId}">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
                        </svg>
                    </button>
                </div>
                <!-- Mobile Dropdown Menu -->
                <div class="mobile-dropdown absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 hidden" data-task-id="${summaryId}" style="top: 2.5rem;">
                    <button class="download-summary-btn block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left" data-task-id="${summaryId}">Download</button>
                    <button class="copy-summary-btn block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left" data-task-id="${summaryId}">Copy to clipboard</button>
                    <button class="share-summary-btn block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left" data-task-id="${summaryId}">Share</button>
                </div>
            </div>
            <div class="summary-container-content prose prose-img:rounded-lg prose-img:shadow-md prose-img:mx-auto prose-img:max-w-full p-4 border-l border-r border-b border-gray-200 rounded-b-md">
                <p class="text-center text-gray-500">Processing task...</p>
            </div>
        `;

        // Add containers to the DOM
        if (thinkingContainers) {
            thinkingContainers.prepend(thinkingContainer);
        }

        if (summaryContainers) {
            summaryContainers.prepend(summaryContainer);
        }

        // Update current containers
        currentThinkingContainer = thinkingContainer;
        currentThinkingContent = thinkingContainer.querySelector('.prose');
        currentSummaryContainer = summaryContainer;

        return {
            thinkingContainer,
            thinkingContent: currentThinkingContent,
            summaryContainer
        };
    }

    // Function to handle real-time thinking process
    let thinkingInterval = null;
    let currentThinkingStep = null;
    let currentWordIndex = 0;
    let currentWords = [];
    let currentStepText = '';
    let typingSpeed = 30; // milliseconds per word

    function simulateThinking() {
        // Create new containers for this task
        const taskDesc = taskDescription ? taskDescription.value.trim() : 'Unknown task';
        const { thinkingContent, thinkingContainer } = createThinkingContainer(taskDesc);

        if (!thinkingContent) return;

        // Clear previous content
        thinkingContent.innerHTML = '';

        // Make taskCounter available globally for the thinking process handler
        window.taskCounter = taskCounter;

        // Use our enhanced thinking process handler if available
        if (window.startThinkingProcess) {
            console.log('Using enhanced thinking process handler');
            // Pass the container ID to the thinking process handler
            window.startThinkingProcess(taskDesc, thinkingContainer.id);
        } else {
            console.log('Enhanced thinking process handler not available, using fallback');

            // Fallback to basic thinking display
            // Add initial placeholder with typing cursor
            const initialP = document.createElement('div');
            initialP.className = 'thinking-step mb-2';
            initialP.innerHTML = '<span class="typing-cursor">|</span>';
            thinkingContent.appendChild(initialP);

            // Set current step
            currentThinkingStep = initialP;
            currentWordIndex = 0;
            currentWords = [];
            currentStepText = '';
        }
    }

    // Function to update thinking process with real-time steps
    function updateThinkingProcess(message) {
        if (!currentThinkingContent) return;

        // Check if this is a new thinking step
        if (currentWords.length === 0) {
            // This is a new step, create a new element
            currentThinkingStep = document.createElement('div');
            currentThinkingStep.className = 'thinking-step mb-2';
            currentThinkingContent.appendChild(currentThinkingStep);

            // Split the message into words
            currentWords = message.split(' ');
            currentWordIndex = 0;
            currentStepText = '';

            // Start typing animation
            startTypingAnimation();

            // Scroll to the top of the thinking container to show the new content
            const thinkingProcess = currentThinkingContainer.querySelector('.thinking-process');
            if (thinkingProcess) {
                thinkingProcess.scrollTop = 0;
            }
        } else {
            // This is an existing step, just update the text
            // We'll handle this in the polling function
        }
    }

    // Function to animate typing word by word
    function startTypingAnimation() {
        // Clear any existing interval
        if (thinkingInterval) {
            clearInterval(thinkingInterval);
        }

        // Function to add the next word with a random delay for natural typing effect
        function addNextWord() {
            if (currentWordIndex >= currentWords.length) {
                // We've typed all words for this step
                // Remove typing cursor
                if (currentThinkingStep) {
                    // Use markdown-it if available
                    if (md) {
                        currentThinkingStep.innerHTML = md.render(currentStepText);
                    } else {
                        currentThinkingStep.textContent = currentStepText;
                    }
                }

                // Reset for next step
                currentWords = [];
                return;
            }

            // Add the next word
            currentStepText += (currentWordIndex > 0 ? ' ' : '') + currentWords[currentWordIndex];
            currentWordIndex++;

            // Update the element with the current text and cursor
            if (currentThinkingStep) {
                // Use markdown-it if available
                if (md) {
                    currentThinkingStep.innerHTML = md.render(currentStepText) + '<span class="typing-cursor">|</span>';
                } else {
                    currentThinkingStep.textContent = currentStepText;

                    // Add typing cursor
                    const cursor = document.createElement('span');
                    cursor.className = 'typing-cursor';
                    cursor.innerHTML = '|';
                    currentThinkingStep.appendChild(cursor);
                }
            }

            // Scroll to bottom of the current thinking container
            const thinkingProcess = currentThinkingContainer.querySelector('.thinking-process');
            if (thinkingProcess) {
                thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
            }

            // Schedule the next word with a random delay for natural typing effect
            const delay = Math.floor(Math.random() * 30) + 10; // 10-40ms delay
            setTimeout(addNextWord, delay);
        }

        // Start adding words
        addNextWord();
    }
    // Function to search for an image and insert it without a container
    window.searchAndInsertImageWithoutContainer = function(description, placeholderId) {
        console.log(`Searching for image: ${description} for placeholder: ${placeholderId}`);

        // Find the placeholder element
        const placeholder = document.getElementById(placeholderId);
        if (!placeholder) {
            console.error(`Placeholder not found: ${placeholderId}`);
            return;
        }

        // Make an API request to search for an image
        fetch(`/api/super-agent/search-image?query=${encodeURIComponent(description)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error searching for image:', data.error);
                    placeholder.innerHTML = `<p class="text-red-500">Error loading image: ${data.error}</p>`;
                    return;
                }

                if (data.image_url) {
                    // Create the image element
                    const img = document.createElement('img');
                    img.src = data.image_url;
                    img.alt = description;
                    img.style.cssText = `
                        max-width: 100% !important;
                        height: auto !important;
                        border-radius: 0.5rem !important;
                        margin: 1.5rem auto !important;
                        display: block !important;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
                        object-fit: contain !important;
                    `;
                    img.setAttribute('loading', 'lazy');
                    img.setAttribute('data-processed-by-image-processor', 'true');

                    // Create a caption
                    const caption = document.createElement('div');
                    caption.className = 'image-caption';
                    caption.textContent = description;
                    caption.style.cssText = `
                        margin-top: 0.5rem !important;
                        margin-bottom: 1.5rem !important;
                        font-size: 0.9rem !important;
                        color: #666 !important;
                        font-style: italic !important;
                        text-align: center !important;
                        max-width: 90% !important;
                        margin-left: auto !important;
                        margin-right: auto !important;
                    `;

                    // Replace the placeholder with the image and caption
                    placeholder.innerHTML = '';
                    placeholder.appendChild(img);
                    placeholder.appendChild(caption);
                } else {
                    console.error('No image URL returned');
                    placeholder.innerHTML = `<p class="text-gray-500">No image found for: ${description}</p>`;
                }
            })
            .catch(error => {
                console.error('Error fetching image:', error);
                placeholder.innerHTML = `<p class="text-red-500">Error loading image</p>`;
            });
    };

    // Function to detect LLM tool requests
    function detectAndHandleLLMTool(description) {
        const lowerDesc = description.toLowerCase();

        // Email Campaign Manager detection
        const emailPatterns = [
            /create\s+(?:an?\s+)?email\s+campaign/i,
            /generate\s+(?:an?\s+)?email\s+campaign/i,
            /email\s+marketing\s+campaign/i,
            /marketing\s+email/i,
            /email\s+newsletter/i,
            /promotional\s+email/i,
            /email\s+blast/i,
            /email\s+sequence/i
        ];

        for (const pattern of emailPatterns) {
            if (pattern.test(description)) {
                return {
                    tool: 'email-campaign',
                    params: extractEmailParams(description)
                };
            }
        }

        // SEO Content Optimizer detection
        const seoPatterns = [
            /optimize\s+(?:this\s+)?(?:for\s+)?seo/i,
            /optimize\s+(?:this\s+)?content/i,
            /seo\s+optimization/i,
            /improve\s+seo/i,
            /search\s+engine\s+optimization/i,
            /seo\s+content/i,
            /keyword\s+optimization/i,
            /meta\s+tags/i
        ];

        for (const pattern of seoPatterns) {
            if (pattern.test(description)) {
                return {
                    tool: 'seo-optimize',
                    params: extractSEOParams(description)
                };
            }
        }

        // Learning Path Generator detection
        const learningPatterns = [
            /create\s+(?:a\s+)?learning\s+path/i,
            /generate\s+(?:a\s+)?learning\s+path/i,
            /learning\s+curriculum/i,
            /study\s+plan/i,
            /course\s+curriculum/i,
            /learning\s+roadmap/i,
            /education\s+plan/i,
            /training\s+program/i,
            /learn\s+.+\s+step\s+by\s+step/i,
            /how\s+to\s+learn\s+/i
        ];

        for (const pattern of learningPatterns) {
            if (pattern.test(description)) {
                return {
                    tool: 'learning-path',
                    params: extractLearningParams(description)
                };
            }
        }

        return null;
    }

    // Function to extract email campaign parameters
    function extractEmailParams(description) {
        const params = {
            topic: '',
            audience: 'general audience',
            campaign_type: 'promotional',
            tone: 'professional'
        };

        // Extract topic - look for "about", "for", or quoted content
        const topicPatterns = [
            /(?:about|for|regarding)\s+([^.!?]+)/i,
            /"([^"]+)"/,
            /'([^']+)'/
        ];

        for (const pattern of topicPatterns) {
            const match = description.match(pattern);
            if (match) {
                params.topic = match[1].trim();
                break;
            }
        }

        // If no specific topic found, use the whole description
        if (!params.topic) {
            params.topic = description.replace(/create\s+(?:an?\s+)?email\s+campaign\s*/i, '').trim();
        }

        // Extract audience
        const audiencePatterns = [
            /(?:for|to|targeting)\s+([\w\s]+?)(?:\s+about|\s+regarding|$)/i,
            /audience:\s*([^.!?]+)/i
        ];

        for (const pattern of audiencePatterns) {
            const match = description.match(pattern);
            if (match) {
                params.audience = match[1].trim();
                break;
            }
        }

        // Extract campaign type
        if (/newsletter/i.test(description)) params.campaign_type = 'newsletter';
        else if (/welcome/i.test(description)) params.campaign_type = 'welcome';
        else if (/announcement/i.test(description)) params.campaign_type = 'announcement';

        // Extract tone
        if (/casual/i.test(description)) params.tone = 'casual';
        else if (/friendly/i.test(description)) params.tone = 'friendly';
        else if (/urgent/i.test(description)) params.tone = 'urgent';
        else if (/enthusiastic/i.test(description)) params.tone = 'enthusiastic';

        return params;
    }

    // Function to extract SEO parameters
    function extractSEOParams(description) {
        const params = {
            content: '',
            target_keywords: [],
            content_type: 'article'
        };

        // Extract content - look for quoted content or "this content"
        const contentPatterns = [
            /"([^"]+)"/,
            /'([^']+)'/,
            /optimize\s+this\s+content:\s*([^.!?]+)/i,
            /content:\s*([^.!?]+)/i
        ];

        for (const pattern of contentPatterns) {
            const match = description.match(pattern);
            if (match) {
                params.content = match[1].trim();
                break;
            }
        }

        // Extract keywords
        const keywordPatterns = [
            /keywords?\s*:\s*([^.!?]+)/i,
            /for\s+(?:the\s+)?keywords?\s+([^.!?]+)/i,
            /targeting\s+([^.!?]+)/i
        ];

        for (const pattern of keywordPatterns) {
            const match = description.match(pattern);
            if (match) {
                params.target_keywords = match[1].split(/[,\s]+/).filter(k => k.trim().length > 0);
                break;
            }
        }

        // Extract content type
        if (/blog\s+post/i.test(description)) params.content_type = 'blog_post';
        else if (/product\s+description/i.test(description)) params.content_type = 'product_description';
        else if (/landing\s+page/i.test(description)) params.content_type = 'landing_page';

        return params;
    }

    // Function to extract learning path parameters
    function extractLearningParams(description) {
        const params = {
            subject: '',
            skill_level: 'beginner',
            learning_style: 'mixed',
            time_commitment: 'moderate',
            goals: []
        };

        // Extract subject - look for "learn", "study", or quoted content
        const subjectPatterns = [
            /(?:learn|study|master)\s+([^.!?]+)/i,
            /(?:about|for)\s+([^.!?]+)/i,
            /"([^"]+)"/,
            /'([^']+)'/
        ];

        for (const pattern of subjectPatterns) {
            const match = description.match(pattern);
            if (match) {
                params.subject = match[1].trim();
                break;
            }
        }

        // Extract skill level
        if (/beginner/i.test(description)) params.skill_level = 'beginner';
        else if (/intermediate/i.test(description)) params.skill_level = 'intermediate';
        else if (/advanced/i.test(description)) params.skill_level = 'advanced';

        // Extract learning style
        if (/visual/i.test(description)) params.learning_style = 'visual';
        else if (/auditory/i.test(description)) params.learning_style = 'auditory';
        else if (/hands.?on|kinesthetic/i.test(description)) params.learning_style = 'kinesthetic';

        // Extract time commitment
        if (/intensive|fast.?track|quickly/i.test(description)) params.time_commitment = 'intensive';
        else if (/light|slowly|part.?time/i.test(description)) params.time_commitment = 'light';

        // Extract goals
        const goalPatterns = [
            /goals?\s*:\s*([^.!?]+)/i,
            /to\s+(become|get|achieve|master|understand)\s+([^.!?]+)/i
        ];

        for (const pattern of goalPatterns) {
            const match = description.match(pattern);
            if (match) {
                const goalText = match[1] || match[2];
                params.goals = goalText.split(/[,\s]+/).filter(g => g.trim().length > 0);
                break;
            }
        }

        return params;
    }

    // Function to handle LLM tool requests
    function handleLLMToolRequest(tool, params, originalDescription) {
        console.log(`Handling LLM tool request: ${tool}`, params);

        // Show a special message for LLM tools
        if (currentThinkingContent) {
            currentThinkingContent.innerHTML = `
                <div class="thinking-step">
                    <strong>🤖 Detected ${tool.replace('-', ' ')} request</strong>
                </div>
                <div class="thinking-step">
                    💭 Using advanced AI to generate high-quality content...
                </div>
                <div class="thinking-step">
                    ⚡ Processing with LLM-powered tools for best results
                </div>
            `;
        }

        // Make API request to the appropriate LLM tool endpoint
        const apiUrl = `/api/llm-tools/${tool}`;

        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        })
        .then(response => response.json())
        .then(data => {
            console.log('LLM tool response:', data);

            // Stop thinking process
            if (window.stopThinkingProcess) {
                window.stopThinkingProcess(true, currentThinkingContainer.id);
            }

            // Display the results
            displayLLMToolResults(tool, data, originalDescription);

            // Track successful LLM tool activity in enhanced history
            if (window.trackActivity) {
                try {
                    // Get uploaded files if available
                    let currentUploadedFiles = [];
                    if (window.universalFileUpload) {
                        currentUploadedFiles = window.universalFileUpload.getFiles('task') || [];
                    }

                    window.trackActivity('agent_wave', 'llm_tool', {
                        tool_type: tool,
                        description: originalDescription,
                        files: currentUploadedFiles
                    }, {
                        success: true,
                        tool_name: tool.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()),
                        result_type: data.data ? Object.keys(data.data).join(', ') : 'unknown'
                    });
                } catch (trackError) {
                    console.warn('Error tracking successful LLM tool activity:', trackError);
                }
            }

            // Re-enable the button
            executeTaskBtn.disabled = false;
            executeTaskBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            executeTaskBtn.innerHTML = 'Execute Task';
        })
        .catch(error => {
            console.error('LLM tool error:', error);

            // Track failed LLM tool activity in enhanced history
            if (window.trackActivity) {
                try {
                    // Get uploaded files if available
                    let currentUploadedFiles = [];
                    if (window.universalFileUpload) {
                        currentUploadedFiles = window.universalFileUpload.getFiles('task') || [];
                    }

                    window.trackActivity('agent_wave', 'llm_tool', {
                        tool_type: tool,
                        description: originalDescription,
                        files: currentUploadedFiles
                    }, null, null, false, `${tool.replace('-', ' ')} tool error: ${error.message}`);
                } catch (trackError) {
                    console.warn('Error tracking failed LLM tool activity:', trackError);
                }
            }

            // Stop thinking process
            if (window.stopThinkingProcess) {
                window.stopThinkingProcess(false, currentThinkingContainer.id);
            }

            // Display error
            if (currentSummaryContainer) {
                const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
                if (summaryContentDiv) {
                    summaryContentDiv.innerHTML = `
                        <div class="bg-white rounded-lg shadow-sm border border-red-200 overflow-hidden">
                            <div class="bg-red-50 px-6 py-4 border-b border-red-200">
                                <h3 class="text-lg font-semibold text-red-700 flex items-center">
                                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                                    </svg>
                                    Error
                                </h3>
                            </div>
                            <div class="p-6 text-red-700">
                                Failed to process ${tool.replace('-', ' ')} request: ${error.message}
                            </div>
                        </div>
                    `;
                }
            }

            // Re-enable the button
            executeTaskBtn.disabled = false;
            executeTaskBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            executeTaskBtn.innerHTML = 'Execute Task';
        });
    }

    // Function to display LLM tool results
    function displayLLMToolResults(tool, data, originalDescription) {
        if (!data || data.status !== 'success') {
            console.error('Invalid LLM tool response:', data);
            return;
        }

        const result = data.data;
        let formattedContent = '';

        // Format content based on tool type
        if (tool === 'email-campaign') {
            formattedContent = formatEmailCampaignResults(result);
        } else if (tool === 'seo-optimize') {
            formattedContent = formatSEOResults(result);
        } else if (tool === 'learning-path') {
            formattedContent = formatLearningPathResults(result);
        }

        // Display in summary container
        if (currentSummaryContainer && formattedContent) {
            const summaryContentDiv = currentSummaryContainer.querySelector('.summary-container-content');
            if (summaryContentDiv) {
                // Process as markdown
                const processedHtml = md ? md.render(formattedContent) : formattedContent.replace(/\n/g, '<br>');

                summaryContentDiv.innerHTML = `
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-semibold text-gray-900 flex items-center">
                                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>
                                ${tool.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} Results
                            </h3>
                        </div>
                        <div class="p-6 prose max-w-none">
                            ${processedHtml}
                        </div>
                    </div>
                `;
            }
        }
    }

    // Format email campaign results
    function formatEmailCampaignResults(result) {
        let content = `# Email Campaign: ${result.campaign_topic}\n\n`;

        content += `**Target Audience:** ${result.target_audience}\n`;
        content += `**Campaign Type:** ${result.campaign_type}\n`;
        content += `**Tone:** ${result.tone}\n\n`;

        // Subject lines
        if (result.subject_lines && result.subject_lines.length > 0) {
            content += `## Subject Line Options\n\n`;
            result.subject_lines.forEach((subject, index) => {
                content += `**${subject.variation}:** ${subject.text}\n`;
                content += `- Character count: ${subject.character_count}\n`;
                content += `- Predicted open rate: ${subject.predicted_open_rate?.toFixed(1)}%\n\n`;
            });
        }

        // Email body
        if (result.email_body) {
            content += `## Email Content\n\n`;
            content += `**Word count:** ${result.email_body.word_count}\n`;
            content += `**Estimated read time:** ${result.email_body.estimated_read_time}\n\n`;

            if (result.email_body.text_content) {
                content += `### Text Version\n\n`;
                content += result.email_body.text_content + '\n\n';
            }
        }

        // Performance metrics
        if (result.performance_metrics) {
            content += `## Performance Insights\n\n`;
            content += `**Expected open rate:** ${result.performance_metrics.expected_open_rate}\n`;
            content += `**Expected click rate:** ${result.performance_metrics.expected_click_rate}\n\n`;
        }

        return content;
    }

    // Format SEO results
    function formatSEOResults(result) {
        let content = `# SEO Content Optimization Results\n\n`;

        // Original vs optimized analysis
        if (result.current_analysis && result.optimized_analysis) {
            content += `## Content Analysis\n\n`;
            content += `**Original word count:** ${result.current_analysis.word_count}\n`;
            content += `**Optimized word count:** ${result.optimized_analysis.word_count}\n`;
            content += `**Readability score:** ${result.optimized_analysis.readability_score?.score || 'N/A'}\n\n`;
        }

        // Target keywords
        if (result.target_keywords && result.target_keywords.length > 0) {
            content += `## Target Keywords\n\n`;
            result.target_keywords.forEach(keyword => {
                content += `- ${keyword}\n`;
            });
            content += '\n';
        }

        // Optimized content
        if (result.optimized_content) {
            content += `## Optimized Content\n\n`;
            content += result.optimized_content + '\n\n';
        }

        // SEO recommendations
        if (result.recommendations && result.recommendations.length > 0) {
            content += `## SEO Recommendations\n\n`;
            result.recommendations.forEach(rec => {
                content += `### ${rec.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} (${rec.priority})\n`;
                content += `**Issue:** ${rec.issue}\n`;
                content += `**Recommendation:** ${rec.recommendation}\n`;
                content += `**Impact:** ${rec.impact}\n\n`;
            });
        }

        // Meta tags
        if (result.meta_tags) {
            content += `## Meta Tags\n\n`;
            content += `**Title:** ${result.meta_tags.title}\n`;
            content += `**Description:** ${result.meta_tags.description}\n`;
            if (result.meta_tags.keywords) {
                content += `**Keywords:** ${result.meta_tags.keywords}\n`;
            }
            content += '\n';
        }

        return content;
    }

    // Format learning path results
    function formatLearningPathResults(result) {
        let content = `# Learning Path: ${result.subject}\n\n`;

        content += `**Skill Level:** ${result.skill_level}\n`;
        content += `**Learning Style:** ${result.learning_style}\n`;
        content += `**Time Commitment:** ${result.time_commitment}\n\n`;

        // Curriculum
        if (result.curriculum && result.curriculum.modules) {
            content += `## Curriculum Overview\n\n`;
            content += `**Total Modules:** ${result.curriculum.total_modules}\n`;
            content += `**Total Duration:** ${result.curriculum.total_duration_weeks} weeks\n\n`;

            content += `## Learning Modules\n\n`;
            result.curriculum.modules.forEach((module, index) => {
                content += `### Module ${module.id}: ${module.title}\n\n`;
                content += `**Duration:** ${module.duration_weeks} weeks\n`;
                content += `**Difficulty:** ${module.difficulty}\n\n`;

                if (module.description) {
                    content += `**Description:** ${module.description}\n\n`;
                }

                if (module.learning_objectives && module.learning_objectives.length > 0) {
                    content += `**Learning Objectives:**\n`;
                    module.learning_objectives.forEach(obj => {
                        content += `- ${obj}\n`;
                    });
                    content += '\n';
                }

                if (module.key_concepts && module.key_concepts.length > 0) {
                    content += `**Key Concepts:**\n`;
                    module.key_concepts.forEach(concept => {
                        content += `- ${concept}\n`;
                    });
                    content += '\n';
                }

                if (module.practical_exercises && module.practical_exercises.length > 0) {
                    content += `**Practical Exercises:**\n`;
                    module.practical_exercises.forEach(exercise => {
                        content += `- ${exercise}\n`;
                    });
                    content += '\n';
                }
            });
        }

        // Resources
        if (result.resources && result.resources.length > 0) {
            content += `## Recommended Resources\n\n`;
            result.resources.forEach(resource => {
                content += `### ${resource.title}\n`;
                content += `**Type:** ${resource.type}\n`;
                if (resource.url) {
                    content += `**Link:** [${resource.title}](${resource.url})\n`;
                }
                if (resource.description) {
                    content += `**Description:** ${resource.description}\n`;
                }
                content += '\n';
            });
        }

        return content;
    }
});