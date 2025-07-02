/**
 * Markdown Processor for Super Agent
 * This file contains functions to properly process Markdown content
 */

// Initialize markdown-it with proper options
function initializeMarkdownIt() {
    return window.markdownit({
        html: true,  // Enable HTML tags in source
        breaks: true,  // Convert '\n' in paragraphs into <br>
        linkify: true,  // Autoconvert URL-like text to links
        typographer: true  // Enable some language-neutral replacement + quotes beautification
    });
}

// Process Markdown content before rendering
function processMarkdownHeadings(markdownText) {
    if (!markdownText) return '';

    // Instead of replacing markdown with HTML, we'll just add special handling for the Sources section
    // This allows markdown-it to properly process all the markdown syntax
    let processedText = markdownText;

    // Special handling for Sources section - add an ID to the heading
    processedText = processedText.replace(/^## Sources$/gm, '## Sources {#sources-heading}');

    // Ensure proper spacing between paragraphs
    // Replace single newlines between paragraphs with double newlines
    processedText = processedText.replace(/([^\n])\n([^\n])/g, '$1\n\n$2');

    // Ensure proper spacing after lists before paragraphs
    processedText = processedText.replace(/(\n[*-] .+)\n([^*\n-])/g, '$1\n\n$2');
    processedText = processedText.replace(/(\n\d+\. .+)\n([^\d\n])/g, '$1\n\n$2');

    // Ensure proper spacing after headings
    processedText = processedText.replace(/(#{1,6} .+)\n([^#\n])/g, '$1\n\n$2');

    return processedText;
}

// Process HTML to fix image containers
function fixImageContainers(html) {
    if (!html) return '';

    // First, check if the HTML contains any image containers
    if (!html.includes('<div class="image-container"') &&
        !html.includes('<img src=') &&
        !html.includes('style="max-width:100%"')) {
        return html; // No image containers to fix
    }

    // Create a temporary DOM element to parse the HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // Process all nodes recursively to find text nodes with HTML
    const processNode = (node) => {
        // If this is a text node, check if it contains HTML
        if (node.nodeType === Node.TEXT_NODE) {
            const text = node.textContent.trim();
            if (text.includes('<div class="image-container"') ||
                (text.includes('<img src=') && text.includes('style="max-width:100%"'))) {

                // Parse the text as HTML
                const tempDoc = parser.parseFromString(text, 'text/html');

                // Replace the text node with the parsed HTML nodes
                const fragment = document.createDocumentFragment();
                Array.from(tempDoc.body.childNodes).forEach(childNode => {
                    fragment.appendChild(childNode.cloneNode(true));
                });

                if (node.parentNode) {
                    node.parentNode.replaceChild(fragment, node);
                }

                return true; // Node was replaced
            }
        }
        // If this is an element node, process its children
        else if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if this element's innerHTML contains image HTML
            if (node.innerHTML.includes('<div class="image-container"') ||
                (node.innerHTML.includes('<img src=') && node.innerHTML.includes('style="max-width:100%"'))) {

                // Process all child nodes
                const childNodes = Array.from(node.childNodes);
                let nodeReplaced = false;

                for (let i = 0; i < childNodes.length; i++) {
                    const replaced = processNode(childNodes[i]);
                    if (replaced) {
                        nodeReplaced = true;
                        // Re-get the child nodes as they may have changed
                        childNodes.splice(i, 1, ...Array.from(node.childNodes).slice(i));
                    }
                }

                // If no child nodes were replaced but the element still contains HTML,
                // try parsing the entire element's content
                if (!nodeReplaced && node.innerHTML.includes('<div class="image-container"')) {
                    const tempDoc = parser.parseFromString(node.innerHTML, 'text/html');
                    node.innerHTML = tempDoc.body.innerHTML;
                }
            }
        }

        return false; // No replacement
    };

    // Process all nodes in the document
    Array.from(doc.body.childNodes).forEach(processNode);

    // Find all div elements that might still contain image HTML as text
    const divs = doc.querySelectorAll('div');
    divs.forEach(div => {
        const text = div.textContent.trim();

        // Check if the div contains HTML for an image container
        if (text.includes('<div class="image-container"') ||
            (text.includes('<img src=') && text.includes('style="max-width:100%"'))) {

            // Parse the text as HTML
            const tempDoc = parser.parseFromString(text, 'text/html');

            // Replace the div's content with the parsed HTML
            div.innerHTML = tempDoc.body.innerHTML;
        }
    });

    // Convert the document back to HTML
    return doc.body.innerHTML;
}

// Render Markdown to HTML with proper processing
function renderMarkdown(markdownText) {
    if (!markdownText) return '';

    // Initialize markdown-it with additional options
    const md = initializeMarkdownIt();

    // Enable the attribute plugin for IDs on headings
    md.use(function(md) {
        // Simple attribute parser for headings
        const originalHeadingRule = md.renderer.rules.heading_open || function(tokens, idx, options, env, self) {
            return self.renderToken(tokens, idx, options);
        };

        md.renderer.rules.heading_open = function(tokens, idx, options, env, self) {
            const token = tokens[idx];
            const nextToken = tokens[idx + 1];

            // Check if the heading content contains an ID attribute
            if (nextToken && nextToken.type === 'inline' && nextToken.content.includes('{#')) {
                const match = nextToken.content.match(/\{#([^}]+)\}/);
                if (match) {
                    // Add the ID to the heading tag
                    token.attrJoin('id', match[1]);
                    // Remove the ID syntax from the content
                    nextToken.content = nextToken.content.replace(/\s*\{#[^}]+\}\s*/, '');
                }
            }

            // Special handling for Sources heading
            if (token.tag === 'h2' && nextToken && nextToken.content === 'Sources') {
                token.attrJoin('id', 'sources-heading');
            }

            return originalHeadingRule(tokens, idx, options, env, self);
        };
    });

    // Process headings before rendering
    const processedText = processMarkdownHeadings(markdownText);

    // Render to HTML
    let html = md.render(processedText);

    // Fix any image containers that might be showing as HTML
    html = fixImageContainers(html);

    // Post-process HTML to improve spacing
    // Add extra spacing between paragraphs
    html = html.replace(/<\/p><p>/g, '</p>\n\n<p>');

    // Add extra spacing after lists
    html = html.replace(/<\/ul><p>/g, '</ul>\n\n<p>');
    html = html.replace(/<\/ol><p>/g, '</ol>\n\n<p>');

    // Add extra spacing after headings
    html = html.replace(/<\/h([1-6])><p>/g, '</h$1>\n\n<p>');

    // Wrap in task-summary class for styling
    html = '<div class="task-summary">' + html + '</div>';

    return html;
}

// Export functions
window.markdownProcessor = {
    initializeMarkdownIt,
    processMarkdownHeadings,
    fixImageContainers,
    renderMarkdown
};
