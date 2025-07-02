/**
 * Booking Results Handler
 * Enhances the display of booking results in the task summary
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the booking results handler
    initBookingResultsHandler();
});

function initBookingResultsHandler() {
    // Listen for task summary updates
    document.addEventListener('taskSummaryUpdated', function(event) {
        enhanceBookingResults();
    });
}

/**
 * Enhance booking results display in task summaries
 */
function enhanceBookingResults() {
    // Get all summary containers
    const summaryContainers = document.querySelectorAll('.summary-container-content');
    
    summaryContainers.forEach(container => {
        // Check if this is a booking result
        if (isBookingResult(container)) {
            transformBookingResult(container);
        }
    });
}

/**
 * Check if a container contains booking results
 */
function isBookingResult(container) {
    // Look for booking-related headers
    const headers = container.querySelectorAll('h1');
    for (const header of headers) {
        const text = header.textContent.toLowerCase();
        if (text.includes('flight options') || 
            text.includes('hotel options') || 
            text.includes('ride options') ||
            text.includes('car rental options')) {
            return true;
        }
    }
    
    // Check for booking sections
    if (container.textContent.toLowerCase().includes('price comparison') ||
        container.textContent.toLowerCase().includes('booking links')) {
        return true;
    }
    
    return false;
}

/**
 * Transform booking results with enhanced UI
 */
function transformBookingResult(container) {
    // Add booking-results class to container
    container.classList.add('booking-results');
    
    // Transform price comparison section
    transformPriceComparison(container);
    
    // Transform best value and lowest price options
    transformValueOptions(container);
    
    // Transform all options section
    transformAllOptions(container);
    
    // Transform booking links
    transformBookingLinks(container);
}

/**
 * Transform price comparison section
 */
function transformPriceComparison(container) {
    const priceComparisonHeader = Array.from(container.querySelectorAll('h2')).find(
        h => h.textContent.trim() === 'Price Comparison'
    );
    
    if (priceComparisonHeader) {
        // Create a wrapper for the price comparison section
        const wrapper = document.createElement('div');
        wrapper.className = 'price-comparison';
        
        // Find all elements until the next h2 or h3
        let currentElement = priceComparisonHeader.nextElementSibling;
        const elements = [];
        
        while (currentElement && 
               currentElement.tagName !== 'H2' && 
               currentElement.tagName !== 'H3') {
            elements.push(currentElement);
            currentElement = currentElement.nextElementSibling;
        }
        
        // Move elements to the wrapper
        wrapper.appendChild(priceComparisonHeader.cloneNode(true));
        elements.forEach(el => {
            // Transform provider list
            if (el.textContent.includes('Providers:')) {
                const providersText = el.textContent;
                const providers = providersText.split('Providers:')[1].split(',').map(p => p.trim());
                
                const providersWrapper = document.createElement('div');
                providersWrapper.className = 'providers-list';
                
                providers.forEach(provider => {
                    if (provider) {
                        const tag = document.createElement('span');
                        tag.className = 'provider-tag';
                        tag.textContent = provider;
                        providersWrapper.appendChild(tag);
                    }
                });
                
                const newEl = document.createElement('div');
                newEl.innerHTML = `<div class="detail-label">Providers:</div>`;
                newEl.appendChild(providersWrapper);
                wrapper.appendChild(newEl);
            }
            // Transform price range
            else if (el.textContent.includes('Price Range:')) {
                const priceRangeText = el.textContent;
                const priceRange = priceRangeText.split('Price Range:')[1].trim();
                
                const newEl = document.createElement('div');
                newEl.innerHTML = `<div class="detail-label">Price Range</div>
                                   <div class="price-range">${priceRange}</div>`;
                wrapper.appendChild(newEl);
            }
            else {
                wrapper.appendChild(el.cloneNode(true));
            }
        });
        
        // Replace the original section with the enhanced version
        if (priceComparisonHeader.parentNode) {
            priceComparisonHeader.parentNode.insertBefore(wrapper, priceComparisonHeader);
            priceComparisonHeader.remove();
            elements.forEach(el => el.remove());
        }
    }
}

