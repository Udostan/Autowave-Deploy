// Modal Handlers
console.log('Modal handlers script loaded');

// Execute immediately and also on DOMContentLoaded
function initializeModalHandlers() {
    console.log('Initializing modal handlers');

    // Get modal elements
    const summaryModal = document.getElementById('summaryModal');
    const modalTaskResults = document.getElementById('modalTaskResults');
    const closeModalBtn = document.getElementById('closeSummaryModal');
    const expandSummaryBtn = document.getElementById('expandSummaryBtn');

    console.log('Modal elements:', {
        summaryModal: summaryModal ? 'Found' : 'Not found',
        modalTaskResults: modalTaskResults ? 'Found' : 'Not found',
        closeModalBtn: closeModalBtn ? 'Found' : 'Not found',
        expandSummaryBtn: expandSummaryBtn ? 'Found' : 'Not found'
    });

    // Function to fix any white backgrounds in the modal content
    function fixModalContentStyles(content) {
        // Replace any white backgrounds with transparent or dark backgrounds
        let fixedContent = content
            .replace(/background-color:\s*white/gi, 'background-color: #111827')
            .replace(/background-color:\s*#fff/gi, 'background-color: #111827')
            .replace(/background-color:\s*#ffffff/gi, 'background-color: #111827')
            .replace(/background-color:\s*rgb\(255,\s*255,\s*255\)/gi, 'background-color: #111827')
            .replace(/background:\s*white/gi, 'background: #111827')
            .replace(/background:\s*#fff/gi, 'background: #111827')
            .replace(/background:\s*#ffffff/gi, 'background: #111827')
            .replace(/background:\s*rgb\(255,\s*255,\s*255\)/gi, 'background: #111827')
            .replace(/color:\s*black/gi, 'color: #e5e7eb')
            .replace(/color:\s*#000/gi, 'color: #e5e7eb')
            .replace(/color:\s*#000000/gi, 'color: #e5e7eb')
            .replace(/color:\s*rgb\(0,\s*0,\s*0\)/gi, 'color: #e5e7eb');

        // Add a wrapper with dark background to ensure no white shows through
        fixedContent = `<div style="background-color: #111827 !important; padding: 0;">${fixedContent}</div>`;

        return fixedContent;
    }

    // Function to open the modal with content
    function openSummaryModal(content) {
        if (!summaryModal || !modalTaskResults) {
            console.error('Modal elements not found');
            return;
        }

        console.log('Opening modal with content');

        // Fix any white backgrounds in the content
        const fixedContent = fixModalContentStyles(content);

        // Set the content
        const taskSummaryElement = modalTaskResults.querySelector('.task-summary');
        if (taskSummaryElement) {
            taskSummaryElement.innerHTML = fixedContent;

            // Apply dark mode styles to all elements in the modal
            const allElements = taskSummaryElement.querySelectorAll('*');
            allElements.forEach(element => {
                // Force dark background on all elements except section headers
                if (!element.closest('.section-header')) {
                    element.style.backgroundColor = '#111827';
                }

                // Check if the element has inline styles with white background or black text
                if (element.style.backgroundColor === 'white' ||
                    element.style.backgroundColor === '#fff' ||
                    element.style.backgroundColor === '#ffffff' ||
                    element.style.backgroundColor === 'rgb(255, 255, 255)') {
                    element.style.backgroundColor = '#111827';
                }

                if (element.style.color === 'black' ||
                    element.style.color === '#000' ||
                    element.style.color === '#000000' ||
                    element.style.color === 'rgb(0, 0, 0)') {
                    element.style.color = '#e5e7eb';
                }

                // Remove any background images that might be white
                if (element.style.backgroundImage) {
                    element.style.backgroundImage = 'none';
                }

                // Check for computed style as well
                const computedStyle = window.getComputedStyle(element);
                if (computedStyle.backgroundColor === 'rgb(255, 255, 255)' && !element.closest('.section-header')) {
                    element.style.backgroundColor = '#111827';
                }
            });

            // Add a specific fix for any remaining white backgrounds
            setTimeout(() => {
                const whiteElements = taskSummaryElement.querySelectorAll('[style*="background-color: white"], [style*="background-color:#fff"], [style*="background-color: #ffffff"], [style*="background: white"], [style*="background:#fff"], [style*="background: #ffffff"]');
                whiteElements.forEach(element => {
                    if (!element.closest('.section-header')) {
                        element.style.backgroundColor = '#111827';
                        element.style.background = '#111827';
                    }
                });

                // Specifically target links and paragraphs that might have white backgrounds
                const textElements = taskSummaryElement.querySelectorAll('p, a, span, li, div');
                textElements.forEach(element => {
                    if (!element.closest('.section-header')) {
                        element.style.backgroundColor = '#111827';
                        element.style.background = '#111827';
                    }
                });
            }, 100);
        } else {
            console.error('Task summary element not found in modal');
        }

        // Show the modal
        summaryModal.classList.remove('hidden');

        // Prevent scrolling on the body
        document.body.style.overflow = 'hidden';
    }

    // Function to close the modal
    function closeModal() {
        if (!summaryModal) {
            console.error('Modal element not found');
            return;
        }

        console.log('Closing modal');

        // Hide the modal
        summaryModal.classList.add('hidden');

        // Allow scrolling on the body
        document.body.style.overflow = '';
    }

    // Add event listener to expand button
    if (expandSummaryBtn) {
        console.log('Adding click event listener to expand button');
        expandSummaryBtn.addEventListener('click', function() {
            console.log('Expand button clicked');

            // Get the current summary content
            const summaryContainers = document.getElementById('summaryContainers');
            if (!summaryContainers) {
                console.error('Summary containers element not found');
                return;
            }

            // Get all summary containers
            const containers = summaryContainers.querySelectorAll('.summary-container');
            if (!containers.length) {
                console.error('No summary containers found');
                return;
            }

            console.log('Found', containers.length, 'summary containers');

            // Get the content from all summary containers
            let allContent = '';
            containers.forEach(container => {
                const header = container.querySelector('h4');
                const content = container.querySelector('.summary-container-content');

                if (header && content) {
                    allContent += `<div class="dark-summary-section">
                        <div class="section-header">
                            <h2>${header.textContent}</h2>
                        </div>
                        <div class="section-content">
                            <div class="dark-summary-content">${content.innerHTML}</div>
                        </div>
                    </div>`;
                }
            });

            // Open the modal with the content
            openSummaryModal(allContent);
        });
    } else {
        console.error('Expand button not found');
    }

    // Add event listener to close button
    if (closeModalBtn) {
        console.log('Adding click event listener to close button');
        closeModalBtn.addEventListener('click', function() {
            closeModal();
        });
    } else {
        console.error('Close button not found');
    }

    // Close modal when clicking outside the content
    if (summaryModal) {
        summaryModal.addEventListener('click', function(e) {
            if (e.target === summaryModal) {
                closeModal();
            }
        });
    }

    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && summaryModal && !summaryModal.classList.contains('hidden')) {
            closeModal();
        }
    });
}

// Call the function immediately
initializeModalHandlers();

// Also call it when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeModalHandlers);

// Add a fallback for when the script loads after DOMContentLoaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document already loaded, initializing modal handlers now');
    setTimeout(initializeModalHandlers, 100);
}
