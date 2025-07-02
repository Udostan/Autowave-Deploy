/**
 * Agen911 - Main JavaScript
 * Contains common functionality for the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');

    // Always use light theme as requested
    document.body.setAttribute('data-theme', 'light');
    document.body.classList.remove('dark-mode');

    // Store light theme preference
    localStorage.setItem('theme', 'light');

    // Theme toggle functionality removed as requested
    // Add loading animation when forms are submitted
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
                submitButton.disabled = true;

                // Store the original text to restore it if there's an error
                submitButton.dataset.originalText = originalText;
            }

            // Create a loading overlay for results container if it exists
            const resultsContainer = document.querySelector('.results-container');
            if (resultsContainer) {
                const loadingOverlay = document.createElement('div');
                loadingOverlay.className = 'loading';
                loadingOverlay.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';

                resultsContainer.innerHTML = '';
                resultsContainer.appendChild(loadingOverlay);
            }
        });
    });

    // Handle form validation errors
    forms.forEach(form => {
        form.addEventListener('invalid', function(e) {
            // Prevent the browser's default validation popup
            e.preventDefault();

            // Get the invalid input
            const invalidInput = e.target;

            // Add error styling
            invalidInput.classList.add('input-error');

            // Create error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'error-message';
            errorMessage.textContent = invalidInput.validationMessage;

            // Insert error message after the input
            invalidInput.parentNode.insertBefore(errorMessage, invalidInput.nextSibling);

            // Remove error styling and message when input is focused
            invalidInput.addEventListener('focus', function() {
                this.classList.remove('input-error');
                if (errorMessage.parentNode) {
                    errorMessage.parentNode.removeChild(errorMessage);
                }
            }, { once: true });
        }, true);
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Alt+S to focus search
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="query"]');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Alt+C to focus chat
        if (e.altKey && e.key === 'c') {
            e.preventDefault();
            const chatInput = document.querySelector('input[name="message"]');
            if (chatInput) {
                chatInput.focus();
            }
        }

        // Alt+H to open professional history sidebar (replaced old history page)
        if (e.altKey && e.key === 'h') {
            e.preventDefault();
            // Open the professional history sidebar instead
            if (window.professionalHistory) {
                window.professionalHistory.openSidebar();
            }
        }

        // Alt+Home to go to home
        if (e.altKey && e.key === 'Home') {
            e.preventDefault();
            window.location.href = '/';
        }
    });
});
