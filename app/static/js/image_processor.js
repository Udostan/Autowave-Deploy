/**
 * Image Processor for Task Summary
 * This file handles image processing in the task summary to display images without containers
 */

document.addEventListener('DOMContentLoaded', function() {
    // First, remove all existing captions
    setTimeout(removeAllCaptions, 500);

    // Initialize the image processor
    initImageProcessor();

    // Also check periodically for new images
    setInterval(checkForImages, 1000);

    // And periodically remove captions
    setInterval(removeAllCaptions, 2000);
});

// Function to remove all captions
function removeAllCaptions() {
    console.log('Removing all image captions');
    const captions = document.querySelectorAll('.image-caption');
    console.log(`Found ${captions.length} captions to remove`);

    captions.forEach(caption => {
        if (caption.parentNode) {
            caption.parentNode.removeChild(caption);
        }
    });
}

function initImageProcessor() {
    // Add a mutation observer to detect new task summaries
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                checkForImages();
            }
        });
    });

    // Start observing the document body for changes
    observer.observe(document.body, { childList: true, subtree: true });
}

function checkForImages() {
    // Get all summary containers
    const summaryContainers = document.querySelectorAll('.summary-container-content');

    summaryContainers.forEach(container => {
        // Process all images in the container
        processImagesInContainer(container);
    });

    // Also check the task results div (for compatibility with different UI versions)
    const taskResults = document.getElementById('taskResults');
    if (taskResults) {
        processImagesInContainer(taskResults);
    }
}

function processImagesInContainer(container) {
    // Process all image containers
    const imageContainers = container.querySelectorAll('.image-container');
    console.log(`Found ${imageContainers.length} image containers to process in image_processor.js`);

    // Keep track of processed images to avoid duplicates
    const processedImages = new Set();

    imageContainers.forEach(imgContainer => {
        // Get the image and caption
        const img = imgContainer.querySelector('img');
        const caption = imgContainer.querySelector('.image-caption');

        if (img) {
            // Skip if already processed
            if (img.hasAttribute('data-processed-by-image-processor')) {
                return;
            }

            // Mark as processed
            img.setAttribute('data-processed-by-image-processor', 'true');

            // Add to processed set if it has a src
            if (img.src) {
                processedImages.add(img.src);
            }

            // Style the image directly
            img.style.maxWidth = '100%';
            img.style.height = 'auto';
            img.style.borderRadius = '0.5rem';
            img.style.margin = '1.5rem auto';
            img.style.display = 'block';
            img.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
            img.style.objectFit = 'contain';
            img.setAttribute('loading', 'lazy');

            // Insert the image before the container
            imgContainer.parentNode.insertBefore(img, imgContainer);

            // Don't add captions at all - just skip this part
            console.log('Skipping caption insertion for image container');

            // Remove the now-empty container
            imgContainer.parentNode.removeChild(imgContainer);
        }
    });

    // Process standalone images (not in containers)
    const standaloneImages = Array.from(container.querySelectorAll('img'))
        .filter(img => !img.closest('.image-container'));

    console.log(`Found ${standaloneImages.length} standalone images to process in image_processor.js`);

    standaloneImages.forEach(img => {
        // Skip if already processed
        if (img.hasAttribute('data-processed-by-image-processor')) {
            return;
        }

        // Mark as processed
        img.setAttribute('data-processed-by-image-processor', 'true');

        // Style the image directly
        img.style.maxWidth = '100%';
        img.style.height = 'auto';
        img.style.borderRadius = '0.5rem';
        img.style.margin = '1.5rem auto';
        img.style.display = 'block';
        img.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.1)';
        img.style.objectFit = 'contain';
        img.setAttribute('loading', 'lazy');

        // Don't add captions at all - just skip this part
        console.log('Skipping caption insertion for standalone image');
    });

    // Process image placeholders [IMAGE: description]
    processImagePlaceholders(container);
}

function processImagePlaceholders(container) {
    // Get the HTML content
    const content = container.innerHTML;

    // Check if there are image placeholders
    if (!content.includes('[IMAGE:')) {
        return;
    }

    console.log('Processing image placeholders in image_processor.js');

    // Create a temporary div to hold the content
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = content;

    // Find all text nodes
    const textNodes = [];
    const walker = document.createTreeWalker(
        tempDiv,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.includes('[IMAGE:')) {
            textNodes.push(node);
        }
    }

    // Process each text node
    textNodes.forEach(textNode => {
        const text = textNode.textContent;
        const regex = /\[IMAGE:\s*(.*?)\]/g;
        let match;
        let lastIndex = 0;
        const fragments = [];

        while ((match = regex.exec(text)) !== null) {
            // Add the text before the match
            if (match.index > lastIndex) {
                fragments.push(document.createTextNode(text.substring(lastIndex, match.index)));
            }

            // Create the image placeholder
            const description = match[1].trim();
            const placeholderId = `img-placeholder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

            const placeholder = document.createElement('div');
            placeholder.id = placeholderId;
            placeholder.style.margin = '1.5rem auto';
            placeholder.style.textAlign = 'center';
            placeholder.setAttribute('data-processed-by-image-processor', 'true');

            const spinner = document.createElement('div');
            spinner.className = 'loading-spinner';
            spinner.style.margin = '2rem auto';
            placeholder.appendChild(spinner);

            // Don't add a caption here - it will be added by searchAndInsertImageWithoutContainer

            fragments.push(placeholder);

            // Queue the image search
            setTimeout(() => {
                searchAndInsertImageWithoutContainer(description, placeholderId);
            }, 500);

            lastIndex = match.index + match[0].length;
        }

        // Add the remaining text
        if (lastIndex < text.length) {
            fragments.push(document.createTextNode(text.substring(lastIndex)));
        }

        // Replace the text node with the fragments
        const parent = textNode.parentNode;
        fragments.forEach(fragment => {
            parent.insertBefore(fragment, textNode);
        });
        parent.removeChild(textNode);
    });

    // Update the container content
    container.innerHTML = tempDiv.innerHTML;
}

// This function should be defined in your main JavaScript file
function searchAndInsertImageWithoutContainer(description, placeholderId) {
    // This is a placeholder function that should be implemented in your main JS file
    console.log(`Searching for image: ${description} for placeholder: ${placeholderId}`);
}
