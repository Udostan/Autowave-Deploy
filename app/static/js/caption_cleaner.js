/**
 * Caption Cleaner
 * This file handles cleaning up duplicate captions by removing duplicates based on text content
 */

document.addEventListener('DOMContentLoaded', function() {
    // Run the cleanup after a short delay
    setTimeout(removeDuplicateCaptions, 1000);

    // Also run periodically to catch any new captions
    setInterval(removeDuplicateCaptions, 3000);
});

/**
 * Simple function to remove duplicate captions based on their text content
 */
function removeDuplicateCaptions() {
    console.log('Running caption cleanup');

    // Get all image captions
    const captions = document.querySelectorAll('.image-caption');
    console.log(`Found ${captions.length} captions`);

    // Keep track of which captions we've seen
    const seenCaptions = new Set();

    // For each caption
    captions.forEach(caption => {
        // Get the caption text
        const text = caption.textContent.trim();

        // If we've seen this caption before, remove it
        if (seenCaptions.has(text)) {
            console.log(`Removing duplicate caption: ${text}`);
            caption.parentNode.removeChild(caption);
        } else {
            // Otherwise, mark it as seen
            seenCaptions.add(text);
        }
    });
}
