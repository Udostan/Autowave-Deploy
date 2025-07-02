// Task container handlers

document.addEventListener('DOMContentLoaded', function() {
    console.log('Task container handlers loaded!');

    // Add test content to the summary container for testing purposes
    setTimeout(() => {
        const summaryContent = document.querySelector('#summary-container-initial .summary-container-content');
        if (summaryContent && summaryContent.innerHTML.includes('Task results will appear here')) {
            console.log('Adding test content to summary container for button testing');
            summaryContent.innerHTML = `
                <div style="padding: 20px;">
                    <h3>Test Task Summary</h3>
                    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    <p>This is a test summary to verify that the download and share buttons are working correctly.</p>
                    <ul>
                        <li>✅ Download button should create an HTML file</li>
                        <li>✅ Copy button should copy text to clipboard</li>
                        <li>✅ Share button should open share dialog or copy to clipboard</li>
                    </ul>
                    <p><em>You can now test the download, copy, and share buttons above!</em></p>
                </div>
            `;
        }

        // Add direct event listeners to the buttons as a backup
        console.log('Adding direct event listeners to buttons...');
        const copyButtons = document.querySelectorAll('.copy-summary-btn');
        const downloadButtons = document.querySelectorAll('.download-summary-btn');
        const shareButtons = document.querySelectorAll('.share-summary-btn');

        console.log('Found buttons:', {
            copy: copyButtons.length,
            download: downloadButtons.length,
            share: shareButtons.length
        });

        copyButtons.forEach((btn, index) => {
            console.log(`Adding direct listener to copy button ${index}:`, btn);
            btn.addEventListener('click', function(e) {
                console.log('🔥 DIRECT COPY BUTTON CLICKED!', this);
                e.preventDefault();
                e.stopPropagation();

                // Simple copy test
                const testText = `Test copy from Prime Agent - ${new Date().toLocaleString()}`;
                navigator.clipboard.writeText(testText).then(() => {
                    console.log('✅ Direct copy successful!');
                    showToast('✅ Copy button working! Text copied to clipboard.', 'success');
                    this.classList.add('text-green-500');
                    setTimeout(() => {
                        this.classList.remove('text-green-500');
                    }, 1000);
                }).catch(err => {
                    console.error('❌ Direct copy failed:', err);
                    showToast('❌ Copy failed. Please try again.', 'error');
                });
            });
        });
    }, 1000);
    // Close all mobile dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.mobile-menu-btn') && !event.target.closest('.mobile-dropdown')) {
            // Close all dropdowns
            document.querySelectorAll('.mobile-dropdown').forEach(dropdown => {
                dropdown.classList.add('hidden');
            });
        }
    });

    // Event delegation for "Go to summary" buttons and other interactions
    document.body.addEventListener('click', function(event) {
        console.log('Body click detected:', event.target, 'Classes:', event.target.className);

        // Special debug for copy buttons
        if (event.target.closest('.copy-summary-btn')) {
            console.log('🎯 COPY BUTTON AREA CLICKED!');
        }
        // Check if the clicked element is a goto-summary-btn or one of its children
        const button = event.target.closest('.goto-summary-btn');
        if (button) {
            const taskId = button.getAttribute('data-task-id');
            if (taskId) {
                // Find the corresponding summary container
                const summaryContainer = document.getElementById(taskId);
                if (summaryContainer) {
                    // Scroll to the summary container
                    summaryContainer.scrollIntoView({ behavior: 'smooth' });

                    // Highlight the summary container briefly
                    summaryContainer.classList.add('highlight-container');
                    setTimeout(() => {
                        summaryContainer.classList.remove('highlight-container');
                    }, 2000);
                }
            }
        }

        // Check if the clicked element is a download-summary-btn or one of its children
        const downloadBtn = event.target.closest('.download-summary-btn');
        if (downloadBtn) {
            console.log('Download button clicked!', downloadBtn);
            event.preventDefault();
            event.stopPropagation();

            // Show download options menu
            showDownloadOptionsMenu(downloadBtn);
        }

        // Check if the clicked element is a copy-summary-btn or one of its children
        const copyBtn = event.target.closest('.copy-summary-btn');
        if (copyBtn) {
            console.log('🔥 COPY BUTTON CLICKED!', copyBtn);
            console.log('Copy button element:', copyBtn);
            console.log('Copy button classes:', copyBtn.className);
            const taskId = copyBtn.getAttribute('data-task-id');
            console.log('Task ID for copy:', taskId);

            if (taskId) {
                // Find the corresponding summary container
                const summaryContainer = document.getElementById(taskId);
                console.log('Summary container found for copy:', summaryContainer);

                if (summaryContainer) {
                    // Get the content div
                    const contentDiv = summaryContainer.querySelector('.summary-container-content');
                    console.log('Content div found for copy:', contentDiv);

                    if (contentDiv) {
                        // Get the text content - if empty, create a default message
                        let textContent = contentDiv.innerText.trim();
                        if (!textContent || textContent === 'Task results will appear here') {
                            textContent = `Prime Agent Task Summary

Date: ${new Date().toLocaleDateString()}
Time: ${new Date().toLocaleTimeString()}

This is a sample task summary from AutoWave Prime Agent. Your actual task results will appear here when you run a task.

Generated by AutoWave Prime Agent - https://autowave.pro`;
                        }

                        console.log('Text content to copy:', textContent);

                        // Copy to clipboard
                        navigator.clipboard.writeText(textContent)
                            .then(() => {
                                console.log('Text copied to clipboard successfully');

                                // Show success feedback with toast
                                showToast('✅ Content copied to clipboard!', 'success');

                                // Show success feedback on button
                                copyBtn.classList.add('text-green-500');
                                setTimeout(() => {
                                    copyBtn.classList.remove('text-green-500');
                                }, 1000);
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

                                    showToast('✅ Content copied to clipboard!', 'success');

                                    copyBtn.classList.add('text-green-500');
                                    setTimeout(() => {
                                        copyBtn.classList.remove('text-green-500');
                                    }, 1000);
                                } catch (fallbackErr) {
                                    console.error('Fallback copy method also failed:', fallbackErr);
                                    showToast('❌ Failed to copy content. Please try again.', 'error');
                                }
                            });
                    } else {
                        console.error('Content div not found for copy');
                    }
                } else {
                    console.error('Summary container not found for copy');
                }
            } else {
                console.error('Task ID not found for copy');
            }
        }

        // Check if the clicked element is a share-summary-btn or one of its children
        const shareBtn = event.target.closest('.share-summary-btn');
        if (shareBtn) {
            console.log('Share button clicked!', shareBtn);
            const taskId = shareBtn.getAttribute('data-task-id');
            console.log('Task ID for share:', taskId);

            if (taskId) {
                // Find the corresponding summary container
                const summaryContainer = document.getElementById(taskId);
                console.log('Summary container found for share:', summaryContainer);

                if (summaryContainer) {
                    // Get the content div
                    const contentDiv = summaryContainer.querySelector('.summary-container-content');
                    console.log('Content div found for share:', contentDiv);

                    if (contentDiv) {
                        // Get the task title
                        const titleElement = summaryContainer.querySelector('h4');
                        const title = titleElement ? titleElement.textContent.trim().replace('Task Summary: ', '') : 'Prime Agent Task Summary';

                        // Get the text content - if empty, create a default message
                        let textContent = contentDiv.innerText.trim();
                        if (!textContent || textContent === 'Task results will appear here') {
                            textContent = `Prime Agent Task Summary

Date: ${new Date().toLocaleDateString()}
Time: ${new Date().toLocaleTimeString()}

This is a sample task summary from AutoWave Prime Agent. Your actual task results will appear here when you run a task.

Generated by AutoWave Prime Agent - https://autowave.pro`;
                        }

                        // Create share data
                        const shareData = {
                            title: `AutoWave - ${title}`,
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
                                    // Show success feedback
                                    shareBtn.classList.add('text-green-500');
                                    setTimeout(() => {
                                        shareBtn.classList.remove('text-green-500');
                                    }, 1000);
                                })
                                .catch(err => {
                                    console.error('Share failed:', err);
                                    // Fallback to copy to clipboard
                                    fallbackShare(shareData, shareBtn);
                                });
                        } else {
                            console.log('Web Share API not available, using fallback');
                            // Fallback for browsers that don't support sharing
                            fallbackShare(shareData, shareBtn);
                        }
                    } else {
                        console.error('Content div not found for share');
                    }
                } else {
                    console.error('Summary container not found for share');
                }
            } else {
                console.error('Task ID not found for share');
            }
        }

        // Check if the clicked element is a mobile-menu-btn
        const mobileMenuBtn = event.target.closest('.mobile-menu-btn');
        if (mobileMenuBtn) {
            const taskId = mobileMenuBtn.getAttribute('data-task-id');
            if (taskId) {
                // Find the corresponding dropdown
                const dropdown = document.querySelector(`.mobile-dropdown[data-task-id="${taskId}"]`);
                if (dropdown) {
                    // Close all other dropdowns first
                    document.querySelectorAll('.mobile-dropdown').forEach(d => {
                        if (d !== dropdown) {
                            d.classList.add('hidden');
                        }
                    });

                    // Toggle this dropdown
                    dropdown.classList.toggle('hidden');

                    // Prevent the event from bubbling up to document
                    event.stopPropagation();
                }
            }
        }

        // Check if the clicked element is the clear all tasks button
        const clearAllBtn = event.target.closest('#clearAllTasksBtn');
        if (clearAllBtn) {
            // Clear all thinking containers except the initial one
            const thinkingContainers = document.querySelectorAll('.thinking-container:not(#thinking-container-initial)');
            thinkingContainers.forEach(container => {
                container.remove();
            });

            // Clear all summary containers except the initial one
            const summaryContainers = document.querySelectorAll('.summary-container:not(#summary-container-initial)');
            summaryContainers.forEach(container => {
                container.remove();
            });

            // Reset the initial containers
            const initialThinkingContent = document.querySelector('#thinking-container-initial .thinking-process');
            if (initialThinkingContent) {
                initialThinkingContent.innerHTML = '<div class="prose prose-sm max-w-none text-sm text-gray-500"><p class="typing-cursor">Starting analysis and planning process...</p></div>';
            }

            const initialSummaryContent = document.querySelector('#summary-container-initial .summary-container-content');
            if (initialSummaryContent) {
                initialSummaryContent.innerHTML = '<p class="text-center text-gray-500">Task results will appear here</p>';
            }

            // Reset the progress bar and processing indicator
            const progressFill = document.getElementById('progressFill');
            if (progressFill) {
                progressFill.style.width = '0%';
            }

            const processingIndicator = document.getElementById('processingIndicator');
            if (processingIndicator) {
                processingIndicator.classList.remove('completed');
            }

            const stepDescription = document.getElementById('stepDescription');
            if (stepDescription) {
                stepDescription.textContent = 'Analyzing your request and preparing execution plan';
            }
        }
    });

    // Fallback share function
    function fallbackShare(shareData, button) {
        console.log('Using fallback share method');

        // Create a formatted text with title and content
        const formattedText = `${shareData.title}

${shareData.text}

---
Shared from AutoWave Prime Agent: ${shareData.url}`;

        console.log('Formatted text for sharing:', formattedText);

        // Copy to clipboard
        navigator.clipboard.writeText(formattedText)
            .then(() => {
                console.log('Text copied to clipboard successfully');

                // Show success message with better styling
                showToast('✅ Content copied to clipboard! You can now paste it anywhere to share.', 'success');

                // Show success feedback on button
                button.classList.add('text-green-500');
                setTimeout(() => {
                    button.classList.remove('text-green-500');
                }, 1000);
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

                    showToast('✅ Content copied to clipboard! You can now paste it anywhere to share.', 'success');

                    button.classList.add('text-green-500');
                    setTimeout(() => {
                        button.classList.remove('text-green-500');
                    }, 1000);
                } catch (fallbackErr) {
                    console.error('Fallback copy method also failed:', fallbackErr);
                    showToast('❌ Failed to copy content. Please try again.', 'error');
                }
            });
    }

    // Show download options menu
    function showDownloadOptionsMenu(downloadBtn) {
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
        const buttonRect = downloadBtn.getBoundingClientRect();
        downloadBtn.style.position = 'relative';
        downloadBtn.appendChild(menu);

        // Add event listeners for menu options
        menu.querySelector('.download-html-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            downloadAsHTML(taskId);
            menu.remove();
        });

        menu.querySelector('.download-pdf-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            downloadAsPDF(taskId);
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

    // Download as HTML function
    function downloadAsHTML(taskId) {
        console.log('Downloading as HTML for task:', taskId);

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
        if (!htmlContent || htmlContent === '<p class="text-center text-gray-500">Task results will appear here</p>') {
            htmlContent = `
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Prime Agent Task Summary</h2>
                    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    <p>This is a sample task summary. Your actual task results will appear here when you run a task.</p>
                    <hr>
                    <p><em>Generated by AutoWave Prime Agent</em></p>
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
    <title>Prime Agent Task Summary</title>
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
        <h1>AutoWave Prime Agent - Task Summary</h1>
        <p>Generated on: ${new Date().toLocaleString()}</p>
    </div>
    <div class="content">
        ${htmlContent}
    </div>
    <div class="footer">
        <p>Generated by AutoWave Prime Agent | <a href="https://autowave.pro">autowave.pro</a></p>
    </div>
</body>
</html>`;

        const blob = new Blob([fullHtmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);

        // Get the task title
        const titleElement = summaryContainer.querySelector('h4');
        const title = titleElement ? titleElement.textContent.trim().replace('Task Summary: ', '') : 'task_summary';

        // Create a temporary link and trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = title.substring(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase() + '_' + new Date().toISOString().slice(0, 10) + '.html';
        document.body.appendChild(a);
        a.click();

        // Clean up
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);

        showToast('✅ HTML file downloaded successfully!', 'success');
        console.log('HTML download completed successfully!');
    }

    // Download as PDF function
    function downloadAsPDF(taskId) {
        console.log('Downloading as PDF for task:', taskId);

        const summaryContainer = document.getElementById(taskId);
        if (!summaryContainer) {
            console.error('Summary container not found');
            showToast('❌ Error: Content not found', 'error');
            return;
        }

        const contentDiv = summaryContainer.querySelector('.summary-container-content');
        if (!contentDiv) {
            console.error('Content div not found');
            showToast('❌ Error: Content not found', 'error');
            return;
        }

        // Check if html2pdf is available
        if (typeof html2pdf === 'undefined') {
            console.error('html2pdf library not loaded');
            showToast('❌ PDF generation library not available', 'error');
            return;
        }

        // Get the content - if empty, create a default message
        let htmlContent = contentDiv.innerHTML.trim();
        if (!htmlContent || htmlContent === '<p class="text-center text-gray-500">Task results will appear here</p>') {
            htmlContent = `
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Prime Agent Task Summary</h2>
                    <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleTimeString()}</p>
                    <p>This is a sample task summary. Your actual task results will appear here when you run a task.</p>
                    <hr>
                    <p><em>Generated by AutoWave Prime Agent</em></p>
                </div>
            `;
        }

        // Get the task title
        const titleElement = summaryContainer.querySelector('h4');
        const title = titleElement ? titleElement.textContent.trim().replace('Task Summary: ', '') : 'task_summary';
        const filename = title.substring(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase() + '_' + new Date().toISOString().slice(0, 10) + '.pdf';

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
                <h1 style="color: #333; margin: 0 0 10px 0; font-size: 24px;">AutoWave Prime Agent - Task Summary</h1>
                <p style="margin: 0; color: #666;">Generated on: ${new Date().toLocaleString()}</p>
            </div>
            <div style="margin-bottom: 30px;">
                ${htmlContent}
            </div>
            <div style="border-top: 2px solid #eee; padding-top: 20px; margin-top: 20px; color: #666; font-size: 10px;">
                <p style="margin: 0;">Generated by AutoWave Prime Agent | autowave.pro</p>
            </div>
        `;

        document.body.appendChild(pdfContainer);

        // Show loading toast
        showToast('📄 Generating PDF...', 'info');

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
            showToast('✅ PDF downloaded successfully!', 'success');

            // Clean up
            document.body.removeChild(pdfContainer);
        }).catch((error) => {
            console.error('PDF generation failed:', error);
            showToast('❌ PDF generation failed. Please try again.', 'error');

            // Clean up
            if (document.body.contains(pdfContainer)) {
                document.body.removeChild(pdfContainer);
            }
        });
    }

    // Toast notification function
    function showToast(message, type = 'info') {
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
});

// Add CSS class for mobile responsiveness
const addResponsiveStyles = () => {
    // Check if we've already added the style element
    if (!document.getElementById('responsive-styles')) {
        const style = document.createElement('style');
        style.id = 'responsive-styles';
        style.textContent = `
            @media (max-width: 768px) {
                .summary-container-header {
                    flex-wrap: wrap;
                }
                .summary-container-header h3 {
                    font-size: 0.95rem;
                    margin-bottom: 0.5rem;
                    width: 100%;
                }
            }
        `;
        document.head.appendChild(style);
    }
};

// Call the function to add responsive styles
addResponsiveStyles();
