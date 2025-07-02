// Code Generator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Code Generator JS loaded');

    // Get elements
    const buildProjectBtn = document.getElementById('buildProjectBtn');
    const codePrompt = document.getElementById('codePrompt');
    const projectType = document.getElementById('projectType');
    const complexity = document.getElementById('complexity');
    const codeGenerationProcess = document.getElementById('codeGenerationProcess');
    const projectFilesList = document.getElementById('projectFilesList');
    const codeEditor = document.getElementById('codeEditor');
    const codeContent = document.getElementById('codeContent');
    const fileTabs = document.getElementById('fileTabs');
    const filesList = document.getElementById('filesList');
    const previewFrame = document.getElementById('previewFrame');
    const typingIndicator = document.getElementById('typingIndicator');
    const copyAllCodeBtn = document.getElementById('copyAllCodeBtn');
    const downloadCodeBtn = document.getElementById('downloadCodeBtn');
    const refreshPreviewBtn = document.getElementById('refreshPreviewBtn');
    const openPreviewBtn = document.getElementById('openPreviewBtn');

    // Project files storage
    let projectFiles = {};
    let currentFile = '';
    let isGenerating = false;

    // Check if Prism.js is available for syntax highlighting
    let prismAvailable = typeof Prism !== 'undefined';
    if (!prismAvailable) {
        console.warn('Prism.js not available - code highlighting will be disabled');
        // Load Prism.js dynamically
        loadScript('https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js', function() {
            loadCSS('https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css');
            prismAvailable = true;
            console.log('Prism.js loaded dynamically');
        });
    }

    // Helper function to load scripts dynamically
    function loadScript(url, callback) {
        const script = document.createElement('script');
        script.src = url;
        script.onload = callback;
        document.head.appendChild(script);
    }

    // Helper function to load CSS dynamically
    function loadCSS(url) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        document.head.appendChild(link);
    }

    // Helper function to get language class for syntax highlighting
    function getLanguageClass(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'js': return 'language-javascript';
            case 'html': return 'language-html';
            case 'css': return 'language-css';
            case 'py': return 'language-python';
            case 'java': return 'language-java';
            case 'c': return 'language-c';
            case 'cpp': return 'language-cpp';
            case 'json': return 'language-json';
            case 'md': return 'language-markdown';
            default: return 'language-plaintext';
        }
    }

    // Helper function to get file icon based on extension
    function getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        switch (ext) {
            case 'js': return '<i class="fas fa-file-code text-yellow-500"></i>';
            case 'html': return '<i class="fas fa-file-code text-orange-500"></i>';
            case 'css': return '<i class="fas fa-file-code text-blue-500"></i>';
            case 'py': return '<i class="fas fa-file-code text-green-500"></i>';
            case 'java': return '<i class="fas fa-file-code text-red-500"></i>';
            case 'c':
            case 'cpp': return '<i class="fas fa-file-code text-purple-500"></i>';
            case 'json': return '<i class="fas fa-file-code text-gray-500"></i>';
            case 'md': return '<i class="fas fa-file-alt text-gray-500"></i>';
            case 'jpg':
            case 'jpeg':
            case 'png':
            case 'gif': return '<i class="fas fa-file-image text-green-500"></i>';
            default: return '<i class="fas fa-file text-gray-500"></i>';
        }
    }

    // Helper function to format file size
    function formatFileSize(size) {
        if (size < 1024) return size + ' B';
        else if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB';
        else return (size / (1024 * 1024)).toFixed(1) + ' MB';
    }

    // Helper function to create a file tab
    function createFileTab(filename, isActive = false) {
        const tab = document.createElement('button');
        tab.className = `px-4 py-2 text-sm font-medium text-gray-700 border-b-2 border-transparent hover:text-black hover:border-gray-300 ${isActive ? 'active-file-tab' : ''}`;
        tab.setAttribute('data-file', filename);
        tab.textContent = filename;
        tab.addEventListener('click', function() {
            switchToFile(filename);
        });
        return tab;
    }

    // Helper function to create a file card
    function createFileCard(filename, content) {
        const size = new Blob([content]).size;
        const card = document.createElement('div');
        card.className = 'file-card cursor-pointer';
        card.innerHTML = `
            <div class="flex items-center">
                <span class="file-icon">${getFileIcon(filename)}</span>
                <span class="file-name">${filename}</span>
            </div>
            <div class="file-size mt-2">${formatFileSize(size)}</div>
        `;
        card.addEventListener('click', function() {
            switchToFile(filename);
        });
        return card;
    }

    // Function to switch to a different file
    function switchToFile(filename) {
        if (!projectFiles[filename]) return;

        // Update active tab
        document.querySelectorAll('#fileTabs button').forEach(tab => {
            tab.classList.remove('active-file-tab');
        });
        const tab = document.querySelector(`#fileTabs button[data-file="${filename}"]`);
        if (tab) tab.classList.add('active-file-tab');

        // Update code editor
        currentFile = filename;
        codeEditor.className = getLanguageClass(filename);
        codeContent.textContent = projectFiles[filename];

        // Apply syntax highlighting
        if (prismAvailable && typeof Prism !== 'undefined') {
            Prism.highlightElement(codeContent);
        }
    }

    // Helper function to get appropriate icon for file type
    function getFileIcon(filename) {
        if (filename.endsWith('.py')) return '🐍';
        if (filename.endsWith('.html')) return '🌐';
        if (filename.endsWith('.css')) return '🎨';
        if (filename.endsWith('.js')) return '📜';
        if (filename.endsWith('.md')) return '📝';
        if (filename.endsWith('.json')) return '📊';
        if (filename.endsWith('.txt')) return '📄';
        if (filename.includes('README')) return '📚';
        return '📁';
    }

    // Variables for code execution
    let currentExecutionId = null;
    let executionStatusInterval = null;

    // Function to execute Python code on the server
    function executePythonCode() {
        // Check if we have files to execute
        if (Object.keys(projectFiles).length === 0) {
            return;
        }

        // Prepare files for execution
        const files = [];
        Object.keys(projectFiles).forEach(filename => {
            files.push({
                name: filename,
                content: projectFiles[filename]
            });
        });

        // Stop any existing execution
        if (currentExecutionId) {
            stopExecution();
        }

        // Show loading state in preview
        previewFrame.srcdoc = `
            <html>
            <head>
                <style>
                    body { font-family: sans-serif; padding: 20px; background-color: #f5f5f5; }
                    .loading { text-align: center; margin-top: 50px; }
                    .spinner { display: inline-block; width: 50px; height: 50px; border: 5px solid rgba(0, 0, 0, 0.1); border-radius: 50%; border-top-color: #333; animation: spin 1s ease-in-out infinite; }
                    @keyframes spin { to { transform: rotate(360deg); } }
                </style>
            </head>
            <body>
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Executing code...</p>
                </div>
            </body>
            </html>
        `;

        // Execute the project
        fetch('/api/code-executor/execute-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                files: files
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Store the execution ID
                currentExecutionId = data.project_id;

                // Start polling for execution status
                if (executionStatusInterval) {
                    clearInterval(executionStatusInterval);
                }

                executionStatusInterval = setInterval(() => {
                    updateExecutionStatus();
                }, 1000);
            } else {
                // Show error in preview
                previewFrame.srcdoc = `
                    <html>
                    <head>
                        <style>
                            body { font-family: sans-serif; padding: 20px; background-color: #f5f5f5; }
                            .error { color: red; font-weight: bold; }
                        </style>
                    </head>
                    <body>
                        <h2>Error executing code</h2>
                        <div class="error">${data.error || 'Unknown error'}</div>
                    </body>
                    </html>
                `;
            }
        })
        .catch(error => {
            console.error('Error executing project:', error);

            // Show error in preview
            previewFrame.srcdoc = `
                <html>
                <head>
                    <style>
                        body { font-family: sans-serif; padding: 20px; background-color: #f5f5f5; }
                        .error { color: red; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <h2>Error executing code</h2>
                    <div class="error">${error.message || 'Unknown error'}</div>
                </body>
                </html>
            `;
        });
    }

    // Function to update execution status
    function updateExecutionStatus() {
        if (!currentExecutionId) {
            return;
        }

        fetch(`/api/code-executor/status/${currentExecutionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.status;

                // Update preview based on status
                if (status.status === 'completed' || status.status === 'error') {
                    // Stop polling
                    if (executionStatusInterval) {
                        clearInterval(executionStatusInterval);
                        executionStatusInterval = null;
                    }
                }

                // Update preview with output and images
                updatePreviewWithExecutionResult(status);
            }
        })
        .catch(error => {
            console.error('Error getting execution status:', error);
        });
    }

    // Function to stop execution
    function stopExecution() {
        if (!currentExecutionId) {
            return;
        }

        fetch(`/api/code-executor/stop/${currentExecutionId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            // Stop polling
            if (executionStatusInterval) {
                clearInterval(executionStatusInterval);
                executionStatusInterval = null;
            }

            // Clear execution ID
            currentExecutionId = null;
        })
        .catch(error => {
            console.error('Error stopping execution:', error);
        });
    }

    // Function to update preview with execution result
    function updatePreviewWithExecutionResult(status) {
        // Create HTML content for preview
        let previewContent = `
            <html>
            <head>
                <style>
                    body { font-family: sans-serif; padding: 20px; background-color: #f5f5f5; }
                    .output { background-color: #000; color: #0f0; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }
                    .error { color: red; }
                    .images { margin-top: 20px; text-align: center; }
                    .images img { max-width: 100%; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 5px; }
                    .status { margin-bottom: 10px; font-weight: bold; }
                    .running { color: blue; }
                    .completed { color: green; }
                    .error-status { color: red; }
                </style>
            </head>
            <body>
                <div class="status ${status.status === 'running' ? 'running' : status.status === 'completed' ? 'completed' : 'error-status'}">
                    Status: ${status.status.toUpperCase()}
                </div>
        `;

        // Add output
        if (status.output) {
            previewContent += `
                <h3>Output:</h3>
                <div class="output">${status.output.replace(/\n/g, '<br>')}</div>
            `;
        }

        // Add images
        if (status.images && status.images.length > 0) {
            previewContent += `
                <div class="images">
                    <h3>Visualization:</h3>
            `;

            // Add the latest image
            const latestImage = status.images[status.images.length - 1];
            previewContent += `
                <img src="data:image/png;base64,${latestImage}" alt="Execution visualization">
            `;

            previewContent += `
                </div>
            `;
        }

        previewContent += `
            </body>
            </html>
        `;

        // Update preview iframe
        previewFrame.srcdoc = previewContent;
    }

    // Function to update the preview
    function updatePreview() {
        // Check if this is a Python project (has .py files)
        const hasPythonFiles = Object.keys(projectFiles).some(filename => filename.endsWith('.py'));
        console.log('Python code execution enabled');

        if (hasPythonFiles && !projectFiles['index.html']) {
            // Execute Python code on the server and show live output
            executePythonCode();
            return;
        }
        else if (!projectFiles['index.html']) {
            // If there's no index.html, create a simple preview with the available files
            let previewContent = `
                <html>
                <head>
                    <title>Project Preview</title>
                    <style>
                        body { font-family: sans-serif; padding: 20px; background-color: #f5f5f5; }
                        h1 { color: #333; text-align: center; margin-bottom: 20px; }
                        .preview-container { max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); }
                        .file-list { margin-top: 20px; }
                        .file-item { padding: 12px; border-bottom: 1px solid #eee; display: flex; align-items: center; }
                        .file-icon { margin-right: 10px; color: #3498db; }
                    </style>
                </head>
                <body>
                    <div class="preview-container">
                        <h1>Project Files</h1>
                        <div class="file-list">
            `;

            Object.keys(projectFiles).forEach(filename => {
                const icon = getFileIcon(filename);
                previewContent += `<div class="file-item"><span class="file-icon">${icon}</span> ${filename}</div>`;
            });

            previewContent += `
                        </div>
                    </div>
                </body>
                </html>
            `;

            previewFrame.srcdoc = previewContent;
            return;
        }

        // For web projects with index.html
        let htmlContent = projectFiles['index.html'];

        // Inject CSS files
        Object.keys(projectFiles).forEach(filename => {
            if (filename.endsWith('.css')) {
                htmlContent = htmlContent.replace('</head>', `<style>${projectFiles[filename]}</style></head>`);
            }
        });

        // Inject JavaScript files
        Object.keys(projectFiles).forEach(filename => {
            if (filename.endsWith('.js')) {
                htmlContent = htmlContent.replace('</body>', `<script>${projectFiles[filename]}</script></body>`);
            }
        });

        // Update the preview iframe
        previewFrame.srcdoc = htmlContent;
    }

    // Function to simulate typing effect
    function simulateTyping(element, text, speed = 10, startIndex = 0, callback = null) {
        if (startIndex === 0) {
            element.textContent = '';
            typingIndicator.style.display = 'flex';
        }

        if (startIndex < text.length) {
            element.textContent += text.charAt(startIndex);
            setTimeout(() => {
                simulateTyping(element, text, speed, startIndex + 1, callback);
            }, speed);
        } else {
            typingIndicator.style.display = 'none';
            if (callback) callback();
        }
    }

    // Function to add a file to the project
    function addFile(filename, content) {
        projectFiles[filename] = content;

        // Add file tab if it doesn't exist
        if (!document.querySelector(`#fileTabs button[data-file="${filename}"]`)) {
            const isFirstFile = Object.keys(projectFiles).length === 1;
            fileTabs.appendChild(createFileTab(filename, isFirstFile));
        }

        // Add file card if it doesn't exist
        if (!document.querySelector(`#filesList .file-card[data-file="${filename}"]`)) {
            const card = createFileCard(filename, content);
            card.setAttribute('data-file', filename);
            filesList.appendChild(card);
        }

        // Switch to this file if it's the first one
        if (Object.keys(projectFiles).length === 1) {
            switchToFile(filename);
        }

        // Always update preview when a file is added or modified
        updatePreview();
    }

    // Function to generate code with typing effect
    function generateCodeWithTypingEffect(files) {
        isGenerating = true;
        let fileIndex = 0;

        // Initialize preview immediately
        files.forEach(file => {
            projectFiles[file.name] = ''; // Add empty files first
        });
        updatePreview(); // Show initial preview

        function processNextFile() {
            if (fileIndex >= files.length) {
                isGenerating = false;
                return;
            }

            const file = files[fileIndex];
            addFile(file.name, ''); // Add empty file first
            switchToFile(file.name); // Switch to this file

            // Track progress for real-time preview updates
            let currentProgress = 0;
            const totalLength = file.content.length;
            const updateInterval = Math.max(50, Math.floor(totalLength / 20)); // Update every ~5% of content

            // Simulate typing for this file with progress updates
            function typeWithUpdates(element, text, speed, index) {
                if (index === 0) {
                    element.textContent = '';
                    typingIndicator.style.display = 'flex';
                }

                if (index < text.length) {
                    element.textContent += text.charAt(index);

                    // Update project files and preview at intervals
                    if (index % updateInterval === 0 || index === text.length - 1) {
                        projectFiles[file.name] = element.textContent;
                        updatePreview();
                    }

                    setTimeout(() => {
                        typeWithUpdates(element, text, speed, index + 1);
                    }, speed);
                } else {
                    typingIndicator.style.display = 'none';
                    // Final update with complete content
                    projectFiles[file.name] = text;
                    updatePreview();

                    // Apply syntax highlighting
                    if (prismAvailable && typeof Prism !== 'undefined') {
                        Prism.highlightElement(codeContent);
                    }

                    // Process next file
                    fileIndex++;
                    setTimeout(processNextFile, 500);
                }
            }

            // Start typing with updates
            typeWithUpdates(codeContent, file.content, 5, 0);
        }

        // Start processing files
        processNextFile();
    }

    // Function to handle build project button click
    if (buildProjectBtn) {
        buildProjectBtn.addEventListener('click', function() {
            const prompt = codePrompt.value.trim();
            if (!prompt) {
                alert('Please enter a project description');
                return;
            }

            // Show code generation process
            codeGenerationProcess.classList.remove('hidden');
            projectFilesList.classList.remove('hidden');

            // Clear previous project
            projectFiles = {};
            fileTabs.innerHTML = '';
            filesList.innerHTML = '';
            codeContent.textContent = '// Generating code...';

            // Disable button during request
            buildProjectBtn.disabled = true;
            buildProjectBtn.classList.add('opacity-50', 'cursor-not-allowed');
            buildProjectBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...`;

            // Make API request
            fetch('/api/super-agent/generate-project', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    prompt: prompt,
                    project_type: projectType.value,
                    complexity: complexity.value
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.files && data.files.length > 0) {
                    // Generate code with typing effect
                    generateCodeWithTypingEffect(data.files);
                } else {
                    // Show error
                    codeContent.textContent = data.error || 'Failed to generate project. Please try again.';
                }
            })
            .catch(error => {
                console.error('Error generating project:', error);
                codeContent.textContent = `Error: ${error.message || 'Failed to generate project'}`;
            })
            .finally(() => {
                // Re-enable button
                buildProjectBtn.disabled = false;
                buildProjectBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                buildProjectBtn.innerHTML = `
                    <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                    Build Project`;
            });
        });
    }

    // Copy all code button
    if (copyAllCodeBtn) {
        copyAllCodeBtn.addEventListener('click', function() {
            if (currentFile && projectFiles[currentFile]) {
                navigator.clipboard.writeText(projectFiles[currentFile]).then(() => {
                    // Show success message
                    const originalTitle = copyAllCodeBtn.getAttribute('title');
                    copyAllCodeBtn.setAttribute('title', 'Copied!');
                    setTimeout(() => {
                        copyAllCodeBtn.setAttribute('title', originalTitle);
                    }, 2000);
                });
            }
        });
    }

    // Download code button
    if (downloadCodeBtn) {
        downloadCodeBtn.addEventListener('click', function() {
            if (Object.keys(projectFiles).length === 0) return;

            // If only one file, download it directly
            if (Object.keys(projectFiles).length === 1) {
                const filename = Object.keys(projectFiles)[0];
                const content = projectFiles[filename];
                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                a.click();
                URL.revokeObjectURL(url);
                return;
            }

            // For multiple files, create a zip file
            if (typeof JSZip === 'undefined') {
                // Load JSZip dynamically if not available
                loadScript('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.7.1/jszip.min.js', function() {
                    createAndDownloadZip();
                });
            } else {
                createAndDownloadZip();
            }

            function createAndDownloadZip() {
                const zip = new JSZip();

                // Add all files to the zip
                Object.keys(projectFiles).forEach(filename => {
                    zip.file(filename, projectFiles[filename]);
                });

                // Generate and download the zip
                zip.generateAsync({ type: 'blob' }).then(function(content) {
                    const url = URL.createObjectURL(content);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'project.zip';
                    a.click();
                    URL.revokeObjectURL(url);
                });
            }
        });
    }

    // Refresh preview button
    if (refreshPreviewBtn) {
        refreshPreviewBtn.addEventListener('click', function() {
            updatePreview();
        });
    }

    // Open preview in new window button
    if (openPreviewBtn) {
        openPreviewBtn.addEventListener('click', function() {
            if (!projectFiles['index.html']) {
                alert('No HTML file to preview');
                return;
            }

            // Create a blob with the HTML content
            let htmlContent = projectFiles['index.html'];

            // Inject CSS files
            Object.keys(projectFiles).forEach(filename => {
                if (filename.endsWith('.css')) {
                    htmlContent = htmlContent.replace('</head>', `<style>${projectFiles[filename]}</style></head>`);
                }
            });

            // Inject JavaScript files
            Object.keys(projectFiles).forEach(filename => {
                if (filename.endsWith('.js')) {
                    htmlContent = htmlContent.replace('</body>', `<script>${projectFiles[filename]}</script></body>`);
                }
            });

            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            window.open(url, '_blank');
        });
    }

    // Add example files for testing
    if (window.location.search.includes('test=true')) {
        setTimeout(() => {
            const testFiles = [
                {
                    name: 'index.html',
                    content: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo App</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>Todo List</h1>
        <div class="todo-app">
            <div class="input-section">
                <input type="text" id="taskInput" placeholder="Add a new task...">
                <button id="addTaskBtn">Add</button>
            </div>
            <ul id="taskList"></ul>
        </div>
    </div>
    <script src="app.js"></script>
</body>
</html>`
                },
                {
                    name: 'styles.css',
                    content: `* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Arial', sans-serif;
}

body {
    background-color: #f5f5f5;
    color: #333;
}

.container {
    max-width: 600px;
    margin: 50px auto;
    padding: 20px;
}

h1 {
    text-align: center;
    margin-bottom: 20px;
    color: #2c3e50;
}

.todo-app {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
}

.input-section {
    display: flex;
    margin-bottom: 20px;
}

input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px 0 0 4px;
    font-size: 16px;
}

button {
    padding: 10px 20px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 0 4px 4px 0;
    cursor: pointer;
    font-size: 16px;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #2980b9;
}

ul {
    list-style-type: none;
}

li {
    padding: 10px 15px;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

li:last-child {
    border-bottom: none;
}

.delete-btn {
    background-color: #e74c3c;
    padding: 5px 10px;
    border-radius: 4px;
}

.delete-btn:hover {
    background-color: #c0392b;
}

.completed {
    text-decoration: line-through;
    color: #7f8c8d;
}`
                },
                {
                    name: 'app.js',
                    content: `document.addEventListener('DOMContentLoaded', function() {
    const taskInput = document.getElementById('taskInput');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const taskList = document.getElementById('taskList');

    // Load tasks from localStorage
    let tasks = JSON.parse(localStorage.getItem('tasks')) || [];

    // Render initial tasks
    renderTasks();

    // Add task event
    addTaskBtn.addEventListener('click', addTask);
    taskInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addTask();
        }
    });

    // Function to add a new task
    function addTask() {
        const taskText = taskInput.value.trim();
        if (taskText) {
            tasks.push({
                id: Date.now(),
                text: taskText,
                completed: false
            });
            saveTasks();
            renderTasks();
            taskInput.value = '';
        }
    }

    // Function to toggle task completion
    function toggleTask(id) {
        tasks = tasks.map(task => {
            if (task.id === id) {
                return { ...task, completed: !task.completed };
            }
            return task;
        });
        saveTasks();
        renderTasks();
    }

    // Function to delete a task
    function deleteTask(id) {
        tasks = tasks.filter(task => task.id !== id);
        saveTasks();
        renderTasks();
    }

    // Function to save tasks to localStorage
    function saveTasks() {
        localStorage.setItem('tasks', JSON.stringify(tasks));
    }

    // Function to render tasks
    function renderTasks() {
        taskList.innerHTML = '';
        tasks.forEach(task => {
            const li = document.createElement('li');

            // Create task text span
            const taskText = document.createElement('span');
            taskText.textContent = task.text;
            if (task.completed) {
                taskText.classList.add('completed');
            }
            taskText.addEventListener('click', () => toggleTask(task.id));

            // Create delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.classList.add('delete-btn');
            deleteBtn.addEventListener('click', () => deleteTask(task.id));

            // Append elements to list item
            li.appendChild(taskText);
            li.appendChild(deleteBtn);

            // Append list item to task list
            taskList.appendChild(li);
        });
    }
});`
                }
            ];

            // Show code generation process
            codeGenerationProcess.classList.remove('hidden');
            projectFilesList.classList.remove('hidden');

            // Generate code with typing effect
            generateCodeWithTypingEffect(testFiles);
        }, 1000);
    }
});