/**
 * Transform best value and lowest price options
 */
function transformValueOptions(container) {
    // Find best value option
    const bestValueHeader = Array.from(container.querySelectorAll('h3')).find(
        h => h.textContent.trim() === 'Best Value Option'
    );
    
    if (bestValueHeader) {
        transformOptionSection(bestValueHeader, 'best-value-option', 'Best Value');
    }
    
    // Find lowest price option
    const lowestPriceHeader = Array.from(container.querySelectorAll('h3')).find(
        h => h.textContent.trim() === 'Lowest Price Option'
    );
    
    if (lowestPriceHeader) {
        transformOptionSection(lowestPriceHeader, 'lowest-price-option', 'Lowest Price');
    }
}

/**
 * Transform an option section (best value or lowest price)
 */
function transformOptionSection(header, className, labelText) {
    // Create a wrapper for the option section
    const wrapper = document.createElement('div');
    wrapper.className = className;
    
    // Add the label
    const label = document.createElement('div');
    label.className = `option-label ${className.replace('-option', '')}-label`;
    label.textContent = labelText;
    wrapper.appendChild(label);
    
    // Find all elements until the next h2 or h3
    let currentElement = header.nextElementSibling;
    const elements = [];
    
    while (currentElement && 
           currentElement.tagName !== 'H2' && 
           currentElement.tagName !== 'H3') {
        elements.push(currentElement);
        currentElement = currentElement.nextElementSibling;
    }
    
    // Create details container
    const details = document.createElement('div');
    details.className = 'option-details';
    
    // Process each detail
    elements.forEach(el => {
        if (el.textContent.includes(':')) {
            const parts = el.textContent.split(':');
            const label = parts[0].trim();
            const value = parts.slice(1).join(':').trim();
            
            const detailItem = document.createElement('div');
            detailItem.className = 'detail-item';
            
            // Special formatting for price
            if (label.includes('Price')) {
                detailItem.innerHTML = `
                    <div class="detail-label">${label}</div>
                    <div class="price-value">${value}</div>
                `;
            } else {
                detailItem.innerHTML = `
                    <div class="detail-label">${label}</div>
                    <div class="detail-value">${value}</div>
                `;
            }
            
            details.appendChild(detailItem);
        } else {
            details.appendChild(el.cloneNode(true));
        }
    });
    
    wrapper.appendChild(details);
    
    // Replace the original section with the enhanced version
    if (header.parentNode) {
        header.parentNode.insertBefore(wrapper, header);
        header.remove();
        elements.forEach(el => el.remove());
    }
}

/**
 * Transform all options section
 */
function transformAllOptions(container) {
    const allOptionsHeader = Array.from(container.querySelectorAll('h2')).find(
        h => h.textContent.trim() === 'All Available Options'
    );
    
    if (allOptionsHeader) {
        // Create a wrapper for all options
        const wrapper = document.createElement('div');
        wrapper.className = 'all-options';
        wrapper.appendChild(allOptionsHeader.cloneNode(true));
        
        // Create grid for options
        const optionsGrid = document.createElement('div');
        optionsGrid.className = 'options-grid';
        
        // Find all option headers (h3 elements after the all options header)
        const optionHeaders = [];
        let currentElement = allOptionsHeader.nextElementSibling;
        
        while (currentElement && currentElement.tagName !== 'H2') {
            if (currentElement.tagName === 'H3') {
                optionHeaders.push(currentElement);
            }
            currentElement = currentElement.nextElementSibling;
        }
        
        // Process each option
        optionHeaders.forEach(header => {
            const optionCard = createOptionCard(header);
            if (optionCard) {
                optionsGrid.appendChild(optionCard);
            }
        });
        
        wrapper.appendChild(optionsGrid);
        
        // Replace the original section
        if (allOptionsHeader.parentNode) {
            const endElement = findSectionEnd(allOptionsHeader);
            allOptionsHeader.parentNode.insertBefore(wrapper, allOptionsHeader);
            
            // Remove original elements
            let current = allOptionsHeader;
            while (current && current !== endElement) {
                const next = current.nextElementSibling;
                current.remove();
                current = next;
            }
        }
    }
}

