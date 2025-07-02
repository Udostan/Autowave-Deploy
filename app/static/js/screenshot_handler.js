/**
 * Screenshot Handler
 * This file handles the display and interaction with screenshots in the task summary
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the screenshot handler
    initScreenshotHandler();

    // Also check periodically for new screenshots
    setInterval(checkForScreenshots, 1000);
});

function initScreenshotHandler() {
    console.log('Initializing screenshot handler');

    // Add a mutation observer to detect new task summaries
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                checkForScreenshots();
            }
        });
    });

    // Start observing the document body for changes
    observer.observe(document.body, { childList: true, subtree: true });
}

function checkForScreenshots() {
    // Look for screenshot elements in the task summary
    const screenshotElements = document.querySelectorAll('img[src^="data:image/png;base64,"]');

    if (screenshotElements.length > 0) {
        console.log(`Found ${screenshotElements.length} screenshot elements to process`);

        screenshotElements.forEach(processScreenshot);
    }

    // Also check for screenshot buttons
    const screenshotButtons = document.querySelectorAll('.screenshot-zoom-btn, .screenshot-download-btn');

    if (screenshotButtons.length > 0) {
        console.log(`Found ${screenshotButtons.length} screenshot buttons to process`);

        screenshotButtons.forEach(attachButtonHandlers);
    }
}

function processScreenshot(imgElement) {
    // Skip if already processed
    if (imgElement.hasAttribute('data-screenshot-processed')) {
        return;
    }

    console.log('Processing screenshot:', imgElement);

    // Mark as processed
    imgElement.setAttribute('data-screenshot-processed', 'true');
    imgElement.setAttribute('data-processed-by-image-processor', 'true');

    // Get the parent container
    const container = imgElement.closest('.bg-white.rounded-lg.shadow-md.overflow-hidden.border.border-gray-200');

    if (!container) {
        console.log('No container found for screenshot, creating a new one');

        // Create a new container
        const newContainer = document.createElement('div');
        newContainer.className = 'screenshot-container';

        // Create header
        const header = document.createElement('div');
        header.className = 'screenshot-header';

        // Create title
        const title = document.createElement('div');
        title.className = 'screenshot-title';
        title.textContent = imgElement.alt || 'Screenshot';
        header.appendChild(title);

        // Add header to container
        newContainer.appendChild(header);

        // Create image container
        const imageContainer = document.createElement('div');
        imageContainer.className = 'screenshot-image-container';

        // Style the image
        imgElement.className = 'screenshot-image';

        // Move the image to the new container
        if (imgElement.parentNode) {
            // Check if there's a caption after the image
            let caption = imgElement.nextElementSibling;
            if (caption && caption.classList.contains('image-caption')) {
                // Remove the caption to avoid duplication
                caption.parentNode.removeChild(caption);
            }

            imgElement.parentNode.removeChild(imgElement);
        }

        imageContainer.appendChild(imgElement);
        newContainer.appendChild(imageContainer);

        // Create footer with buttons
        const footer = document.createElement('div');
        footer.className = 'screenshot-footer';

        // Create zoom button
        const zoomBtn = document.createElement('button');
        zoomBtn.className = 'screenshot-btn screenshot-zoom-btn';
        zoomBtn.innerHTML = '<i class="fas fa-search-plus"></i> Zoom';
        zoomBtn.setAttribute('data-screenshot', imgElement.src.split(',')[1]); // Extract base64 data
        zoomBtn.setAttribute('data-title', imgElement.alt || 'Screenshot');
        footer.appendChild(zoomBtn);

        // Create download button
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'screenshot-btn screenshot-download-btn';
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download';
        downloadBtn.setAttribute('data-screenshot', imgElement.src.split(',')[1]); // Extract base64 data
        downloadBtn.setAttribute('data-title', imgElement.alt || 'Screenshot');
        footer.appendChild(downloadBtn);

        // Add footer to container
        newContainer.appendChild(footer);

        // Insert the new container where the image was
        const summaryContainer = document.querySelector('.summary-container-content');
        if (summaryContainer) {
            summaryContainer.appendChild(newContainer);
        } else {
            // Fallback to inserting after the image's original parent
            const parent = imgElement.parentNode || document.body;
            parent.appendChild(newContainer);
        }

        // Attach event handlers to buttons
        attachButtonHandlers(zoomBtn);
        attachButtonHandlers(downloadBtn);
    } else {
        console.log('Found container for screenshot, styling it');

        // Check if there are any captions outside the container
        const nextElement = container.nextElementSibling;
        if (nextElement && nextElement.classList.contains('image-caption')) {
            // Remove the caption to avoid duplication
            nextElement.parentNode.removeChild(nextElement);
        }

        // Style the existing container
        container.className = 'screenshot-container';

        // Find and style the header
        const header = container.querySelector('.p-4');
        if (header) {
            header.className = 'screenshot-header';

            // Find and style the title
            const title = header.querySelector('h3');
            if (title) {
                title.className = 'screenshot-title';
            }

            // Find and style the URL
            const url = header.querySelector('p');
            if (url) {
                url.className = 'screenshot-url';
            }
        }

        // Find and style the image container
        const imageContainer = container.querySelector('.border-t.border-gray-200');
        if (imageContainer) {
            imageContainer.className = 'screenshot-image-container';
        }

        // Style the image
        imgElement.className = 'screenshot-image';

        // Find and style the footer
        const footer = container.querySelector('.p-3.bg-gray-50.border-t.border-gray-200.flex.justify-end');
        if (footer) {
            footer.className = 'screenshot-footer';

            // Find and style the buttons
            const buttons = footer.querySelectorAll('button');
            buttons.forEach(button => {
                button.className = 'screenshot-btn ' + (button.classList.contains('screenshot-zoom-btn') ? 'screenshot-zoom-btn' : 'screenshot-download-btn');

                // Attach event handlers
                attachButtonHandlers(button);
            });
        }
    }
}

function attachButtonHandlers(button) {
    // Skip if already processed
    if (button.hasAttribute('data-handler-attached')) {
        return;
    }

    console.log('Attaching handler to button:', button);

    // Mark as processed
    button.setAttribute('data-handler-attached', 'true');

    // Add event listener based on button type
    if (button.classList.contains('screenshot-zoom-btn')) {
        button.addEventListener('click', handleZoomClick);
    } else if (button.classList.contains('screenshot-download-btn')) {
        button.addEventListener('click', handleDownloadClick);
    }
}

function handleZoomClick() {
    console.log('Zoom button clicked');

    // Get screenshot data
    const screenshot = this.getAttribute('data-screenshot');
    const title = this.getAttribute('data-title');

    if (!screenshot) {
        console.error('No screenshot data found');
        return;
    }

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'screenshot-modal';

    modal.innerHTML = `
        <div class="screenshot-modal-content">
            <div class="screenshot-modal-close">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 18L18 6M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="screenshot-modal-image-container">
                <img src="data:image/png;base64,${screenshot}" alt="${title}" class="screenshot-modal-image">
            </div>
        </div>
    `;

    // Add to document
    document.body.appendChild(modal);

    // Add event listener to close button
    modal.querySelector('.screenshot-modal-close').addEventListener('click', function() {
        document.body.removeChild(modal);
    });

    // Close when clicking outside the image
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

function handleDownloadClick() {
    console.log('Download button clicked');

    // Get screenshot data
    const screenshot = this.getAttribute('data-screenshot');
    const title = this.getAttribute('data-title') || 'screenshot';

    if (!screenshot) {
        console.error('No screenshot data found');
        return;
    }

    // Create download link
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${screenshot}`;
    link.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${new Date().toISOString().slice(0, 10)}.png`;

    // Trigger download
    document.body.appendChild(link);
    link.click();

    // Clean up
    setTimeout(() => {
        document.body.removeChild(link);
    }, 100);
}
