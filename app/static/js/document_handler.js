/**
 * Document Handler
 * Handles document display and interactions in the task summary
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the document handler
    initDocumentHandler();
});

function initDocumentHandler() {
    // Listen for task summary updates
    document.addEventListener('taskSummaryUpdated', function(event) {
        enhanceDocumentDisplay();
    });
}

/**
 * Enhance document display in task summaries
 */
function enhanceDocumentDisplay() {
    // Get all summary containers
    const summaryContainers = document.querySelectorAll('.summary-container-content, .task-summary');
    
    summaryContainers.forEach(container => {
        // Check if this contains a document
        if (isDocumentResult(container)) {
            transformDocumentDisplay(container);
        }
    });
}

/**
 * Check if the container contains a document result
 */
function isDocumentResult(container) {
    const content = container.innerHTML;
    
    // Check for document type indicators
    return content.includes('(Report)') || 
           content.includes('(Essay)') || 
           content.includes('(Legal)') || 
           content.includes('(Business)') || 
           content.includes('(Academic)') || 
           content.includes('(Letter)');
}

/**
 * Transform document display with enhanced UI
 */
function transformDocumentDisplay(container) {
    // Parse the document content
    const content = container.innerHTML;
    
    // Extract document title and type
    const titleMatch = content.match(/<h1[^>]*>([^<(]+)(\([^)]+\))<\/h1>/);
    if (!titleMatch) return;
    
    const title = titleMatch[1].trim();
    const type = titleMatch[2].replace(/[()]/g, '').trim();
    
    // Extract document content
    let documentContent = '';
    let analysisContent = '';
    
    // Check if there's an analysis section
    if (content.includes('<h2>Document Analysis</h2>')) {
        const parts = content.split('<h2>Document Analysis</h2>');
        documentContent = parts[0].replace(/<h1[^>]*>[^<]+<\/h1>/, '').trim();
        analysisContent = '<h2>Document Analysis</h2>' + parts[1];
    } else {
        documentContent = content.replace(/<h1[^>]*>[^<]+<\/h1>/, '').trim();
    }
    
    // Extract preview image if available
    let previewImage = '';
    const imageMatch = content.match(/<img src="([^"]+)" alt="[^"]*PDF Preview[^"]*">/);
    if (imageMatch) {
        previewImage = imageMatch[1];
    }
    
    // Extract PDF download link if available
    let pdfDownloadLink = '';
    const pdfMatch = content.match(/\[Download PDF\]\((data:application\/pdf;base64,[^)]+)\)/);
    if (pdfMatch) {
        pdfDownloadLink = pdfMatch[1];
    }
    
    // Create enhanced document display
    const enhancedDisplay = createDocumentDisplay(
        title, 
        type, 
        documentContent, 
        analysisContent, 
        previewImage, 
        pdfDownloadLink
    );
    
    // Replace the container content
    container.innerHTML = enhancedDisplay;
    
    // Add event listeners for document actions
    addDocumentEventListeners(container);
}

/**
 * Create enhanced document display
 */
function createDocumentDisplay(title, type, documentContent, analysisContent, previewImage, pdfDownloadLink) {
    // Create document container
    let html = `
        <div class="document-container">
            <div class="document-header">
                <h2 class="document-title">${title}</h2>
                <span class="document-type-badge">${type}</span>
            </div>
            <div class="document-content">
                ${documentContent}
            </div>
    `;
    
    // Add preview if available
    if (previewImage) {
        html += `
            <div class="document-preview">
                <img src="${previewImage}" alt="${title} Preview">
            </div>
        `;
    }
    
    // Add document actions
    html += `
        <div class="document-actions">
    `;
    
    // Add PDF download button if available
    if (pdfDownloadLink) {
        html += `
            <a href="${pdfDownloadLink}" download="${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.pdf" class="document-action-button">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Download PDF
            </a>
        `;
    }
    
    // Add copy button
    html += `
            <button class="document-action-button document-copy-btn">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Copy Text
            </button>
        </div>
    `;
    
    // Add analysis section if available
    if (analysisContent) {
        // Extract metrics
        const wordCountMatch = analysisContent.match(/Word Count: ([0-9,]+)/);
        const readabilityMatch = analysisContent.match(/Readability: ([^<\n]+)/);
        
        // Extract suggestions
        const suggestionsMatch = analysisContent.match(/<h3>Improvement Suggestions<\/h3>([^<]+(?:<[^>]+>[^<]+)*)/);
        
        html += `
            <div class="document-analysis">
                <h3>Document Analysis</h3>
                <div class="document-metrics">
        `;
        
        if (wordCountMatch) {
            html += `
                    <div class="document-metric">
                        <div class="document-metric-label">Word Count</div>
                        <div class="document-metric-value">${wordCountMatch[1]}</div>
                    </div>
            `;
        }
        
        if (readabilityMatch) {
            html += `
                    <div class="document-metric">
                        <div class="document-metric-label">Readability</div>
                        <div class="document-metric-value">${readabilityMatch[1]}</div>
                    </div>
            `;
        }
        
        html += `
                </div>
        `;
        
        if (suggestionsMatch) {
            const suggestions = suggestionsMatch[1].trim().split('\n').map(s => s.replace(/^- /, '').trim());
            
            html += `
                <h3>Improvement Suggestions</h3>
                <div class="document-suggestions">
            `;
            
            suggestions.forEach(suggestion => {
                if (suggestion.trim()) {
                    html += `<div class="document-suggestion">${suggestion}</div>`;
                }
            });
            
            html += `
                </div>
            `;
        }
        
        html += `
            </div>
        `;
    }
    
    html += `
        </div>
    `;
    
    return html;
}

/**
 * Add event listeners for document actions
 */
function addDocumentEventListeners(container) {
    // Add copy button event listener
    const copyBtn = container.querySelector('.document-copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', function() {
            const documentContent = container.querySelector('.document-content');
            if (documentContent) {
                // Copy text to clipboard
                const text = documentContent.innerText;
                navigator.clipboard.writeText(text).then(
                    function() {
                        // Show success message
                        const originalText = copyBtn.innerHTML;
                        copyBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>Copied!';
                        
                        // Reset button after 2 seconds
                        setTimeout(function() {
                            copyBtn.innerHTML = originalText;
                        }, 2000);
                    },
                    function(err) {
                        console.error('Could not copy text: ', err);
                    }
                );
            }
        });
    }
}
