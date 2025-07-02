// Function to execute Python code on the server
function executePythonCode() {
    // Show loading indicator in the preview
    previewFrame.srcdoc = `
        <html>
        <head>
            <style>
                body { font-family: monospace; padding: 20px; background-color: #1e1e1e; color: #f0f0f0; }
                .output { white-space: pre-wrap; }
                .loading { text-align: center; margin: 20px 0; }
                .loading-spinner { display: inline-block; width: 30px; height: 30px; border: 3px solid rgba(255,255,255,.3); border-radius: 50%; border-top-color: #fff; animation: spin 1s ease-in-out infinite; }
                @keyframes spin { to { transform: rotate(360deg); } }
                .error { color: #ff6b6b; }
                .success { color: #6bff6b; }
                .warning { color: #ffff6b; }
                .controls { margin-top: 20px; }
                button { background-color: #333; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #444; }
            </style>
        </head>
        <body>
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>Executing code...</p>
            </div>
            <div class="output"></div>
            <div class="controls" style="display: none;">
                <button onclick="window.location.reload()">Run Again</button>
            </div>
            <script>
                // Function to update the output
                function updateOutput(text) {
                    document.querySelector('.output').innerHTML = text
                        .replace(/\\n/g, '<br>')
                        .replace(/ERROR:/g, '<span class="error">ERROR:</span>')
                        .replace(/WARNING:/g, '<span class="warning">WARNING:</span>')
                        .replace(/Execution completed successfully/g, '<span class="success">Execution completed successfully</span>');
                }

                // Function to hide the loading indicator
                function hideLoading() {
                    document.querySelector('.loading').style.display = 'none';
                    document.querySelector('.controls').style.display = 'block';
                }
            </script>
        </body>
        </html>
    `;

    // Prepare the files for execution
    const files = [];
    for (const filename in projectFiles) {
        files.push({
            name: filename,
            content: projectFiles[filename]
        });
    }

    // Send the files to the server for execution
    fetch('/api/code-executor/execute-project', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ files })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Start polling for execution status
            const projectId = data.project_id;
            pollExecutionStatus(projectId);
        } else {
            // Show error in the preview
            const errorMessage = data.error || 'Failed to execute code';
            previewFrame.contentWindow.updateOutput(`Error: ${errorMessage}`);
            previewFrame.contentWindow.hideLoading();
        }
    })
    .catch(error => {
        console.error('Error executing code:', error);
        previewFrame.contentWindow.updateOutput(`Error: ${error.message}`);
        previewFrame.contentWindow.hideLoading();
    });
}

// Function to poll for execution status
function pollExecutionStatus(projectId) {
    let lastOutputLength = 0;
    const maxPolls = 30; // Maximum number of polls (30 seconds)
    let pollCount = 0;
    
    const pollInterval = setInterval(() => {
        pollCount++;
        
        fetch(`/api/code-executor/status/${projectId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const status = data.status;
                    
                    // Update the output in the preview if there's new content
                    if (status.output && status.output.length > lastOutputLength) {
                        lastOutputLength = status.output.length;
                        previewFrame.contentWindow.updateOutput(status.output);
                    }
                    
                    // If execution is complete, stop polling
                    if (status.status === 'completed' || status.status === 'error' || status.status === 'stopped') {
                        clearInterval(pollInterval);
                        previewFrame.contentWindow.hideLoading();
                    }
                    
                    // If we've reached the maximum number of polls, stop polling
                    if (pollCount >= maxPolls) {
                        clearInterval(pollInterval);
                        previewFrame.contentWindow.updateOutput(status.output + '\n\nExecution timed out after 30 seconds.');
                        previewFrame.contentWindow.hideLoading();
                        
                        // Stop the execution on the server
                        fetch(`/api/code-executor/stop/${projectId}`, {
                            method: 'POST'
                        }).catch(error => console.error('Error stopping execution:', error));
                    }
                } else {
                    // Show error in the preview
                    const errorMessage = data.error || 'Failed to get execution status';
                    previewFrame.contentWindow.updateOutput(`Error: ${errorMessage}`);
                    previewFrame.contentWindow.hideLoading();
                    clearInterval(pollInterval);
                }
            })
            .catch(error => {
                console.error('Error polling execution status:', error);
                previewFrame.contentWindow.updateOutput(`Error polling execution status: ${error.message}`);
                previewFrame.contentWindow.hideLoading();
                clearInterval(pollInterval);
            });
    }, 1000); // Poll every second
}