/**
 * Create an option card for the all options grid
 */
function createOptionCard(header) {
    if (!header) return null;
    
    const card = document.createElement('div');
    card.className = 'option-card';
    
    // Extract the title
    const title = header.textContent.trim();
    
    // Find all elements until the next h3 or h2
    let currentElement = header.nextElementSibling;
    const elements = [];
    
    while (currentElement && 
           currentElement.tagName !== 'H3' && 
           currentElement.tagName !== 'H2') {
        elements.push(currentElement);
        currentElement = currentElement.nextElementSibling;
    }
    
    // Extract price and other details
    let price = '';
    const details = [];
    
    elements.forEach(el => {
        if (el.textContent.includes('Price:')) {
            price = el.textContent.split('Price:')[1].trim();
        } else if (el.textContent.includes(':')) {
            details.push(el.textContent.trim());
        }
    });
    
    // Create card header
    const cardHeader = document.createElement('div');
    cardHeader.className = 'option-card-header';
    cardHeader.innerHTML = `
        <h4 class="option-card-title">${title}</h4>
        <div class="option-card-price">${price}</div>
    `;
    card.appendChild(cardHeader);
    
    // Create card details
    if (details.length > 0) {
        const cardDetails = document.createElement('div');
        cardDetails.className = 'option-card-details';
        
        details.forEach(detail => {
            const parts = detail.split(':');
            const label = parts[0].trim();
            const value = parts.slice(1).join(':').trim();
            
            const detailElement = document.createElement('div');
            detailElement.className = 'option-card-detail';
            detailElement.innerHTML = `
                <span class="option-card-detail-icon">•</span>
                <span><strong>${label}:</strong> ${value}</span>
            `;
            cardDetails.appendChild(detailElement);
        });
        
        card.appendChild(cardDetails);
    }
    
    return card;
}

/**
 * Transform booking links section
 */
function transformBookingLinks(container) {
    const bookingLinksHeader = Array.from(container.querySelectorAll('h2')).find(
        h => h.textContent.trim() === 'Booking Links'
    );
    
    if (bookingLinksHeader) {
        // Create a wrapper for booking links
        const wrapper = document.createElement('div');
        wrapper.className = 'booking-links';
        wrapper.appendChild(bookingLinksHeader.cloneNode(true));
        
        // Find the list of links
        let linksList = null;
        let currentElement = bookingLinksHeader.nextElementSibling;
        
        while (currentElement && currentElement.tagName !== 'H2') {
            if (currentElement.tagName === 'UL') {
                linksList = currentElement;
                break;
            }
            currentElement = currentElement.nextElementSibling;
        }
        
        if (linksList) {
            // Create grid for links
            const linksGrid = document.createElement('div');
            linksGrid.className = 'booking-links-grid';
            
            // Process each link
            const links = linksList.querySelectorAll('a');
            links.forEach(link => {
                const href = link.getAttribute('href');
                const text = link.textContent.trim();
                
                const linkElement = document.createElement('a');
                linkElement.className = 'booking-link';
                linkElement.href = href;
                linkElement.textContent = text;
                linkElement.target = '_blank';
                
                linksGrid.appendChild(linkElement);
            });
            
            wrapper.appendChild(linksGrid);
            
            // Replace the original section
            if (bookingLinksHeader.parentNode) {
                const endElement = findSectionEnd(bookingLinksHeader);
                bookingLinksHeader.parentNode.insertBefore(wrapper, bookingLinksHeader);
                
                // Remove original elements
                let current = bookingLinksHeader;
                while (current && current !== endElement) {
                    const next = current.nextElementSibling;
                    current.remove();
                    current = next;
                }
            }
        }
    }
}

/**
 * Find the end of a section (next h2 or end of container)
 */
function findSectionEnd(startElement) {
    let current = startElement.nextElementSibling;
    
    while (current) {
        if (current.tagName === 'H2') {
            return current;
        }
        current = current.nextElementSibling;
    }
    
    return null;
}
