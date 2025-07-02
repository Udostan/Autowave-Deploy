/**
 * Booking Handler
 * Handles the booking tab functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the booking handler
    initBookingHandler();
});

function initBookingHandler() {
    // Get DOM elements
    const bookingTypeSelect = document.getElementById('bookingType');
    const carTypeContainer = document.getElementById('carTypeContainer');
    const rideTypeContainer = document.getElementById('rideTypeContainer');
    const destinationContainer = document.getElementById('destinationContainer');
    const searchBookingBtn = document.getElementById('searchBookingBtn');
    const bookingResultsContainer = document.getElementById('bookingResultsContainer');
    const bookingResultsContent = document.getElementById('bookingResultsContent');
    
    // Set today's date as the default for start date
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);
    
    startDateInput.valueAsDate = tomorrow;
    endDateInput.valueAsDate = nextWeek;
    
    // Handle booking type changes
    if (bookingTypeSelect) {
        bookingTypeSelect.addEventListener('change', function() {
            updateFormFields(this.value);
        });
        
        // Initialize form fields based on default selection
        updateFormFields(bookingTypeSelect.value);
    }
    
    // Handle search button click
    if (searchBookingBtn) {
        searchBookingBtn.addEventListener('click', function() {
            executeBookingSearch();
        });
    }
    
    // Handle expand button click
    const expandBookingResultsBtn = document.getElementById('expandBookingResultsBtn');
    if (expandBookingResultsBtn) {
        expandBookingResultsBtn.addEventListener('click', function() {
            toggleFullscreen('bookingResultsDisplay');
        });
    }
    
    // Handle download button click
    const downloadBookingResultsBtn = document.getElementById('downloadBookingResultsBtn');
    if (downloadBookingResultsBtn) {
        downloadBookingResultsBtn.addEventListener('click', function() {
            downloadBookingResults();
        });
    }
}

/**
 * Update form fields based on booking type
 */
function updateFormFields(bookingType) {
    const carTypeContainer = document.getElementById('carTypeContainer');
    const rideTypeContainer = document.getElementById('rideTypeContainer');
    const destinationContainer = document.getElementById('destinationContainer');
    const originLabel = document.querySelector('label[for="origin"]');
    const dateSelectionContainer = document.getElementById('dateSelectionContainer');
    const startDateLabel = document.querySelector('label[for="startDate"]');
    const endDateLabel = document.querySelector('label[for="endDate"]');
    
    // Reset all containers
    carTypeContainer.classList.add('hidden');
    rideTypeContainer.classList.add('hidden');
    destinationContainer.classList.remove('hidden');
    
    // Update form fields based on booking type
    switch (bookingType) {
        case 'flight':
            originLabel.textContent = 'Origin City/Airport';
            startDateLabel.textContent = 'Departure Date';
            endDateLabel.textContent = 'Return Date';
            dateSelectionContainer.classList.remove('hidden');
            break;
            
        case 'hotel':
            originLabel.textContent = 'Destination City';
            startDateLabel.textContent = 'Check-in Date';
            endDateLabel.textContent = 'Check-out Date';
            destinationContainer.classList.add('hidden');
            dateSelectionContainer.classList.remove('hidden');
            break;
            
        case 'car':
            originLabel.textContent = 'Pickup Location';
            startDateLabel.textContent = 'Pickup Date';
            endDateLabel.textContent = 'Return Date';
            destinationContainer.classList.add('hidden');
            carTypeContainer.classList.remove('hidden');
            dateSelectionContainer.classList.remove('hidden');
            break;
            
        case 'ride':
            originLabel.textContent = 'Pickup Location';
            destinationContainer.classList.remove('hidden');
            rideTypeContainer.classList.remove('hidden');
            dateSelectionContainer.classList.add('hidden');
            break;
    }
}

/**
 * Execute booking search
 */
function executeBookingSearch() {
    // Show booking results container
    const bookingResultsContainer = document.getElementById('bookingResultsContainer');
    bookingResultsContainer.classList.remove('hidden');
    
    // Get form values
    const bookingType = document.getElementById('bookingType').value;
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const travelers = document.getElementById('travelers').value;
    
    // Additional options based on booking type
    let additionalOptions = {};
    if (bookingType === 'car') {
        additionalOptions.carType = document.getElementById('carType').value;
    } else if (bookingType === 'ride') {
        additionalOptions.rideType = document.getElementById('rideType').value;
    }
    
    // Advanced options
    const compareAllProviders = document.getElementById('compareAllProviders').checked;
    const showRealTimeResults = document.getElementById('showRealTimeResults').checked;
    
    // Update progress indicators
    updateBookingProgress(10, 'Preparing search query...');
    
    // Create booking task description
    let taskDescription = '';
    
    switch (bookingType) {
        case 'flight':
            taskDescription = `Find flights from ${origin} to ${destination} on ${startDate}`;
            if (endDate) {
                taskDescription += ` returning on ${endDate}`;
            }
            taskDescription += ` for ${travelers} traveler${travelers > 1 ? 's' : ''}`;
            break;
            
        case 'hotel':
            taskDescription = `Book a hotel in ${origin} from ${startDate} to ${endDate} for ${travelers} guest${travelers > 1 ? 's' : ''}`;
            break;
            
        case 'car':
            taskDescription = `Rent a ${additionalOptions.carType} car in ${origin} from ${startDate} to ${endDate}`;
            break;
            
        case 'ride':
            taskDescription = `Get a ${additionalOptions.rideType} ride from ${origin} to ${destination}`;
            break;
    }
    
    // Update search process display
    updateSearchProcess(taskDescription);
    
    // Execute the task using the Super Agent's task execution functionality
    updateBookingProgress(20, 'Searching for options...');
    
    // Simulate API call to execute task
    setTimeout(() => {
        updateBookingProgress(50, 'Processing results...');
        
        // Execute the task using the existing task execution functionality
        executeTask(taskDescription, true).then(result => {
            // Update progress
            updateBookingProgress(100, 'Search completed!');
            
            // Display results
            if (result && result.task_summary) {
                displayBookingResults(result.task_summary);
            } else {
                displayBookingError('No results found. Please try again with different search criteria.');
            }
        }).catch(error => {
            updateBookingProgress(100, 'Search failed');
            displayBookingError('An error occurred while searching. Please try again.');
            console.error('Booking search error:', error);
        });
    }, 1000);
}

