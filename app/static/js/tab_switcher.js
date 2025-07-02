// Tab switching functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tab switcher loaded');

    // Get all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');

    // Log all tab buttons
    console.log('Found tab buttons:', tabButtons.length);
    tabButtons.forEach(button => {
        console.log('Tab button:', button.getAttribute('data-tab'));
    });

    // Add click event listeners to each tab button
    tabButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const tabId = this.getAttribute('data-tab');
            console.log('Tab button clicked:', tabId);
            switchTab(tabId);
        });
    });

    // Function to switch tabs
    function switchTab(tabId) {
        console.log('Switching to tab:', tabId);

        // Get all tab contents
        const tabContents = document.querySelectorAll('.tab-content');

        // Log all tab contents
        console.log('Found tab contents:', tabContents.length);
        tabContents.forEach(content => {
            console.log('Tab content ID:', content.id);
        });

        // Hide all tab contents
        tabContents.forEach(content => {
            content.classList.add('hidden');
        });

        // Show the selected tab content
        const selectedContent = document.getElementById(`${tabId}-content`);
        if (selectedContent) {
            selectedContent.classList.remove('hidden');
            console.log(`Showing tab content: ${tabId}-content`);
        } else {
            console.error(`Tab content not found: ${tabId}-content`);
        }

        // Update tab button styles
        tabButtons.forEach(btn => {
            // Reset all buttons
            btn.classList.remove('border-white', 'text-white');
            btn.classList.add('border-transparent', 'text-gray-400');

            // Highlight the selected button
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.remove('border-transparent', 'text-gray-400');
                btn.classList.add('border-white', 'text-white');
            }
        });
    }

    // Check if there's a tab parameter in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');

    // Show the specified tab or the task tab by default
    if (tabParam && document.querySelector(`.tab-button[data-tab="${tabParam}"]`)) {
        console.log('Switching to tab from URL parameter:', tabParam);
        switchTab(tabParam);
    } else {
        console.log('Switching to default tab: task');
        switchTab('task');
    }
});
