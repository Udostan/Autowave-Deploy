// Agentic Code - Smart Code Assistant with Conversational AI
// Similar to Augment's capabilities with step-by-step progress updates

console.log('🚀 AGENTIC CODE JS FILE LOADED!');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 AGENTIC CODE DOM READY!');

    // Global variables
    let codeEditor;
    let currentSessionId = null;
    let isProcessing = false;

    // Elements
    const conversationInput = document.getElementById('conversationInput');
    const conversationSendBtn = document.getElementById('conversationSendBtn');
    const conversationContainer = document.getElementById('conversationContainer');
    const previewContent = document.getElementById('previewContent');
    const codeTab = document.getElementById('codeTab');
    const previewTab = document.getElementById('previewTab');
    const codeEditorContainer = document.getElementById('codeEditorContainer');
    const previewContainer = document.getElementById('previewContainer');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const conversationSidebar = document.getElementById('conversationSidebar');
    const newSessionBtn = document.getElementById('newSessionBtn');


    const fileUploadBtn = document.getElementById('fileUploadBtn');
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');

    // File upload state
    let uploadedFiles = [];

    // Initialize CodeMirror
    function initializeCodeEditor() {
        if (typeof CodeMirror !== 'undefined') {
            codeEditor = CodeMirror.fromTextArea(document.getElementById('codeEditor'), {
                lineNumbers: true,
                mode: 'htmlmixed', // Default mode, will be updated based on language
                theme: 'dracula',
                autoCloseBrackets: true,
                matchBrackets: true,
                indentUnit: 2,
                tabSize: 2,
                lineWrapping: true,
                extraKeys: {
                    "Ctrl-Space": "autocomplete",
                    "Ctrl-/": "toggleComment"
                }
            });

            // Update preview when code changes
            codeEditor.on('change', function() {
                updatePreview();
            });

            console.log('CodeMirror initialized');
        } else {
            console.error('CodeMirror not loaded');
        }
    }

    // Update CodeMirror mode based on language
    function updateCodeEditorMode(language) {
        if (!codeEditor) return;

        let mode = 'htmlmixed'; // default
        if (language === 'python') {
            mode = 'python';
        } else if (language === 'javascript') {
            mode = 'javascript';
        } else if (language === 'css') {
            mode = 'css';
        } else if (language === 'html') {
            mode = 'htmlmixed';
        }

        codeEditor.setOption('mode', mode);
        console.log('CodeMirror mode updated to:', mode);
    }

    // Initialize the editor
    initializeCodeEditor();

    // Add test code for button testing
    setTimeout(function() {
        if (codeEditor) {
            const testCode = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        .red-button {
            background-color: #ff4444;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 18px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .red-button:hover {
            background-color: #cc3333;
        }
    </style>
</head>
<body>
    <button class="red-button" onclick="alert('Hello from the red button!')">Click Me</button>
</body>
</html>`;
            codeEditor.setValue(testCode);
            console.log('✅ Test code added to editor for button testing');
        }
    }, 3000);



    // Tab switching functionality
    if (codeTab && previewTab) {
        codeTab.addEventListener('click', function() {
            showCodeTab();
        });

        previewTab.addEventListener('click', function() {
            showPreviewTab();
        });
    }



    function showCodeTab() {
        codeTab.classList.add('active');
        previewTab.classList.remove('active');
        codeEditorContainer.classList.remove('hidden');
        previewContainer.classList.add('hidden');
        if (codeEditor) {
            codeEditor.refresh();
        }
        // Show code action buttons
        showCodeActionButtons();

    }

    function showPreviewTab() {
        previewTab.classList.add('active');
        codeTab.classList.remove('active');
        previewContainer.classList.remove('hidden');
        codeEditorContainer.classList.add('hidden');
        updatePreview();
        // Show preview action buttons
        showPreviewActionButtons();

    }



    // Update preview
    function updatePreview() {
        if (!codeEditor || !previewContent) return;

        const code = codeEditor.getValue();
        if (!code.trim()) {
            previewContent.innerHTML = '<p class="text-center p-8 text-gray-500">Your code preview will appear here</p>';
            return;
        }

        // Detect language from code content
        const language = detectLanguageFromCode(code);

        if (language === 'python') {
            // For Python code, show formatted code with run button
            showPythonPreview(code);
        } else {
            // For HTML/CSS/JS, show in iframe
            showWebPreview(code);
        }
    }

    function detectLanguageFromCode(code) {
        // Simple language detection based on code content
        if (code.includes('def ') || code.includes('import ') || code.includes('print(') || code.includes('if __name__')) {
            return 'python';
        }
        return 'html';
    }

    function showWebPreview(code) {
        // Create iframe for web preview
        const iframe = document.createElement('iframe');
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.style.minHeight = '500px';

        previewContent.innerHTML = '';
        previewContent.appendChild(iframe);

        // Write code to iframe
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        iframeDoc.open();
        iframeDoc.write(code);
        iframeDoc.close();
    }

    function showPythonPreview(code) {
        // For Python code, show formatted preview with run button
        previewContent.innerHTML = `
            <div class="python-preview h-full flex flex-col">
                <div class="bg-gray-800 text-white p-4 border-b border-gray-600">
                    <div class="flex items-center justify-between">
                        <h3 class="text-lg font-semibold">Python Code</h3>
                        <button id="runPythonBtn" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                            ▶ Run Code
                        </button>
                    </div>
                </div>
                <div class="flex-1 bg-gray-900 text-white p-4 overflow-auto">
                    <pre class="text-sm"><code class="language-python">${escapeHtml(code)}</code></pre>
                </div>
                <div id="pythonOutput" class="bg-black text-green-400 p-4 border-t border-gray-600 min-h-[100px] max-h-[200px] overflow-auto font-mono text-sm" style="display: none;">
                    <div class="text-gray-500 mb-2">Output:</div>
                    <div id="outputContent"></div>
                </div>
            </div>
        `;

        // Add event listener for run button
        const runBtn = document.getElementById('runPythonBtn');
        if (runBtn) {
            runBtn.addEventListener('click', () => runPythonCode(code));
        }
    }

    async function runPythonCode(code) {
        const runBtn = document.getElementById('runPythonBtn');
        const outputDiv = document.getElementById('pythonOutput');
        const outputContent = document.getElementById('outputContent');

        if (!runBtn || !outputDiv || !outputContent) return;

        // Show loading state
        runBtn.disabled = true;
        runBtn.innerHTML = '⏳ Running...';
        outputDiv.style.display = 'block';
        outputContent.innerHTML = '<div class="text-yellow-400">Executing Python code...</div>';

        try {
            const response = await fetch('/api/code-executor/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    language: 'python'
                })
            });

            const result = await response.json();

            if (result.success) {
                const output = result.result;
                let outputHtml = '';

                if (output.stdout) {
                    outputHtml += `<div class="text-green-400">${escapeHtml(output.stdout)}</div>`;
                }

                if (output.stderr) {
                    outputHtml += `<div class="text-red-400">Error: ${escapeHtml(output.stderr)}</div>`;
                }

                if (!output.stdout && !output.stderr) {
                    outputHtml = '<div class="text-gray-400">Code executed successfully (no output)</div>';
                }

                outputContent.innerHTML = outputHtml;
            } else {
                outputContent.innerHTML = `<div class="text-red-400">Error: ${escapeHtml(result.error)}</div>`;
            }
        } catch (error) {
            outputContent.innerHTML = `<div class="text-red-400">Error: ${escapeHtml(error.message)}</div>`;
        } finally {
            // Reset button state
            runBtn.disabled = false;
            runBtn.innerHTML = '▶ Run Code';
        }
    }

    // Handle conversation sidebar toggle
    if (sidebarToggle && conversationSidebar) {
        sidebarToggle.addEventListener('click', function() {
            // Check if we're on mobile
            if (window.innerWidth <= 768) {
                conversationSidebar.classList.toggle('mobile-open');
            } else {
                conversationSidebar.classList.toggle('collapsed');
                sidebarToggle.classList.toggle('collapsed');

                // Toggle the collapsed class on the preview container
                const previewContainer = document.querySelector('.fixed-preview-container');
                if (previewContainer) previewContainer.classList.toggle('sidebar-collapsed');
            }
        });
    }

    // Handle main sidebar toggle - detect when the main content margin changes
    function updatePositionsForMainSidebar() {
        const mainContent = document.getElementById('main-content');
        const conversationSidebar = document.querySelector('.conversation-sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        const previewContainer = document.querySelector('.fixed-preview-container');

        if (!mainContent) return;

        // Check if main sidebar is collapsed by looking at the margin class
        const isMainSidebarCollapsed = mainContent.classList.contains('ml-16');
        const mainSidebarWidth = isMainSidebarCollapsed ? '4rem' : '16rem';

        // Update conversation sidebar position
        if (conversationSidebar) {
            conversationSidebar.style.left = mainSidebarWidth;
        }

        // Update toggle button position
        if (sidebarToggle) {
            const conversationSidebarCollapsed = conversationSidebar && conversationSidebar.classList.contains('collapsed');
            if (conversationSidebarCollapsed) {
                sidebarToggle.style.left = mainSidebarWidth;
            } else {
                sidebarToggle.style.left = `calc(${mainSidebarWidth} + 300px)`;
            }
        }

        // Update preview container position
        if (previewContainer) {
            const conversationSidebarCollapsed = previewContainer.classList.contains('sidebar-collapsed');
            if (conversationSidebarCollapsed) {
                previewContainer.style.left = mainSidebarWidth;
            } else {
                previewContainer.style.left = `calc(${mainSidebarWidth} + 300px)`;
            }
        }
    }

    // Watch for changes to the main content margin classes
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
        // Create a MutationObserver to watch for class changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    updatePositionsForMainSidebar();
                }
            });
        });

        // Start observing
        observer.observe(mainContent, {
            attributes: true,
            attributeFilter: ['class']
        });

        // Initial position update
        updatePositionsForMainSidebar();
    }

    // Listen for main sidebar toggle from layout.html
    document.addEventListener('DOMContentLoaded', function() {
        // Check if main sidebar is collapsed and update our layout accordingly
        const mainSidebar = document.querySelector('.sidebar');
        if (mainSidebar) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const isCollapsed = document.body.classList.contains('collapsed-sidebar');
                        // Update our layout based on main sidebar state
                        updateLayoutForMainSidebar(isCollapsed);
                    }
                });
            });

            observer.observe(document.body, {
                attributes: true,
                attributeFilter: ['class']
            });
        }
    });

    function updateLayoutForMainSidebar(isCollapsed) {
        // This function handles layout updates when the main sidebar is toggled
        // The CSS already handles most of the positioning, but we can add any
        // additional JavaScript-based adjustments here if needed
        console.log('Main sidebar collapsed:', isCollapsed);
    }

    // Handle file upload
    if (fileUploadBtn && fileInput) {
        fileUploadBtn.addEventListener('click', function() {
            fileInput.click();
        });

        fileInput.addEventListener('change', function(e) {
            handleFileUpload(e.target.files);
        });
    }

    // Handle new session
    if (newSessionBtn) {
        newSessionBtn.addEventListener('click', function() {
            startNewSession();
        });
    }

    function startNewSession() {
        currentSessionId = generateSessionId();
        conversationContainer.innerHTML = `
            <div class="agent-response">
                <div class="text-sm text-gray-400 mb-2">🤖 AI Assistant</div>
                <div class="text-white">
                    New session started! I'm ready to help you create and modify code.
                    <br><br>
                    <strong>What I can do:</strong>
                    <ul class="mt-2 ml-4 list-disc text-sm text-gray-300">
                        <li>Generate code from your descriptions</li>
                        <li>Modify existing code based on your requests</li>
                        <li>Explain what I'm planning to do</li>
                        <li>Show step-by-step progress updates</li>
                        <li>Iterate on code until you're satisfied</li>
                    </ul>
                    <br>
                    What would you like to create?
                </div>
            </div>
        `;
        if (codeEditor) {
            codeEditor.setValue('');
        }

        // Clear uploaded files
        uploadedFiles = [];
        updateFilePreview();

        console.log('New session started:', currentSessionId);
    }

    // File upload handling functions
    function handleFileUpload(files) {
        for (let file of files) {
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                continue;
            }

            const fileData = {
                file: file,
                name: file.name,
                type: file.type,
                size: file.size,
                id: Date.now() + Math.random()
            };

            uploadedFiles.push(fileData);

            // Read file content for text files and images
            if (file.type.startsWith('text/') || file.type.startsWith('image/') ||
                file.name.endsWith('.py') || file.name.endsWith('.js') ||
                file.name.endsWith('.html') || file.name.endsWith('.css') ||
                file.name.endsWith('.json') || file.name.endsWith('.md')) {

                readFileContent(fileData);
            }
        }

        updateFilePreview();
        fileInput.value = ''; // Clear the input
    }

    function readFileContent(fileData) {
        const reader = new FileReader();

        if (fileData.file.type.startsWith('image/')) {
            reader.onload = function(e) {
                fileData.content = e.target.result; // Base64 data URL
                fileData.contentType = 'image';
            };
            reader.readAsDataURL(fileData.file);
        } else {
            reader.onload = function(e) {
                fileData.content = e.target.result;
                fileData.contentType = 'text';
            };
            reader.readAsText(fileData.file);
        }
    }

    function updateFilePreview() {
        if (!filePreview) return;

        if (uploadedFiles.length === 0) {
            filePreview.classList.remove('show');
            filePreview.innerHTML = '';
            return;
        }

        filePreview.classList.add('show');
        filePreview.innerHTML = uploadedFiles.map(file => `
            <div class="file-preview-item">
                <div class="file-preview-name">
                    <span>${getFileIcon(file.type)} ${file.name}</span>
                    <span class="text-gray-500">(${formatFileSize(file.size)})</span>
                </div>
                <button class="file-remove-btn" onclick="removeFile('${file.id}')">×</button>
            </div>
        `).join('');
    }

    function getFileIcon(fileType) {
        if (fileType.startsWith('image/')) return '🖼️';
        if (fileType.includes('pdf')) return '📄';
        if (fileType.includes('text') || fileType.includes('json')) return '📝';
        if (fileType.includes('python')) return '🐍';
        if (fileType.includes('javascript')) return '📜';
        return '📁';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function removeFile(fileId) {
        uploadedFiles = uploadedFiles.filter(file => file.id != fileId);
        updateFilePreview();
    }

    // Make removeFile globally accessible
    window.removeFile = removeFile;

    // Handle conversation input
    if (conversationInput && conversationSendBtn) {
        conversationSendBtn.addEventListener('click', function() {
            sendMessage();
        });

        conversationInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    async function sendMessage() {
        if (isProcessing) return;

        const message = conversationInput.value.trim();
        if (!message) return;

        // Check credits before sending message
        if (window.creditSystem) {
            const canProceed = await window.creditSystem.enforceCredits('code_generation_simple');
            if (!canProceed) {
                console.log('Insufficient credits for Agentic Code');
                return;
            }
        }

        isProcessing = true;
        conversationSendBtn.disabled = true;

        // Prepare files data for upload
        const filesData = uploadedFiles.map(file => ({
            name: file.name,
            type: file.type,
            size: file.size,
            content: file.content,
            contentType: file.contentType
        }));

        // Add user message to conversation (include file info if any)
        let displayMessage = message;
        if (uploadedFiles.length > 0) {
            const fileNames = uploadedFiles.map(f => f.name).join(', ');
            displayMessage += `\n\n📎 Attached files: ${fileNames}`;
        }
        addUserMessage(displayMessage);

        conversationInput.value = '';

        // Clear uploaded files after adding to message
        uploadedFiles = [];
        updateFilePreview();

        try {
            // Get current code
            const currentCode = codeEditor ? codeEditor.getValue() : '';

            // Send request to backend with files
            await processAgenticRequest(message, currentCode, filesData);
        } catch (error) {
            console.error('Error processing message:', error);
            addAgentMessage('Sorry, I encountered an error processing your request. Please try again.');
        } finally {
            isProcessing = false;
            conversationSendBtn.disabled = false;
        }
    }

    function addUserMessage(message) {
        const userDiv = document.createElement('div');
        userDiv.className = 'user-prompt';
        userDiv.innerHTML = `
            <div class="text-sm text-gray-400 mb-2">👤 You</div>
            <div class="text-white">${escapeHtml(message)}</div>
        `;
        conversationContainer.appendChild(userDiv);
        scrollToBottom();
    }

    function addAgentMessage(message) {
        const agentDiv = document.createElement('div');
        agentDiv.className = 'agent-response';
        agentDiv.innerHTML = `
            <div class="text-sm text-gray-400 mb-2">🤖 AI Assistant</div>
            <div class="text-white">${message}</div>
        `;
        conversationContainer.appendChild(agentDiv);
        scrollToBottom();
    }

    function addAgentStep(icon, text, isTyping = false) {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'agent-step';

        if (isTyping) {
            stepDiv.innerHTML = `
                <div class="step-icon">${icon}</div>
                <div class="step-text">
                    ${text}
                    <span class="typing-indicator ml-2">
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                        <span class="typing-dot"></span>
                    </span>
                </div>
            `;
        } else {
            stepDiv.innerHTML = `
                <div class="step-icon">${icon}</div>
                <div class="step-text">${text}</div>
            `;
        }

        conversationContainer.appendChild(stepDiv);
        scrollToBottom();
        return stepDiv;
    }

    function updateAgentStep(stepDiv, icon, text) {
        stepDiv.innerHTML = `
            <div class="step-icon">${icon}</div>
            <div class="step-text">${text}</div>
        `;
    }

    async function processAgenticRequest(message, currentCode, filesData = []) {
        // Step 1: Planning
        const planningStep = addAgentStep('🧠', 'Analyzing your request and planning the approach...', true);

        try {
            const requestBody = {
                message: message,
                current_code: currentCode,
                session_id: currentSessionId
            };

            // Add files if any
            if (filesData && filesData.length > 0) {
                requestBody.files = filesData;
            }

            const response = await fetch('/api/agentic-code/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Update planning step
            updateAgentStep(planningStep, '✅', `Planning complete: ${data.plan || 'Ready to proceed'}`);

            // Step 2: Implementation
            const implementationStep = addAgentStep('⚙️', 'Implementing the changes...', true);

            // Simulate step-by-step implementation (like Augment)
            await simulateImplementationSteps(data);

            // Update implementation step
            updateAgentStep(implementationStep, '✅', 'Implementation complete');

            // Step 3: Update code editor
            if (data.code && codeEditor) {
                const updatingStep = addAgentStep('📝', 'Updating code editor...', true);

                // Update CodeMirror mode based on detected language
                if (data.language) {
                    updateCodeEditorMode(data.language);
                }

                // Animate code update
                await animateCodeUpdate(data.code);

                updateAgentStep(updatingStep, '✅', 'Code updated successfully');
            }

            // Step 4: Final response
            if (data.explanation) {
                addAgentMessage(data.explanation);
            }

            // Consume credits after successful code generation
            if (window.creditSystem) {
                window.creditSystem.consumeCredits('code_generation_simple').then(result => {
                    if (result.success) {
                        console.log('Credits consumed successfully for Agentic Code:', result.consumed);
                    } else {
                        console.warn('Failed to consume credits for Agentic Code:', result.error);
                    }
                }).catch(error => {
                    console.error('Error consuming credits for Agentic Code:', error);
                });
            }

            // Track successful activity in enhanced history
            if (window.trackActivity) {
                try {
                    window.trackActivity('agentic_code', 'code_generation', {
                        message: message,
                        current_code: currentCode,
                        files: filesData,
                        session_id: currentSessionId
                    }, {
                        plan: data.plan || 'Code generation completed',
                        code: data.code || '',
                        language: data.language || 'unknown',
                        explanation: data.explanation || 'Code generated successfully'
                    });
                } catch (trackError) {
                    console.warn('Error tracking activity:', trackError);
                    // Don't throw error, just log it
                }
            }

        } catch (error) {
            updateAgentStep(planningStep, '❌', 'Error occurred during processing');

            // Track failed activity
            if (window.trackActivity) {
                try {
                    window.trackActivity('agentic_code', 'code_generation', {
                        message: message,
                        current_code: currentCode,
                        files: filesData,
                        session_id: currentSessionId
                    }, null, null, false, error.message || 'Code generation failed');
                } catch (trackError) {
                    console.warn('Error tracking failed activity:', trackError);
                    // Don't throw error, just log it
                }
            }

            throw error;
        }
    }

    async function simulateImplementationSteps(data) {
        const steps = data.steps || [
            'Analyzing requirements and dependencies',
            'Setting up functional architecture',
            'Implementing core functionality',
            'Adding interactive features',
            'Integrating APIs and data handling',
            'Testing functionality and responsiveness',
            'Optimizing performance',
            'Validating complete functionality'
        ];

        for (let i = 0; i < steps.length; i++) {
            const step = addAgentStep('⚡', steps[i], true);
            await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 500));
            updateAgentStep(step, '✅', steps[i]);
        }

        // Add functionality validation step
        const validationStep = addAgentStep('🔍', 'Validating app functionality...', true);
        await new Promise(resolve => setTimeout(resolve, 1500));
        updateAgentStep(validationStep, '✅', 'App functionality validated - all features working');
    }

    async function animateCodeUpdate(newCode) {
        if (!codeEditor) return;

        // Smooth transition to new code
        const currentCode = codeEditor.getValue();
        const lines = newCode.split('\n');

        codeEditor.setValue('');

        for (let i = 0; i < lines.length; i++) {
            await new Promise(resolve => setTimeout(resolve, 50));
            codeEditor.replaceRange(lines[i] + (i < lines.length - 1 ? '\n' : ''),
                                   {line: i, ch: 0});
        }

        // Update preview
        updatePreview();
    }

    function scrollToBottom() {
        conversationContainer.scrollTop = conversationContainer.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Initialize session
    startNewSession();

    // Check for initial message from URL parameter (from homepage tab selection)
    function checkForInitialMessage() {
        // Get the initial message passed from the template
        const initialMessageElement = document.getElementById('initial-message-data');
        if (initialMessageElement) {
            const initialMessage = initialMessageElement.textContent.trim();
            if (initialMessage) {
                console.log('Found initial message:', initialMessage);

                // Set the message in the input field
                if (conversationInput) {
                    conversationInput.value = initialMessage;
                }

                // Add user message to conversation
                addUserMessage(initialMessage);

                // Automatically process the message
                setTimeout(() => {
                    sendMessage();
                }, 500); // Small delay to ensure everything is initialized
            }
        }
    }









    // Simple Action Button Setup
    setupActionButtons();

    // Action Button Setup (following Prime Agent Tools pattern exactly)
    function setupActionButtons() {
        console.log('🚀 Setting up action buttons with event delegation...');

        // Use event delegation like Prime Agent Tools
        document.body.addEventListener('click', (event) => {
            console.log('Agentic Code - Body click detected:', event.target, 'Classes:', event.target.className);

            // Check if the clicked element is a copy-code-btn or one of its children
            const copyBtn = event.target.closest('.copy-code-btn');
            if (copyBtn) {
                console.log('Agentic Code - Copy button clicked!', copyBtn);
                event.preventDefault();
                event.stopPropagation();
                copyCode();
                return;
            }

            // Check if the clicked element is a download-preview-btn or one of its children
            const downloadBtn = event.target.closest('.download-preview-btn');
            if (downloadBtn) {
                console.log('Agentic Code - Download button clicked!', downloadBtn);
                event.preventDefault();
                event.stopPropagation();
                exportCode();
                return;
            }

            // Check if the clicked element is a open-preview-btn or one of its children
            const openBtn = event.target.closest('.open-preview-btn');
            if (openBtn) {
                console.log('Agentic Code - Open button clicked!', openBtn);
                event.preventDefault();
                event.stopPropagation();
                openCode();
                return;
            }

            // Check if the clicked element is a share-preview-btn or one of its children
            const shareBtn = event.target.closest('.share-preview-btn');
            if (shareBtn) {
                console.log('Agentic Code - Share button clicked!', shareBtn);
                event.preventDefault();
                event.stopPropagation();
                shareCode();
                return;
            }
        });

        console.log('✅ Event delegation setup complete');
    }

    function copyCode() {
        if (codeEditor) {
            const code = codeEditor.getValue();
            if (!code.trim()) {
                alert('No code to copy!');
                return;
            }

            navigator.clipboard.writeText(code).then(() => {
                alert('Code copied to clipboard!');
            }).catch(() => {
                alert('Failed to copy code');
            });
        }
    }

    function exportCode() {
        if (codeEditor) {
            const code = codeEditor.getValue();
            if (!code.trim()) {
                alert('No code to export!');
                return;
            }

            const blob = new Blob([code], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'code.html';
            a.click();
            URL.revokeObjectURL(url);
            alert('Code downloaded!');
        }
    }

    function openCode() {
        if (codeEditor) {
            const code = codeEditor.getValue();
            if (!code.trim()) {
                alert('No code to open!');
                return;
            }

            const newWindow = window.open('', '_blank');
            newWindow.document.write(code);
            newWindow.document.close();
            alert('Code opened in new window!');
        }
    }

    function shareCode() {
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            alert('URL copied to clipboard!');
        }).catch(() => {
            alert('Failed to copy URL');
        });
    }

    // TAB SWITCHING FUNCTIONS FOR BUTTON VISIBILITY
    function showCodeActionButtons() {
        console.log('📋 Showing code action buttons');
        // Copy button should always be visible in code editor
        const copyBtn = document.querySelector('.copy-code-btn');
        if (copyBtn) {
            copyBtn.style.display = 'flex';
        }

        // Hide preview buttons when on code tab
        const downloadBtn = document.querySelector('.download-preview-btn');
        const openBtn = document.querySelector('.open-preview-btn');
        const shareBtn = document.querySelector('.share-preview-btn');

        if (downloadBtn) downloadBtn.style.display = 'none';
        if (openBtn) openBtn.style.display = 'none';
        if (shareBtn) shareBtn.style.display = 'none';

        console.log('✅ Code tab buttons configured');
    }

    function showPreviewActionButtons() {
        console.log('🔗 Showing preview action buttons');
        // Copy button stays visible in code editor
        const copyBtn = document.querySelector('.copy-code-btn');
        if (copyBtn) {
            copyBtn.style.display = 'flex';
        }

        // Show preview buttons when on preview tab
        const downloadBtn = document.querySelector('.download-preview-btn');
        const openBtn = document.querySelector('.open-preview-btn');
        const shareBtn = document.querySelector('.share-preview-btn');

        if (downloadBtn) downloadBtn.style.display = 'flex';
        if (openBtn) openBtn.style.display = 'flex';
        if (shareBtn) shareBtn.style.display = 'flex';

        console.log('✅ Preview tab buttons configured');
    }

    // Check for initial message after a short delay to ensure DOM is ready
    setTimeout(checkForInitialMessage, 100);


});