/**
 * Update booking progress indicator
 */
function updateBookingProgress(percentage, message) {
    const progressFill = document.getElementById('bookingProgressFill');
    const stepDescription = document.getElementById('bookingStepDescription');
    const processingIndicator = document.getElementById('bookingProcessingIndicator');
    
    if (progressFill) {
        progressFill.style.width = `${percentage}%`;
    }
    
    if (stepDescription) {
        stepDescription.textContent = message;
    }
    
    if (processingIndicator && percentage >= 100) {
        processingIndicator.classList.add('completed');
    } else if (processingIndicator) {
        processingIndicator.classList.remove('completed');
    }
}

/**
 * Update search process display
 */
function updateSearchProcess(taskDescription) {
    const searchProcessContainer = document.getElementById('searchProcessContainer');
    
    if (searchProcessContainer) {
        searchProcessContainer.innerHTML = `
            <div class="bg-gray-50 px-4 py-3 rounded-md border border-gray-200">
                <h4 class="font-medium text-gray-700 mb-2">Search Query</h4>
                <div class="prose prose-sm max-w-none text-sm text-gray-500">
                    <p>${taskDescription}</p>
                </div>
            </div>
            <div class="bg-gray-50 px-4 py-3 rounded-md border border-gray-200">
                <h4 class="font-medium text-gray-700 mb-2">Search Process</h4>
                <div class="prose prose-sm max-w-none text-sm text-gray-500">
                    <p>1. Analyzing search parameters</p>
                    <p>2. Connecting to booking providers</p>
                    <p>3. Retrieving real-time availability and pricing</p>
                    <p>4. Comparing options across providers</p>
                    <p>5. Generating comprehensive results</p>
                </div>
            </div>
        `;
    }
}

/**
 * Display booking results
 */
function displayBookingResults(resultHtml) {
    const bookingResultsContent = document.getElementById('bookingResultsContent');
    
    if (bookingResultsContent) {
        // Process the markdown content
        bookingResultsContent.innerHTML = '';
        
        // Create a container for the results
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'booking-results';
        resultsContainer.innerHTML = processMarkdown(resultHtml);
        
        bookingResultsContent.appendChild(resultsContainer);
        
        // Trigger the booking results enhancement
        setTimeout(() => {
            const event = new CustomEvent('taskSummaryUpdated');
            document.dispatchEvent(event);
        }, 100);
    }
}

/**
 * Display booking error
 */
function displayBookingError(errorMessage) {
    const bookingResultsContent = document.getElementById('bookingResultsContent');
    
    if (bookingResultsContent) {
        bookingResultsContent.innerHTML = `
            <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-red-700">${errorMessage}</p>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Toggle fullscreen for an element
 */
function toggleFullscreen(elementId) {
    const element = document.getElementById(elementId);
    
    if (!element) return;
    
    if (!element.classList.contains('fullscreen')) {
        // Save current position and size
        element.dataset.originalParent = element.parentNode.id;
        element.dataset.originalPosition = window.getComputedStyle(element).position;
        element.dataset.originalZIndex = window.getComputedStyle(element).zIndex;
        element.dataset.originalWidth = window.getComputedStyle(element).width;
        element.dataset.originalHeight = window.getComputedStyle(element).height;
        
        // Make fullscreen
        element.classList.add('fullscreen');
        element.style.position = 'fixed';
        element.style.top = '0';
        element.style.left = '0';
        element.style.width = '100vw';
        element.style.height = '100vh';
        element.style.zIndex = '9999';
        element.style.background = 'white';
        
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.className = 'absolute top-4 right-4 p-2 rounded-full bg-gray-200 text-gray-800 hover:bg-gray-300';
        closeButton.innerHTML = '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
        closeButton.onclick = function() {
            toggleFullscreen(elementId);
        };
        element.appendChild(closeButton);
    } else {
        // Restore original position and size
        element.classList.remove('fullscreen');
        element.style.position = element.dataset.originalPosition;
        element.style.top = 'auto';
        element.style.left = 'auto';
        element.style.width = element.dataset.originalWidth;
        element.style.height = element.dataset.originalHeight;
        element.style.zIndex = element.dataset.originalZIndex;
        
        // Remove close button
        const closeButton = element.querySelector('button.absolute');
        if (closeButton) {
            closeButton.remove();
        }
    }
}

/**
 * Download booking results
 */
function downloadBookingResults() {
    const bookingResultsContent = document.getElementById('bookingResultsContent');
    
    if (!bookingResultsContent) return;
    
    // Get the content
    const content = bookingResultsContent.innerHTML;
    
    // Create a blob
    const blob = new Blob([content], { type: 'text/html' });
    
    // Create a download link
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `booking_results_${new Date().toISOString().slice(0, 10)}.html`;
    
    // Trigger download
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
