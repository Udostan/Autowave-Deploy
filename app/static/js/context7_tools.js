/**
 * Prime Agent Tools JavaScript
 * Handles execution of advanced AI tools with thinking simulation
 */

class PrimeAgentTools {
    constructor() {
        this.currentTaskId = null;
        this.eventSource = null;
        this.isExecuting = false;
        this.thinkingInterval = null;
        this.currentStep = 0;
        this.thinkingSteps = [];
        this.displayedSteps = new Set();
        this.thinkingCycles = 0;
        this.isTaskComplete = false;
        this.init();
    }

    init() {
        // Bind event listeners
        document.getElementById('executeTaskBtn').addEventListener('click', () => this.executeTask());
        document.getElementById('taskDescription').addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.executeTask();
            }
        });

        // Clear tasks button
        document.getElementById('clearAllTasksBtn').addEventListener('click', () => this.clearAllTasks());

        // Toggle summary button
        document.getElementById('toggleSummaryBtn').addEventListener('click', () => this.toggleSummary());

        // Copy, download, share buttons
        this.bindActionButtons();

        // Check for URL parameters to auto-execute
        this.checkUrlParameters();

        // Add escape key handler for closing expanded summary
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const resultsContainer = document.getElementById('resultsContainer');
                if (resultsContainer && resultsContainer.classList.contains('summary-expanded')) {
                    this.toggleSummary();
                }
            }
        });
    }

    checkUrlParameters() {
        // First check for initial task from template (from homepage tab selection)
        const initialTaskElement = document.getElementById('initial-task-data');
        let task = null;

        if (initialTaskElement) {
            task = initialTaskElement.textContent.trim();
        }

        // If no initial task from template, check URL parameters
        if (!task) {
            const urlParams = new URLSearchParams(window.location.search);
            task = urlParams.get('task');
        }

        if (task) {
            document.getElementById('taskDescription').value = task;
            // Auto-execute after a short delay to allow UI to load
            setTimeout(() => {
                this.executeTask();
            }, 500);
        }
    }

    async executeTask() {
        const taskDescription = document.getElementById('taskDescription').value.trim();

        if (!taskDescription) {
            this.showError('Please enter a task description');
            return;
        }

        // Check credits before executing task
        if (window.creditSystem) {
            const canProceed = await window.creditSystem.enforceCredits('context7_package_tracking');
            if (!canProceed) {
                console.log('Insufficient credits for Context7 Tools');
                return;
            }
        }

        // Get uploaded files if available
        let fileContent = '';
        if (window.universalFileUpload) {
            fileContent = window.universalFileUpload.getFileContentForAI('context7');
        }

        if (this.isExecuting) {
            this.showError('A task is already executing. Please wait...');
            return;
        }

        this.isExecuting = true;
        this.isTaskComplete = false;
        this.showResults();

        // Initialize thinking simulation
        this.initializeThinkingSteps(taskDescription);
        this.startThinkingSimulation();

        // Start with initial progress
        this.updateProgress('Analyzing your request and preparing execution plan', 0);

        try {
            // Call advanced AI tools API
            const response = await fetch('/api/context7-tools/execute-task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    task: taskDescription + fileContent
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to start task execution');
            }

            this.currentTaskId = data.task_id;

            // Start streaming progress
            this.startProgressStream();

        } catch (error) {
            console.error('Error executing task:', error);
            this.showError(`Error: ${error.message}`);
            this.isExecuting = false;
            this.stopThinkingSimulation();
        }
    }

    startProgressStream() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource(`/api/context7-tools/stream-task?task_id=${this.currentTaskId}`);

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleProgressUpdate(data);
            } catch (error) {
                console.error('Error parsing progress data:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            this.eventSource.close();
            this.checkTaskStatus();
        };
    }

    initializeThinkingSteps(taskDesc) {
        this.currentStep = 0;
        this.displayedSteps.clear();
        this.thinkingCycles = 0;

        // Generate initial thinking steps based on task
        this.thinkingSteps = this.generateInitialSteps(taskDesc);
    }

    generateInitialSteps(taskDesc) {
        const steps = [
            "🧠 Analyzing your request and understanding the requirements...",
            "📋 Breaking down the task into manageable components...",
            "🔍 Identifying the best approach and tools needed...",
            "⚡ Initializing AI systems and preparing execution environment...",
            "🌐 Connecting to web resources and data sources...",
            "📊 Setting up analysis frameworks and processing pipelines...",
            "🎯 Focusing on delivering accurate and comprehensive results...",
            "🔄 Beginning systematic information gathering and processing..."
        ];

        // Add task-specific steps based on keywords
        if (taskDesc.toLowerCase().includes('flight') || taskDesc.toLowerCase().includes('book')) {
            steps.push("✈️ Accessing flight booking systems and airline databases...");
            steps.push("💰 Analyzing pricing data and availability across multiple carriers...");
        }

        if (taskDesc.toLowerCase().includes('hotel') || taskDesc.toLowerCase().includes('accommodation')) {
            steps.push("🏨 Connecting to hotel booking platforms and reservation systems...");
            steps.push("📍 Analyzing location data and accommodation options...");
        }

        if (taskDesc.toLowerCase().includes('business') || taskDesc.toLowerCase().includes('plan')) {
            steps.push("📈 Researching market conditions and industry trends...");
            steps.push("💼 Analyzing business models and competitive landscape...");
        }

        return steps;
    }

    generateMoreSteps(taskDesc, cycle) {
        const moreSteps = [
            "🔄 Continuing deep analysis and data processing...",
            "📊 Cross-referencing multiple data sources for accuracy...",
            "🎯 Refining results and ensuring quality standards...",
            "⚡ Optimizing performance and processing efficiency...",
            "🌟 Applying advanced AI algorithms for better insights...",
            "🔍 Conducting thorough verification and validation...",
            "📋 Organizing information for clear presentation...",
            "🎨 Formatting results for optimal user experience..."
        ];

        // Add cycle-specific variations
        if (cycle > 1) {
            moreSteps.push("🚀 Applying enhanced processing techniques...");
            moreSteps.push("💡 Generating additional insights and recommendations...");
        }

        return moreSteps;
    }

    startThinkingSimulation() {
        if (this.thinkingInterval) {
            clearInterval(this.thinkingInterval);
        }

        // Clear previous thinking content
        const thinkingContent = document.getElementById('thinkingContent');
        thinkingContent.innerHTML = '';

        let allSteps = [...this.thinkingSteps];

        this.thinkingInterval = setInterval(() => {
            // Check if task is complete
            if (this.isTaskComplete) {
                this.displayThinkingStep("✅ Task completed successfully! Results are displayed below.");
                clearInterval(this.thinkingInterval);
                this.thinkingInterval = null;
                return;
            }

            // If we've shown all steps, generate more
            if (this.currentStep >= allSteps.length) {
                this.thinkingCycles++;
                const moreSteps = this.generateMoreSteps(document.getElementById('taskDescription').value, this.thinkingCycles);
                const newSteps = moreSteps.filter(step => !this.displayedSteps.has(step));
                allSteps = [...allSteps, ...newSteps];
            }

            // Display next step if available
            if (this.currentStep < allSteps.length) {
                const step = allSteps[this.currentStep];

                // Use typing animation for some steps
                if (Math.random() > 0.7) {
                    this.displayThinkingStepWithTyping(step);
                } else {
                    this.displayThinkingStep(step);
                }

                this.displayedSteps.add(step);
                this.currentStep++;
            }
        }, 2000); // Show a new step every 2 seconds
    }

    stopThinkingSimulation(showCompletionMessage = true) {
        this.isTaskComplete = true;

        if (this.thinkingInterval) {
            clearInterval(this.thinkingInterval);
            this.thinkingInterval = null;
        }

        if (showCompletionMessage) {
            setTimeout(() => {
                this.displayThinkingStep("✅ Task completed successfully! Results are displayed below.");
            }, 500);
        }
    }

    displayThinkingStep(step) {
        const thinkingContent = document.getElementById('thinkingContent');
        const stepDiv = document.createElement('div');
        stepDiv.className = 'thinking-step mb-2 opacity-0 transform translate-y-2';
        stepDiv.innerHTML = `<p class="text-gray-300">${step}</p>`;

        thinkingContent.appendChild(stepDiv);

        // Animate in
        setTimeout(() => {
            stepDiv.classList.remove('opacity-0', 'transform', 'translate-y-2');
            stepDiv.classList.add('opacity-100');
        }, 50);

        // Scroll to bottom
        thinkingContent.scrollTop = thinkingContent.scrollHeight;
    }

    displayThinkingStepWithTyping(step) {
        const thinkingContent = document.getElementById('thinkingContent');
        const stepDiv = document.createElement('div');
        stepDiv.className = 'thinking-step mb-2';
        stepDiv.innerHTML = `<p class="text-gray-300"></p>`;

        thinkingContent.appendChild(stepDiv);

        const textElement = stepDiv.querySelector('p');
        let i = 0;

        const typeInterval = setInterval(() => {
            if (i < step.length) {
                textElement.textContent += step.charAt(i);
                i++;
            } else {
                clearInterval(typeInterval);
            }
        }, 30);

        // Scroll to bottom
        thinkingContent.scrollTop = thinkingContent.scrollHeight;
    }

    handleProgressUpdate(data) {
        if (data.status === 'started') {
            this.updateProgress('AI processing initiated...', 40);
        } else if (data.status === 'complete') {
            this.handleTaskComplete(data.result);
        } else if (data.status === 'error') {
            this.handleTaskError(data.result);
        } else if (data.stage) {
            // Progress update - add real progress steps to thinking
            this.displayThinkingStep(`🔄 ${data.message || data.stage}`);
            if (data.progress) {
                this.updateProgress(data.message || data.stage, data.progress);
            }
        }
    }

    async checkTaskStatus() {
        if (!this.currentTaskId) return;

        try {
            const response = await fetch(`/api/context7-tools/task-status?task_id=${this.currentTaskId}`);
            const data = await response.json();

            if (data.success && data.status === 'complete') {
                this.handleTaskComplete(data.result);
            } else if (data.success && data.status === 'error') {
                this.handleTaskError(data.result);
            } else {
                // Still processing, check again in a moment
                setTimeout(() => this.checkTaskStatus(), 2000);
            }
        } catch (error) {
            console.error('Error checking task status:', error);
            this.showError('Error checking task status');
        }
    }

    handleTaskComplete(result) {
        this.isExecuting = false;
        this.stopThinkingSimulation();
        this.updateProgress('Task execution completed successfully!', 100);

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        // Consume credits after successful task completion
        if (window.creditSystem) {
            window.creditSystem.consumeCredits('context7_package_tracking').then(result => {
                if (result.success) {
                    console.log('Credits consumed successfully for Context7 Tools:', result.consumed);
                } else {
                    console.warn('Failed to consume credits for Context7 Tools:', result.error);
                }
            }).catch(error => {
                console.error('Error consuming credits for Context7 Tools:', error);
            });
        }

        // Show completion indicator
        this.showCompletionIndicator();

        // Display results
        if (result && result.task_summary) {
            this.displayTaskSummary(result.task_summary);
        } else if (result && result.result) {
            this.displayTaskSummary(result.result);
        } else {
            this.displayTaskSummary('Task completed successfully!');
        }

        // Final thinking step is handled by stopThinkingSimulation
    }

    handleTaskError(result) {
        this.isExecuting = false;

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }

        const errorMessage = result?.error || result?.message || 'An error occurred during task execution';
        this.showError(errorMessage);

        // Display error in summary if available
        if (result && result.task_summary) {
            this.displayTaskSummary(result.task_summary);
        }
    }

    showResults() {
        document.getElementById('resultsContainer').classList.remove('hidden');

        // Reset progress
        this.updateProgress('Initializing AI systems...', 0);

        // Clear previous thinking content
        const thinkingContent = document.getElementById('thinkingContent');
        thinkingContent.innerHTML = '';

        // Clear previous summary
        const summaryContent = document.querySelector('.summary-container-content');
        summaryContent.innerHTML = '<div class="text-center text-gray-500"><p>Processing your request...</p></div>';
    }

    updateProgress(message, percentage) {
        document.getElementById('stepDescription').textContent = message;
        document.getElementById('progressFill').style.width = `${percentage}%`;

        // Update processing indicator
        const indicator = document.getElementById('processingIndicator');
        if (percentage >= 100) {
            indicator.querySelector('div').classList.remove('animate-spin');
            indicator.querySelector('.checkmark').style.display = 'block';
        } else {
            indicator.querySelector('div').classList.add('animate-spin');
            indicator.querySelector('.checkmark').style.display = 'none';
        }
    }



    displayTaskSummary(content) {
        const summaryContent = document.querySelector('.summary-container-content');

        // Convert markdown to HTML if needed
        let htmlContent = content;
        if (typeof content === 'string') {
            // First, preserve existing HTML tags (like img tags)
            const htmlTags = [];
            let tempContent = content;

            // Extract and preserve HTML tags
            tempContent = tempContent.replace(/<[^>]+>/g, (match) => {
                const index = htmlTags.length;
                htmlTags.push(match);
                return `__HTML_TAG_${index}__`;
            });

            // Enhanced markdown conversion with proper header support
            htmlContent = tempContent
                .replace(/^#### (.*$)/gim, '<h4 class="text-base font-semibold mb-2 text-blue-400">$1</h4>')
                .replace(/^### (.*$)/gim, '<h3 class="text-lg font-medium mb-2 text-purple-400">$1</h3>')
                .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold mb-3 text-green-400">$1</h2>')
                .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mb-4 text-white">$1</h1>')
                .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-yellow-300">$1</strong>')
                .replace(/\*(.*?)\*/g, '<em class="italic text-gray-300">$1</em>')
                .replace(/^\* (.*$)/gim, '<li class="ml-4 text-gray-200">$1</li>')
                .replace(/^- (.*$)/gim, '<li class="ml-4 text-gray-200">$1</li>')
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-400 hover:text-purple-300 underline" target="_blank">$1</a>')
                .replace(/\n/g, '<br>');

            // Restore HTML tags
            htmlTags.forEach((tag, index) => {
                htmlContent = htmlContent.replace(`__HTML_TAG_${index}__`, tag);
            });
        }

        summaryContent.innerHTML = htmlContent;
    }

    showCompletionIndicator() {
        const indicator = document.getElementById('processingIndicator');
        indicator.querySelector('div').classList.remove('animate-spin');
        indicator.querySelector('div').classList.add('bg-green-600');
        indicator.querySelector('.checkmark').style.display = 'block';
    }

    showError(message) {
        this.updateProgress(`❌ Error: ${message}`, 0);
        this.addThinkingStep('❌ Error', message);

        // Reset execution state
        this.isExecuting = false;

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    clearAllTasks() {
        // Reset UI
        document.getElementById('resultsContainer').classList.add('hidden');
        document.getElementById('taskDescription').value = '';

        // Clear uploaded files
        if (window.universalFileUpload) {
            window.universalFileUpload.clearFiles('context7');
        }

        // Reset state
        this.currentTaskId = null;
        this.isExecuting = false;

        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    toggleSummary() {
        const resultsContainer = document.getElementById('resultsContainer');
        const taskSummaryContainer = document.getElementById('taskSummaryContainer');
        const toggleSummaryBtn = document.getElementById('toggleSummaryBtn');
        const taskProgressContainer = document.querySelector('#resultsContainer .grid > div:first-child');

        if (!resultsContainer || !taskSummaryContainer || !toggleSummaryBtn) {
            console.warn('Required elements not found for summary toggle');
            return;
        }

        // Toggle the expanded class on the results container
        resultsContainer.classList.toggle('summary-expanded');

        // Update the toggle icon and title
        if (resultsContainer.classList.contains('summary-expanded')) {
            // Change to expanded state
            toggleSummaryBtn.title = "Collapse task summary section";

            // Hide the task progress container
            if (taskProgressContainer) {
                taskProgressContainer.style.display = 'none';
            }

            // Make the task summary container take full width
            taskSummaryContainer.style.gridColumn = '1 / -1';

            // Prevent body scrolling
            document.body.style.overflow = 'hidden';
        } else {
            // Change to normal state
            toggleSummaryBtn.title = "Expand task summary section";

            // Show the task progress container
            if (taskProgressContainer) {
                taskProgressContainer.style.display = '';
            }

            // Reset the task summary container width
            taskSummaryContainer.style.gridColumn = '';

            // Restore body scrolling
            document.body.style.overflow = '';
        }
    }

    bindActionButtons() {
        // Enhanced event delegation for all action buttons
        document.body.addEventListener('click', (event) => {
            console.log('Prime Agent Tools - Body click detected:', event.target, 'Classes:', event.target.className);

            // Check if the clicked element is a download-summary-btn or one of its children
            const downloadBtn = event.target.closest('.download-summary-btn');
            if (downloadBtn) {
                console.log('Prime Agent Tools - Download button clicked!', downloadBtn);
                event.preventDefault();
                event.stopPropagation();

                // Show download options menu
                this.showDownloadOptionsMenu(downloadBtn);
                return;
            }

            // Check if the clicked element is a copy-summary-btn or one of its children
            const copyBtn = event.target.closest('.copy-summary-btn');
            if (copyBtn) {
                console.log('Prime Agent Tools - Copy button clicked!', copyBtn);
                event.preventDefault();
                event.stopPropagation();

                const taskId = copyBtn.getAttribute('data-task-id');
                this.copyToClipboard(taskId);
                return;
            }

            // Check if the clicked element is a share-summary-btn or one of its children
            const shareBtn = event.target.closest('.share-summary-btn');
            if (shareBtn) {
                console.log('Prime Agent Tools - Share button clicked!', shareBtn);
                event.preventDefault();
                event.stopPropagation();

                const taskId = shareBtn.getAttribute('data-task-id');
                this.shareSummary(taskId);
                return;
            }
        });
    }

    // Show download options menu
    showDownloadOptionsMenu(downloadBtn) {
        // Remove any existing menu
        const existingMenu = document.querySelector('.download-options-menu');
        if (existingMenu) {
            existingMenu.remove();
        }

        const taskId = downloadBtn.getAttribute('data-task-id');

        // Create download options menu
        const menu = document.createElement('div');
        menu.className = 'download-options-menu absolute bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-2 min-w-48';
        menu.style.top = '100%';
        menu.style.right = '0';
        menu.style.marginTop = '4px';

        menu.innerHTML = `
            <button class="download-html-btn w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center" data-task-id="${taskId}">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                </svg>
                Download as HTML
            </button>
            <button class="download-pdf-btn w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center" data-task-id="${taskId}">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                Download as PDF
            </button>
        `;

        // Position the menu relative to the download button
        downloadBtn.style.position = 'relative';
        downloadBtn.appendChild(menu);

        // Add event listeners for menu options
        menu.querySelector('.download-html-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.downloadAsHTML(taskId);
            menu.remove();
        });

        menu.querySelector('.download-pdf-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.downloadAsPDF(taskId);
            menu.remove();
        });

        // Close menu when clicking outside
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target)) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 100);
    }

    copyToClipboard(taskId) {
        console.log('Prime Agent Tools - Copy for task:', taskId);

        const summaryContainer = document.getElementById(taskId);
        if (!summaryContainer) {
            console.error('Summary container not found');
            return;
        }

        const contentDiv = summaryContainer.querySelector('.summary-container-content');
        if (!contentDiv) {
            console.error('Content div not found');
            return;
        }

        // Get the text content - if empty, create a default message
        let textContent = contentDiv.innerText.trim();
        if (!textContent || textContent === 'Prime Agent Tools Ready\nSelect a tool above or enter your task to get started') {
            textContent = `Prime Agent Tools Summary

Date: ${new Date().toLocaleDateString()}
Time: ${new Date().toLocaleTimeString()}

This is a sample task summary from AutoWave Prime Agent Tools. Your actual task results will appear here when you run a task.

Generated by AutoWave Prime Agent Tools - https://autowave.pro`;
        }

        console.log('Text content to copy:', textContent);

        // Copy to clipboard
        navigator.clipboard.writeText(textContent)
            .then(() => {
                console.log('Text copied to clipboard successfully');

                // Show success feedback with toast
                this.showToast('✅ Content copied to clipboard!', 'success');
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);

                // Try alternative method for older browsers
                try {
                    const textArea = document.createElement('textarea');
                    textArea.value = textContent;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);

                    this.showToast('✅ Content copied to clipboard!', 'success');
                } catch (fallbackErr) {
                    console.error('Fallback copy method also failed:', fallbackErr);
                    this.showToast('❌ Failed to copy content. Please try again.', 'error');
                }
            });
    }

    // Download as HTML function
    downloadAsHTML(taskId) {
        console.log('Prime Agent Tools - Downloading as HTML for task:', taskId);

        const summaryContainer = document.getElementById(taskId);
        if (!summaryContainer) {
            console.error('Summary container not found');
            return;
        }

        const contentDiv = summaryContainer.querySelector('.summary-container-content');
        if (!contentDiv) {
            console.error('Content div not found');
            return;
        }

        // Get the content - if empty, create a default message
        let htmlContent = contentDiv.innerHTML.trim();
        if (!htmlContent || htmlContent.includes('Prime Agent Tools Ready')) {
            htmlContent = `
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Prime Agent Tools Summary</h2>
                    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    <p>This is a sample task summary. Your actual task results will appear here when you run a task.</p>
                    <hr>
                    <p><em>Generated by AutoWave Prime Agent Tools</em></p>
                </div>
            `;
        }

        // Create a complete HTML document
        const fullHtmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prime Agent Tools Summary</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; background: white; color: #333; }
        h1, h2, h3 { color: #333; }
        .header { border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
        .footer { border-top: 2px solid #eee; padding-top: 20px; margin-top: 20px; color: #666; }
        img { max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; }
        ul, ol { padding-left: 20px; }
        li { margin-bottom: 5px; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AutoWave Prime Agent Tools - Task Summary</h1>
        <p>Generated on: ${new Date().toLocaleString()}</p>
    </div>
    <div class="content">
        ${htmlContent}
    </div>
    <div class="footer">
        <p>Generated by AutoWave Prime Agent Tools | <a href="https://autowave.pro">autowave.pro</a></p>
    </div>
</body>
</html>`;

        const blob = new Blob([fullHtmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);

        // Create filename
        const filename = 'prime_agent_tools_' + new Date().toISOString().slice(0, 10) + '.html';

        // Create a temporary link and trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();

        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);

        this.showToast('✅ HTML file downloaded successfully!', 'success');
        console.log('HTML download completed successfully!');
    }

    // Download as PDF function
    downloadAsPDF(taskId) {
        console.log('Prime Agent Tools - Downloading as PDF for task:', taskId);

        const summaryContainer = document.getElementById(taskId);
        if (!summaryContainer) {
            console.error('Summary container not found');
            this.showToast('❌ Error: Content not found', 'error');
            return;
        }

        const contentDiv = summaryContainer.querySelector('.summary-container-content');
        if (!contentDiv) {
            console.error('Content div not found');
            this.showToast('❌ Error: Content not found', 'error');
            return;
        }

        // Check if html2pdf is available
        if (typeof html2pdf === 'undefined') {
            console.error('html2pdf library not loaded');
            this.showToast('❌ PDF generation library not available', 'error');
            return;
        }

        // Get the content - if empty, create a default message
        let htmlContent = contentDiv.innerHTML.trim();
        if (!htmlContent || htmlContent.includes('Prime Agent Tools Ready')) {
            htmlContent = `
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Prime Agent Tools Summary</h2>
                    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    <p>This is a sample task summary. Your actual task results will appear here when you run a task.</p>
                    <hr>
                    <p><em>Generated by AutoWave Prime Agent Tools</em></p>
                </div>
            `;
        }

        const filename = 'prime_agent_tools_' + new Date().toISOString().slice(0, 10) + '.pdf';

        // Create a temporary container for PDF generation
        const pdfContainer = document.createElement('div');
        pdfContainer.style.position = 'absolute';
        pdfContainer.style.left = '-9999px';
        pdfContainer.style.top = '-9999px';
        pdfContainer.style.width = '210mm'; // A4 width
        pdfContainer.style.fontFamily = 'Arial, sans-serif';
        pdfContainer.style.fontSize = '12px';
        pdfContainer.style.lineHeight = '1.6';
        pdfContainer.style.color = '#333';
        pdfContainer.style.background = 'white';
        pdfContainer.style.padding = '20px';

        pdfContainer.innerHTML = `
            <div style="border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 20px;">
                <h1 style="color: #333; margin: 0 0 10px 0; font-size: 24px;">AutoWave Prime Agent Tools - Task Summary</h1>
                <p style="margin: 0; color: #666;">Generated on: ${new Date().toLocaleString()}</p>
            </div>
            <div style="margin-bottom: 30px;">
                ${htmlContent}
            </div>
            <div style="border-top: 2px solid #eee; padding-top: 20px; margin-top: 20px; color: #666; font-size: 10px;">
                <p style="margin: 0;">Generated by AutoWave Prime Agent Tools | autowave.pro</p>
            </div>
        `;

        document.body.appendChild(pdfContainer);

        // Show loading toast
        this.showToast('📄 Generating PDF...', 'info');

        // Configure PDF options
        const options = {
            margin: 10,
            filename: filename,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: {
                scale: 2,
                useCORS: true,
                allowTaint: true,
                backgroundColor: '#ffffff'
            },
            jsPDF: {
                unit: 'mm',
                format: 'a4',
                orientation: 'portrait',
                compress: true
            }
        };

        // Generate and download PDF
        html2pdf().from(pdfContainer).set(options).save().then(() => {
            console.log('PDF download completed successfully!');
            this.showToast('✅ PDF downloaded successfully!', 'success');

            // Clean up
            document.body.removeChild(pdfContainer);
        }).catch((error) => {
            console.error('PDF generation failed:', error);
            this.showToast('❌ PDF generation failed. Please try again.', 'error');

            // Clean up
            if (document.body.contains(pdfContainer)) {
                document.body.removeChild(pdfContainer);
            }
        });
    }

    shareSummary(taskId) {
        console.log('Prime Agent Tools - Share for task:', taskId);

        const summaryContainer = document.getElementById(taskId);
        if (!summaryContainer) {
            console.error('Summary container not found for share');
            return;
        }

        const contentDiv = summaryContainer.querySelector('.summary-container-content');
        if (!contentDiv) {
            console.error('Content div not found for share');
            return;
        }

        // Get the text content - if empty, create a default message
        let textContent = contentDiv.innerText.trim();
        if (!textContent || textContent === 'Prime Agent Tools Ready\nSelect a tool above or enter your task to get started') {
            textContent = `Prime Agent Tools Summary

Date: ${new Date().toLocaleDateString()}
Time: ${new Date().toLocaleTimeString()}

This is a sample task summary from AutoWave Prime Agent Tools. Your actual task results will appear here when you run a task.

Generated by AutoWave Prime Agent Tools - https://autowave.pro`;
        }

        // Create share data
        const shareData = {
            title: `AutoWave - Prime Agent Tools Summary`,
            text: textContent,
            url: window.location.href
        };

        console.log('Share data prepared:', shareData);

        // Check if Web Share API is available
        if (navigator.share) {
            console.log('Using Web Share API');
            navigator.share(shareData)
                .then(() => {
                    console.log('Share successful');
                    this.showToast('✅ Content shared successfully!', 'success');
                })
                .catch(err => {
                    console.error('Share failed:', err);
                    // Fallback to copy to clipboard
                    this.fallbackShare(shareData);
                });
        } else {
            console.log('Web Share API not available, using fallback');
            // Fallback for browsers that don't support sharing
            this.fallbackShare(shareData);
        }
    }

    // Fallback share function
    fallbackShare(shareData) {
        console.log('Using fallback share method');

        // Create a formatted text with title and content
        const formattedText = `${shareData.title}

${shareData.text}

---
Shared from AutoWave Prime Agent Tools: ${shareData.url}`;

        console.log('Formatted text for sharing:', formattedText);

        // Copy to clipboard
        navigator.clipboard.writeText(formattedText)
            .then(() => {
                console.log('Text copied to clipboard successfully');

                // Show success message with better styling
                this.showToast('✅ Content copied to clipboard! You can now paste it anywhere to share.', 'success');
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);

                // Try alternative method for older browsers
                try {
                    const textArea = document.createElement('textarea');
                    textArea.value = formattedText;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);

                    this.showToast('✅ Content copied to clipboard! You can now paste it anywhere to share.', 'success');
                } catch (fallbackErr) {
                    console.error('Fallback copy method also failed:', fallbackErr);
                    this.showToast('❌ Failed to copy content. Please try again.', 'error');
                }
            });
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 text-white font-medium max-w-sm`;

        // Set background color based on type
        if (type === 'success') {
            toast.style.backgroundColor = '#10B981'; // green-500
        } else if (type === 'error') {
            toast.style.backgroundColor = '#EF4444'; // red-500
        } else {
            toast.style.backgroundColor = '#3B82F6'; // blue-500
        }

        toast.textContent = message;
        document.body.appendChild(toast);

        // Animate in
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'transform 0.3s ease-in-out';
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);

        // Remove after 4 seconds
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PrimeAgentTools();
});
