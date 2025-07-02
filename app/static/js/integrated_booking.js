/**
 * Integrated Booking Handler
 * Handles the booking functionality within the task tab
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the integrated booking handler
    initIntegratedBookingHandler();
});

function initIntegratedBookingHandler() {
    // Get DOM elements
    const enableBookingOptions = document.getElementById('enableBookingOptions');
    const bookingOptionsContainer = document.getElementById('bookingOptionsContainer');
    const bookingTypeSelect = document.getElementById('bookingType');
    const carTypeContainer = document.getElementById('carTypeContainer');
    const rideTypeContainer = document.getElementById('rideTypeContainer');
    const destinationContainer = document.getElementById('destinationContainer');
    const executeTaskBtn = document.getElementById('executeTaskBtn');
    const taskDescription = document.getElementById('taskDescription');
    
    // Set today's date as the default for start date
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        const nextWeek = new Date(today);
        nextWeek.setDate(nextWeek.getDate() + 7);
        
        startDateInput.valueAsDate = tomorrow;
        endDateInput.valueAsDate = nextWeek;
    }
    
    // Toggle booking options visibility
    if (enableBookingOptions && bookingOptionsContainer) {
        enableBookingOptions.addEventListener('change', function() {
            if (this.checked) {
                bookingOptionsContainer.classList.remove('hidden');
            } else {
                bookingOptionsContainer.classList.add('hidden');
            }
        });
    }
    
    // Handle booking type changes
    if (bookingTypeSelect) {
        bookingTypeSelect.addEventListener('change', function() {
            updateFormFields(this.value);
        });
        
        // Initialize form fields based on default selection
        updateFormFields(bookingTypeSelect.value);
    }
    
    // Modify the execute task button to include booking information if enabled
    if (executeTaskBtn && taskDescription) {
        executeTaskBtn.addEventListener('click', function(e) {
            if (enableBookingOptions && enableBookingOptions.checked) {
                // Get the current task description
                let description = taskDescription.value.trim();
                
                // Append booking information to the task description
                const bookingInfo = generateBookingTaskDescription();
                if (bookingInfo) {
                    if (description) {
                        description += "\n\n" + bookingInfo;
                    } else {
                        description = bookingInfo;
                    }
                    
                    // Update the task description
                    taskDescription.value = description;
                }
            }
            
            // The regular task execution will continue as normal
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
    
    if (!carTypeContainer || !rideTypeContainer || !destinationContainer || 
        !originLabel || !dateSelectionContainer || !startDateLabel || !endDateLabel) {
        return;
    }
    
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
 * Generate booking task description based on form values
 */
function generateBookingTaskDescription() {
    // Get form values
    const bookingType = document.getElementById('bookingType').value;
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const travelers = document.getElementById('travelers').value;
    
    if (!origin) {
        alert('Please enter an origin/location');
        return null;
    }
    
    if ((bookingType === 'flight' || bookingType === 'ride') && !destination) {
        alert('Please enter a destination');
        return null;
    }
    
    if ((bookingType === 'flight' || bookingType === 'hotel' || bookingType === 'car') && (!startDate || !endDate)) {
        alert('Please enter dates');
        return null;
    }
    
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
    
    // Add advanced options
    if (compareAllProviders) {
        taskDescription += ". Compare prices across multiple providers";
    }
    
    if (showRealTimeResults) {
        taskDescription += ". Show real-time availability and pricing";
    }
    
    return taskDescription;
}
