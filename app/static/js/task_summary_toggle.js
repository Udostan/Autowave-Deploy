// Task Summary Toggle Handler
document.addEventListener('DOMContentLoaded', function() {
    console.log('Task Summary Toggle Handler loaded');

    // Get the toggle button and summary container
    const toggleSummaryBtn = document.getElementById('toggleSummaryBtn');
    const taskSummaryContainer = document.getElementById('taskSummaryContainer');
    const summaryContainers = document.getElementById('summaryContainers');
    const resultsContainer = document.getElementById('resultsContainer');

    // If the elements don't exist, don't proceed
    if (!toggleSummaryBtn || !taskSummaryContainer || !summaryContainers || !resultsContainer) {
        console.warn('Toggle button, task summary container, summary containers, or results container not found');
        return;
    }

    console.log('Found toggle button and task summary container');

    // Get the SVG icon inside the toggle button
    const toggleIcon = toggleSummaryBtn.querySelector('svg');

    // Get the task progress container (left column)
    const taskProgressContainer = document.querySelector('#resultsContainer .grid > div:first-child');

    // Add click event listener to the toggle button
    toggleSummaryBtn.addEventListener('click', function() {
        console.log('Toggle summary button clicked');

        // Toggle the expanded class on the results container
        resultsContainer.classList.toggle('summary-expanded');

        // Update the toggle icon and title
        if (resultsContainer.classList.contains('summary-expanded')) {
            // Change to expanded state
            toggleSummaryBtn.title = "Collapse task summary section";

            // Hide the task progress container
            if (taskProgressContainer) {
                taskProgressContainer.style.display = 'none';
            }

            // Make the task summary container take full width
            taskSummaryContainer.style.gridColumn = '1 / -1';
        } else {
            // Change to normal state
            toggleSummaryBtn.title = "Expand task summary section";

            // Show the task progress container
            if (taskProgressContainer) {
                taskProgressContainer.style.display = '';
            }

            // Reset the task summary container width
            taskSummaryContainer.style.gridColumn = '';
        }
    });

    console.log('Task Summary Toggle Handler initialized');
});
