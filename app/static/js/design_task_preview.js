/**
 * Design Task Preview
 * Provides live preview functionality for design tasks
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the design task preview
    initDesignTaskPreview();

    // Also check periodically for new design tasks
    setInterval(checkForDesignTasks, 2000);
});

function initDesignTaskPreview() {
    // Create a hidden iframe for previewing HTML
    const previewFrame = document.createElement('iframe');
    previewFrame.id = 'design-preview-frame';
    previewFrame.style.display = 'none';
    document.body.appendChild(previewFrame);

    // Add a mutation observer to detect new task summaries
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                checkForDesignTasks();
            }
        });
    });

    // Start observing the document body for changes
    observer.observe(document.body, { childList: true, subtree: true });
}

function checkForDesignTasks() {
    console.log('Checking for design tasks...');

    // Get all summary containers
    const summaryContainers = document.querySelectorAll('.summary-container-content');

    summaryContainers.forEach(container => {
        // Skip if already processed
        if (container.getAttribute('data-design-processed') === 'true') {
            return;
        }

        // Check if this is a design task result
        if (isDesignTask(container)) {
            console.log('Found design task!');
            transformDesignTask(container);
            container.setAttribute('data-design-processed', 'true');
        }
    });

    // Also check the task results div (for compatibility with different UI versions)
    const taskResults = document.getElementById('taskResults');
    if (taskResults && !taskResults.getAttribute('data-design-processed')) {
        if (isDesignTask(taskResults)) {
            console.log('Found design task in taskResults!');
            transformDesignTask(taskResults);
            taskResults.setAttribute('data-design-processed', 'true');
        }
    }
}

function isDesignTask(container) {
    // Look for design task markers in the content
    const content = container.innerHTML || '';

    // Check for webpage design
    if (content.includes('<h1>Webpage Design</h1>') ||
        content.includes('<h1>Website Design</h1>') ||
        content.includes('<h2>HTML Code</h2>') ||
        content.includes('```html') && content.includes('```css')) {
        console.log('Detected webpage design task');
        return true;
    }

    // Check for diagram design
    if (content.includes('<h1>Flowchart Diagram</h1>') ||
        content.includes('<h1>Sequence Diagram</h1>') ||
        content.includes('<h1>Class Diagram</h1>') ||
        content.includes('<h1>Entity-relationship Diagram</h1>') ||
        content.includes('<h1>Gantt Diagram</h1>') ||
        content.includes('<h1>Pie Diagram</h1>') ||
        content.includes('<h1>Mindmap Diagram</h1>') ||
        content.includes('<h1>Uml Diagram</h1>') ||
        content.includes('```mermaid') ||
        content.includes('```plantuml')) {
        console.log('Detected diagram design task');
        return true;
    }

    // Check for PDF design
    if (content.includes('<h1>PDF Document:</h1>') ||
        content.includes('<h1>PDF Document</h1>') ||
        content.includes('Download PDF')) {
        console.log('Detected PDF design task');
        return true;
    }

    return false;
}

function transformDesignTask(container) {
    // Get the content
    const content = container.innerHTML;

    // Determine the design type
    let designType = 'unknown';
    let designTitle = 'Design Result';

    if (content.includes('<h1>Webpage Design</h1>') ||
        content.includes('<h1>Website Design</h1>')) {
        designType = 'webpage';
        designTitle = 'Webpage Design';
    } else if (content.includes('<h1>Flowchart Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Flowchart Diagram';
    } else if (content.includes('<h1>Sequence Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Sequence Diagram';
    } else if (content.includes('<h1>Class Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Class Diagram';
    } else if (content.includes('<h1>Entity-relationship Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Entity-Relationship Diagram';
    } else if (content.includes('<h1>Gantt Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Gantt Chart';
    } else if (content.includes('<h1>Pie Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Pie Chart';
    } else if (content.includes('<h1>Mindmap Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'Mind Map';
    } else if (content.includes('<h1>Uml Diagram</h1>')) {
        designType = 'diagram';
        designTitle = 'UML Diagram';
    } else if (content.includes('<h1>PDF Document:</h1>') ||
               content.includes('<h1>PDF Document</h1>')) {
        designType = 'pdf';
        // Extract the title
        const titleMatch = content.match(/<h1>PDF Document: (.*?)<\/h1>/);
        if (titleMatch && titleMatch[1]) {
            designTitle = 'PDF Document: ' + titleMatch[1];
        } else {
            designTitle = 'PDF Document';
        }
    }

    // Extract preview image
    let previewImage = '';
    const imgMatch = content.match(/<img[^>]*src="([^"]*)"[^>]*>/);
    if (imgMatch && imgMatch[1]) {
        previewImage = imgMatch[1];
    }

    // Extract code blocks
    const codeBlocks = [];

    if (designType === 'webpage') {
        // Extract HTML code
        let htmlCode = '';
        const htmlMatch = content.match(/```html\n([\s\S]*?)```/);
        if (htmlMatch && htmlMatch[1]) {
            htmlCode = htmlMatch[1];
        } else {
            // Try alternative format
            const altHtmlMatch = content.match(/<h2>HTML Code<\/h2>\s*<pre><code>([\s\S]*?)<\/code><\/pre>/);
            if (altHtmlMatch && altHtmlMatch[1]) {
                htmlCode = altHtmlMatch[1];
            }
        }

        if (htmlCode) {
            codeBlocks.push({
                language: 'html',
                filename: 'index.html',
                code: htmlCode
            });
        }

        // Extract CSS code
        let cssCode = '';
        const cssMatch = content.match(/```css\n([\s\S]*?)```/);
        if (cssMatch && cssMatch[1]) {
            cssCode = cssMatch[1];
        } else {
            // Try alternative format
            const altCssMatch = content.match(/<h2>CSS Code<\/h2>\s*<pre><code>([\s\S]*?)<\/code><\/pre>/);
            if (altCssMatch && altCssMatch[1]) {
                cssCode = altCssMatch[1];
            }
        }

        if (cssCode) {
            codeBlocks.push({
                language: 'css',
                filename: 'styles.css',
                code: cssCode
            });
        }

        // Extract JavaScript code
        let jsCode = '';
        const jsMatch = content.match(/```javascript\n([\s\S]*?)```/);
        if (jsMatch && jsMatch[1]) {
            jsCode = jsMatch[1];
        } else {
            // Try alternative format
            const altJsMatch = content.match(/<h2>JavaScript Code<\/h2>\s*<pre><code>([\s\S]*?)<\/code><\/pre>/);
            if (altJsMatch && altJsMatch[1]) {
                jsCode = altJsMatch[1];
            }
        }

        if (jsCode) {
            codeBlocks.push({
                language: 'javascript',
                filename: 'app.js',
                code: jsCode
            });
        }
    } else if (designType === 'diagram') {
        // Extract diagram code
        const diagramMatch = content.match(/```(?:mermaid|plantuml)?\n([\s\S]*?)```/);
        if (diagramMatch && diagramMatch[1]) {
            codeBlocks.push({
                language: 'diagram',
                filename: 'diagram.md',
                code: diagramMatch[1]
            });
        }
    } else if (designType === 'pdf') {
        // Extract PDF download link
        const pdfMatch = content.match(/\[Download PDF\]\((data:application\/pdf;base64,[^)]*)\)/);
        if (pdfMatch && pdfMatch[1]) {
            codeBlocks.push({
                language: 'pdf',
                filename: 'document.pdf',
                code: pdfMatch[1]
            });
        }
    }

    // Create the enhanced design task display
    const enhancedDisplay = createDesignTaskDisplay(designType, designTitle, previewImage, codeBlocks);

    // Replace the container content
    container.innerHTML = enhancedDisplay;

    // Add event listeners for tabs
    addTabEventListeners(container, designType, codeBlocks);
}

function createDesignTaskDisplay(designType, designTitle, previewImage, codeBlocks) {
    // Create the container
    let html = `
        <div class="design-container">
            <div class="design-header">
                <h3>${designTitle}</h3>
                <div class="design-header-actions">
                    <button class="design-copy-btn" title="Copy to clipboard">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                            <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                        </svg>
                    </button>
                    <button class="design-download-btn" title="Download files">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                            <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="design-tabs">
                <div class="design-tab active" data-tab="preview">Preview</div>
                <div class="design-tab" data-tab="code">Code</div>
            </div>
            <div class="design-content">
                <div class="design-tab-content active" data-tab-content="preview">
                    <div class="design-preview">
                        ${designType === 'webpage' ?
                            `<div class="live-preview-container">
                                <iframe id="live-preview-frame-${Date.now()}" class="live-preview-frame" sandbox="allow-scripts"></iframe>
                             </div>` :
                            (previewImage ? `<img src="${previewImage}" alt="${designTitle}">` : '<p>No preview available</p>')}
                    </div>
                </div>
                <div class="design-tab-content" data-tab-content="code">
                    <div class="design-code">
    `;

    // Add code blocks
    if (codeBlocks.length > 0) {
        codeBlocks.forEach(block => {
            html += `
                <div class="design-code-file">
                    <div class="design-code-file-header">
                        <span>${block.filename}</span>
                        <button class="design-code-copy-btn" title="Copy code" data-filename="${block.filename}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                                <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                            </svg>
                        </button>
                    </div>
                    <pre class="design-code-file-content"><code class="language-${block.language}">${escapeHtml(block.code)}</code></pre>
                </div>
            `;
        });

        // Add download button for all files
        if (designType === 'webpage') {
            html += `
                <div class="text-center">
                    <button class="design-download-all-btn design-download">Download All Files</button>
                </div>
            `;
        } else if (designType === 'pdf') {
            const pdfData = codeBlocks[0].code;
            html += `
                <div class="text-center">
                    <a href="${pdfData}" download="document.pdf" class="design-download">Download PDF</a>
                </div>
            `;
        }
    } else {
        html += '<p>No code available</p>';
    }

    html += `
                    </div>
                </div>
            </div>
        </div>
    `;

    return html;
}

function addTabEventListeners(container, designType, codeBlocks) {
    // Get all tabs in this container
    const tabs = container.querySelectorAll('.design-tab');

    // If this is a webpage, set up the live preview
    if (designType === 'webpage') {
        setupLivePreview(container, codeBlocks);
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Get the tab name
            const tabName = this.getAttribute('data-tab');

            // Remove active class from all tabs
            container.querySelectorAll('.design-tab').forEach(t => {
                t.classList.remove('active');
            });

            // Add active class to this tab
            this.classList.add('active');

            // Hide all tab content
            container.querySelectorAll('.design-tab-content').forEach(c => {
                c.classList.remove('active');
            });

            // Show the selected tab content
            container.querySelector(`.design-tab-content[data-tab-content="${tabName}"]`).classList.add('active');
        });
    });

    // Add event listeners for copy buttons
    const copyButtons = container.querySelectorAll('.design-code-copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the filename
            const filename = this.getAttribute('data-filename');

            // Get the code
            const codeElement = this.closest('.design-code-file').querySelector('code');
            const code = codeElement.textContent;

            // Copy to clipboard
            navigator.clipboard.writeText(code).then(() => {
                // Show success message
                const originalText = this.innerHTML;
                this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>';

                // Reset after 2 seconds
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    });

    // Add event listener for copy all button
    const copyAllButton = container.querySelector('.design-copy-btn');
    if (copyAllButton) {
        copyAllButton.addEventListener('click', function() {
            // Get all code blocks
            const codeBlocks = container.querySelectorAll('.design-code-file');
            let allCode = '';

            codeBlocks.forEach(block => {
                const filename = block.querySelector('.design-code-file-header span').textContent;
                const code = block.querySelector('code').textContent;

                allCode += `// ${filename}\n${code}\n\n`;
            });

            // Copy to clipboard
            navigator.clipboard.writeText(allCode).then(() => {
                // Show success message
                const originalText = this.innerHTML;
                this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>';

                // Reset after 2 seconds
                setTimeout(() => {
                    this.innerHTML = originalText;
                }, 2000);
            });
        });
    }

    // Add event listener for download all button
    const downloadAllButton = container.querySelector('.design-download-all-btn');
    if (downloadAllButton) {
        downloadAllButton.addEventListener('click', function() {
            // Get all code blocks
            const codeBlocks = container.querySelectorAll('.design-code-file');
            const files = [];

            codeBlocks.forEach(block => {
                const filename = block.querySelector('.design-code-file-header span').textContent;
                const code = block.querySelector('code').textContent;

                files.push({
                    name: filename,
                    content: code
                });
            });

            // Create a zip file
            if (typeof JSZip !== 'undefined') {
                const zip = new JSZip();

                files.forEach(file => {
                    zip.file(file.name, file.content);
                });

                zip.generateAsync({type: 'blob'}).then(function(content) {
                    // Create a download link
                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(content);
                    link.download = 'webpage.zip';
                    link.click();
                });
            } else {
                alert('JSZip library is not available. Please include it in your project.');
            }
        });
    }
}

function setupLivePreview(container, codeBlocks) {
    // Find the iframe
    const iframe = container.querySelector('.live-preview-frame');
    if (!iframe) return;

    // Find the HTML, CSS, and JS code
    let htmlCode = '';
    let cssCode = '';
    let jsCode = '';

    codeBlocks.forEach(block => {
        if (block.language === 'html') {
            htmlCode = block.code;
        } else if (block.language === 'css') {
            cssCode = block.code;
        } else if (block.language === 'javascript') {
            jsCode = block.code;
        }
    });

    // Create a complete HTML document
    const completeHtml = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                ${cssCode}
            </style>
        </head>
        <body>
            ${htmlCode}
            <script>
                ${jsCode}
            </script>
        </body>
        </html>
    `;

    // Set the iframe content
    setTimeout(() => {
        const doc = iframe.contentDocument || iframe.contentWindow.document;
        doc.open();
        doc.write(completeHtml);
        doc.close();
    }, 500);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
