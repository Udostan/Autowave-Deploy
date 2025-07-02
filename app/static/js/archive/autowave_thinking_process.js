// ⚠️ ARCHIVED - AUTOWAVE THINKING PROCESS HANDLER ⚠️
// ⚠️ MOVED TO ARCHIVE TO PREVENT CONFLICTS ⚠️
// This script handles the simulated thinking process display for the AutoWave template

document.addEventListener('DOMContentLoaded', function() {
    console.log('Enhanced AutoWave Thinking Process Handler loaded');

    // Get the thinking content element
    let thinkingContent = document.getElementById('thinkingContent');

    // If the element doesn't exist, don't proceed but we'll try again when startThinkingProcess is called
    if (!thinkingContent) {
        console.warn('Thinking content element not found in AutoWave template on initial load - will try again when needed');
    } else {
        console.log('Found thinking content element:', thinkingContent);
    }

    // Add a CSS keyframe animation for the typing cursor if it doesn't exist
    if (!document.querySelector('style#thinking-process-styles')) {
        const style = document.createElement('style');
        style.id = 'thinking-process-styles';
        style.textContent = `
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0; }
            }

            .typing-cursor {
                display: inline-block;
                width: 2px;
                height: 1em;
                background-color: #4B5563;
                margin-left: 2px;
                animation: blink 1s infinite;
                vertical-align: middle;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            .thinking-step {
                margin-bottom: 10px;
                padding-left: 10px;
                border-left: 3px solid #4B5563;
                animation: fadeIn 0.5s ease-in-out;
            }
        `;
        document.head.appendChild(style);
        console.log('Added thinking process styles');
    }

    // Variables to track thinking process
    let thinkingInterval = null;
    let displayedSteps = new Set();
    let thinkingCycles = 0;
    let taskDescription = '';
    let isTaskComplete = false;

    // Log that we're ready
    console.log('Thinking process handler initialized and ready');

    // Function to start the thinking process
    window.startThinkingProcess = function(taskDesc, containerId) {
        console.log('Starting enhanced thinking process for AutoWave template:', taskDesc);
        console.log('Container ID:', containerId || 'Not specified, using current active container');

        // Store the task description for reference
        taskDescription = taskDesc;

        // Reset task completion flag
        isTaskComplete = false;

        // Find the current active thinking container
        // If containerId is provided, use that specific container
        // Otherwise, try to find the most recently created container
        let currentContainer;

        if (containerId) {
            currentContainer = document.getElementById(containerId);
            console.log('Using specified container:', containerId);
        } else {
            // Try to find the most recent container by checking taskCounter
            const taskCounter = window.taskCounter || 0;
            if (taskCounter > 0) {
                currentContainer = document.getElementById(`thinking-container-${taskCounter}`);
                console.log('Using most recent container by task counter:', taskCounter);
            } else {
                currentContainer = document.getElementById('thinking-container-initial');
                console.log('Using initial container as fallback');
            }
        }

        // If we found a container, use its thinking content
        if (currentContainer) {
            thinkingContent = currentContainer.querySelector('.prose');
            console.log('Found thinking content in container:', currentContainer.id);
        } else {
            // Fallback to any thinking content
            console.log('Container not found, trying to find any thinking content');
            thinkingContent = document.querySelector('.thinking-process .prose');
        }

        // If still not found, try to create one
        if (!thinkingContent) {
            console.error('Still cannot find thinking content element - creating one');

            // Try to find the thinking process container
            const thinkingProcess = document.querySelector('.thinking-process');
            if (thinkingProcess) {
                // Create a new thinking content element
                thinkingContent = document.createElement('div');
                thinkingContent.id = 'thinkingContent';
                thinkingContent.className = 'prose prose-sm max-w-none text-sm text-gray-500';
                thinkingProcess.appendChild(thinkingContent);
                console.log('Created new thinking content element');
            } else {
                console.error('Cannot find thinking process container - cannot create thinking content');
                // Create a fallback alert
                alert('Thinking process container not found. Please refresh the page and try again.');
                return;
            }
        }

        // Clear any existing interval
        if (thinkingInterval) {
            clearInterval(thinkingInterval);
            thinkingInterval = null;
        }

        // Reset tracking variables
        displayedSteps = new Set();
        thinkingCycles = 0;

        // Clear previous content
        console.log('Clearing thinking content');
        thinkingContent.innerHTML = '';

        // Make sure the current thinking container is visible
        if (currentContainer) {
            currentContainer.style.display = 'block';
            currentContainer.style.visibility = 'visible';
            console.log('Made current thinking container visible:', currentContainer.id);

            // Make sure the thinking process within this container is visible
            const thinkingProcess = currentContainer.querySelector('.thinking-process');
            if (thinkingProcess) {
                thinkingProcess.style.display = 'block';
                thinkingProcess.style.visibility = 'visible';
                thinkingProcess.style.height = '300px';
                console.log('Made thinking process visible in container:', currentContainer.id);
            }
        } else {
            // Fallback to any thinking container
            console.error('Current container not found - looking for any thinking container');
            const anyThinkingContainer = document.querySelector('.thinking-container');
            if (anyThinkingContainer) {
                anyThinkingContainer.style.display = 'block';
                anyThinkingContainer.style.visibility = 'visible';
                console.log('Made alternative thinking container visible');

                // Make sure the thinking process is visible
                const thinkingProcess = anyThinkingContainer.querySelector('.thinking-process');
                if (thinkingProcess) {
                    thinkingProcess.style.display = 'block';
                    thinkingProcess.style.visibility = 'visible';
                    thinkingProcess.style.height = '300px';
                }
            } else {
                console.error('No thinking container found');
                alert('Thinking container not found. Please refresh the page and try again.');
                return;
            }
        }

        // Add an initial step immediately
        const initialStep = document.createElement('div');
        initialStep.className = 'thinking-step';
        initialStep.innerHTML = `<p>🤔 I'll help you with "${taskDesc.substring(0, 50)}${taskDesc.length > 50 ? '...' : ''}"</p>`;
        thinkingContent.appendChild(initialStep);
        console.log('Added initial thinking step');

        // Generate initial steps based on the task
        const initialSteps = generateInitialSteps(taskDesc);

        // Display first step immediately with typing animation
        if (initialSteps.length > 0) {
            // Skip the first step since we already added a similar one
            displayedSteps.add(initialSteps[0]);

            // Set up interval for remaining steps
            let currentStep = 1;
            let allSteps = [...initialSteps];

            thinkingInterval = setInterval(() => {
                // Check if task is complete
                if (isTaskComplete) {
                    // Add a final "task complete" message
                    displayThinkingStep("✅ Task completed successfully! Results are displayed below.");

                    // Clear the interval
                    clearInterval(thinkingInterval);
                    thinkingInterval = null;
                    return;
                }

                // If we've shown all steps, generate more
                if (currentStep >= allSteps.length) {
                    thinkingCycles++;
                    const moreSteps = generateMoreSteps(taskDesc, thinkingCycles);

                    // Filter out steps we've already shown
                    const newSteps = moreSteps.filter(step => !displayedSteps.has(step));
                    allSteps = [...allSteps, ...newSteps];
                }

                // Display next step if available
                if (currentStep < allSteps.length) {
                    const step = allSteps[currentStep];

                    // Use typing animation for some steps
                    if (Math.random() > 0.7) {
                        displayThinkingStepWithTyping(step);
                    } else {
                        displayThinkingStep(step);
                    }

                    displayedSteps.add(step);
                    currentStep++;
                }
            }, 2000); // Show a new step every 2 seconds (slightly faster)
        }
    };

    // Function to stop the thinking process
    window.stopThinkingProcess = function(showCompletionMessage = true, containerId) {
        console.log('Stopping thinking process for AutoWave template');
        console.log('Container ID for stopping:', containerId || 'Not specified, using current active container');

        // Set task completion flag
        isTaskComplete = true;

        // If a specific container ID is provided, find that container's thinking content
        if (containerId) {
            const container = document.getElementById(containerId);
            if (container) {
                const containerThinkingContent = container.querySelector('.prose');
                if (containerThinkingContent && showCompletionMessage) {
                    // Add completion message to this specific container
                    const completionStep = document.createElement('div');
                    completionStep.className = 'thinking-step success';
                    completionStep.innerHTML = "✅ Task completed successfully! Results are displayed below.";
                    containerThinkingContent.appendChild(completionStep);

                    // Scroll to bottom
                    const thinkingProcess = container.querySelector('.thinking-process');
                    if (thinkingProcess) {
                        thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
                    }
                }
            }
        } else if (thinkingContent && showCompletionMessage) {
            // Add a final "task complete" message to the current thinking content
            displayThinkingStep("✅ Task completed successfully! Results are displayed below.");
        }

        // Clear the interval
        if (thinkingInterval) {
            clearInterval(thinkingInterval);
            thinkingInterval = null;
        }
    };

    // Function to display a thinking step with typing animation
    function displayThinkingStepWithTyping(step) {
        console.log('Displaying thinking step with typing animation:', step);

        // Make sure we have the thinking content element
        if (!thinkingContent) {
            console.error('Thinking content element not found when trying to display step with typing');
            return;
        }

        // Create element for the step
        const stepElement = document.createElement('div');
        stepElement.className = 'thinking-step typing-cursor';

        // Add appropriate class based on content
        if (step.includes('✅')) {
            // Success message
            stepElement.classList.add('success');
        } else if (step.includes('🔍') || step.includes('🌐') || step.includes('🔎')) {
            // Search-related message
            stepElement.classList.add('search');
        } else if (step.includes('⚙️') || step.includes('🔧')) {
            // Processing message
            stepElement.classList.add('processing');
        } else if (step.includes('📊') || step.includes('📈')) {
            // Analysis message
            stepElement.classList.add('analysis');
        } else if (step.includes('💡')) {
            // Insight message
            stepElement.classList.add('insight');
        }

        // Add to the thinking content
        try {
            thinkingContent.appendChild(stepElement);
        } catch (error) {
            console.error('Error adding thinking step with typing to DOM:', error);
            return;
        }

        // Set up typing animation
        let i = 0;
        const typingSpeed = 30; // milliseconds per character
        const typingInterval = setInterval(() => {
            if (i < step.length) {
                try {
                    stepElement.textContent = step.substring(0, i + 1);
                    i++;
                } catch (error) {
                    console.error('Error updating typing text:', error);
                    clearInterval(typingInterval);
                }
            } else {
                // Typing complete
                clearInterval(typingInterval);
                stepElement.classList.remove('typing-cursor');

                // Scroll to bottom
                try {
                    const thinkingProcess = document.querySelector('.thinking-process');
                    if (thinkingProcess) {
                        thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
                    }
                } catch (error) {
                    console.error('Error scrolling thinking process after typing:', error);
                }
            }
        }, typingSpeed);
    }

    // Function to display a thinking step
    function displayThinkingStep(step) {
        console.log('Displaying thinking step:', step);

        // Make sure we have the thinking content element
        if (!thinkingContent) {
            console.error('Thinking content element not found when trying to display step');
            return;
        }

        // Create element for the step
        const stepElement = document.createElement('div');
        stepElement.className = 'thinking-step';

        // Check if step contains an emoji at the beginning
        const hasEmoji = /^[\u{1F300}-\u{1F6FF}\u{2600}-\u{26FF}]/u.test(step);

        // Add appropriate class based on content
        if (step.includes('✅')) {
            // Success message
            stepElement.classList.add('success');
        } else if (step.includes('🔍') || step.includes('🌐') || step.includes('🔎')) {
            // Search-related message
            stepElement.classList.add('search');
        } else if (step.includes('⚙️') || step.includes('🔧')) {
            // Processing message
            stepElement.classList.add('processing');
        } else if (step.includes('📊') || step.includes('📈')) {
            // Analysis message
            stepElement.classList.add('analysis');
        } else if (step.includes('💡')) {
            // Insight message
            stepElement.classList.add('insight');
        }

        // Use markdown if available
        if (window.markdownit) {
            try {
                const md = window.markdownit();
                stepElement.innerHTML = md.render(step);
            } catch (error) {
                console.error('Error rendering markdown:', error);
                stepElement.textContent = step;
            }
        } else {
            // Simple text content
            stepElement.textContent = step;
        }

        // Add to the thinking content
        try {
            thinkingContent.appendChild(stepElement);
            console.log('Added thinking step to DOM');
        } catch (error) {
            console.error('Error adding thinking step to DOM:', error);
            // Try to recreate the thinking content element
            const thinkingProcess = document.querySelector('.thinking-process');
            if (thinkingProcess) {
                thinkingContent = document.createElement('div');
                thinkingContent.id = 'thinkingContent';
                thinkingContent.className = 'prose prose-sm max-w-none text-sm text-gray-500';
                thinkingProcess.innerHTML = '';
                thinkingProcess.appendChild(thinkingContent);
                thinkingContent.appendChild(stepElement);
                console.log('Recreated thinking content element and added step');
            }
        }

        // Scroll to bottom
        try {
            const thinkingProcess = document.querySelector('.thinking-process');
            if (thinkingProcess) {
                thinkingProcess.scrollTop = thinkingProcess.scrollHeight;
            }
        } catch (error) {
            console.error('Error scrolling thinking process:', error);
        }

        // Make sure the thinking container is visible
        try {
            const thinkingContainer = document.getElementById('thinking-container-initial');
            if (thinkingContainer) {
                thinkingContainer.style.display = 'block';
                thinkingContainer.style.visibility = 'visible';
            }
        } catch (error) {
            console.error('Error making thinking container visible:', error);
        }
    }

    // Function to generate initial thinking steps
    function generateInitialSteps(taskDesc) {
        const lowerTaskDesc = taskDesc.toLowerCase();

        // Start with engaging, conversational initial steps with emojis
        const steps = [
            `🤔 I'll help you with "${taskDesc.substring(0, 50)}${taskDesc.length > 50 ? '...' : ''}"`,
            "💭 Let me think about how to approach this task...",
            "🌐 I'll search the web for the most up-to-date information on this topic."
        ];

        // Add task-specific thinking steps based on keywords in the task
        if (lowerTaskDesc.includes('compare') || lowerTaskDesc.includes('vs') || lowerTaskDesc.includes('versus')) {
            steps.push("⚖️ Finding detailed comparison points between these options.");
            steps.push("🔍 Looking for expert reviews and user experiences to provide a balanced comparison.");
            steps.push("📊 I'll create a side-by-side comparison of the key features and benefits.");
        }

        if (lowerTaskDesc.includes('recipe') || lowerTaskDesc.includes('cook') || lowerTaskDesc.includes('food')) {
            steps.push("🍳 Searching for authentic recipes from culinary experts and food blogs.");
            steps.push("⭐ I'll find recipes with the best ratings and reviews.");
            steps.push("📝 Looking for detailed ingredient lists and step-by-step instructions.");
        }

        if (lowerTaskDesc.includes('travel') || lowerTaskDesc.includes('vacation') || lowerTaskDesc.includes('trip')) {
            steps.push("🧳 Looking for current travel information, including prices and availability.");
            steps.push("🚨 Checking travel advisories and local recommendations for the best experience.");
            steps.push("🗺️ Researching the best attractions and activities at your destination.");
        }

        if (lowerTaskDesc.includes('code') || lowerTaskDesc.includes('program') || lowerTaskDesc.includes('develop')) {
            steps.push("💻 Searching for the most efficient coding approaches and best practices.");
            steps.push("📚 Reviewing documentation and developer resources for this technology.");
            steps.push("🧩 I'll provide well-structured, commented code that follows modern standards.");
        }

        if (lowerTaskDesc.includes('health') || lowerTaskDesc.includes('medical') || lowerTaskDesc.includes('doctor')) {
            steps.push("🏥 Searching for information from reputable medical sources.");
            steps.push("🔬 Looking for peer-reviewed research and expert medical opinions.");
            steps.push("⚕️ Finding information from health organizations and medical journals.");
        }

        if (lowerTaskDesc.includes('news') || lowerTaskDesc.includes('current') || lowerTaskDesc.includes('recent')) {
            steps.push("📰 Searching for the most recent news articles on this topic.");
            steps.push("🔄 Checking multiple news sources to ensure balanced coverage.");
            steps.push("📅 Focusing on information published within the last few days.");
        }

        if (lowerTaskDesc.includes('book') || lowerTaskDesc.includes('read') || lowerTaskDesc.includes('author')) {
            steps.push("📚 Looking for book reviews and summaries from literary critics.");
            steps.push("✍️ Researching the author's background and writing style.");
            steps.push("📖 Finding key themes and notable quotes from the book.");
        }

        return steps;
    }

    // Function to generate more thinking steps based on cycle
    function generateMoreSteps(taskDesc, cycle) {
        const lowerTaskDesc = taskDesc.toLowerCase();
        let steps = [];

        if (cycle === 1) {
            // First cycle: Research-focused steps
            steps = [
                "🔍 Searching through multiple reliable sources...",
                "📊 Analyzing the most recent information available...",
                "⚖️ Comparing data from different authoritative sources...",
                "👩‍🔬 Looking for expert opinions and peer-reviewed research...",
                "🌐 Gathering comprehensive information from across the web...",
                "📑 Collecting relevant data points from multiple sources...",
                "🧠 Thinking through the key aspects of your question..."
            ];
        } else if (cycle === 2) {
            // Second cycle: Analysis steps
            steps = [
                "⚙️ Evaluating the reliability of the sources I've found...",
                "🎯 Identifying the most relevant information for your query...",
                "🧩 Synthesizing information from multiple perspectives...",
                "⚠️ Checking for any contradictory information in the sources...",
                "📋 Organizing the key points into a coherent structure...",
                "💡 Identifying the most important insights from the research...",
                "🔄 Cross-referencing information between different sources..."
            ];
        } else if (cycle === 3) {
            // Third cycle: Formatting and preparation steps
            steps = [
                "📝 Preparing a comprehensive response with all the key details...",
                "📊 Organizing the information in a clear, readable format...",
                "🖼️ Adding relevant images to enhance understanding...",
                "📑 Creating a well-structured summary of the findings...",
                "✅ Finalizing the response with all requested elements...",
                "🔤 Ensuring the information is presented in a logical order...",
                "📌 Highlighting the most important points for quick reference..."
            ];
        } else {
            // Additional cycles: Mix of progress updates
            steps = [
                "⏳ Still working on this... gathering comprehensive information.",
                "🔄 Analyzing multiple sources to ensure accuracy.",
                "🔍 Finding the most relevant and up-to-date information for you.",
                "📋 Organizing the information into a clear, structured format.",
                "⚡ Almost there! Putting together the final details.",
                "📊 Creating visual elements to help explain complex information.",
                "🧠 Thinking through all aspects of your question to ensure a complete answer."
            ];

            // Add some "almost done" messages in later cycles
            if (cycle > 3) {
                steps.push("🏁 Almost finished compiling all the information...");
                steps.push("✨ Putting the final touches on your comprehensive answer...");
                steps.push("⌛ Just a moment more as I finalize the details...");
                steps.push("📋 Doing a final check to ensure all your questions are answered...");
                steps.push("🔄 Running a final verification on all the information...");
            }
        }

        return steps;
    }
});
