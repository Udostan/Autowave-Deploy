/**
 * ARCHIVED: Webpage Generator JavaScript - MOVED TO CODE WAVE
 *
 * This file has been archived because webpage generation has been moved to Code Wave.
 * All webpage creation functionality should now be handled by Code Wave instead.
 *
 * DO NOT USE THIS FILE FOR NEW DEVELOPMENT
 */

// Function to download the webpage
function downloadWebpage() {
    // Create a blob from the webpage content
    const content = document.querySelector('.webpage-preview').outerHTML;
    const title = document.querySelector('.text-2xl.font-bold').textContent;

    // Create the HTML content with Tailwind CSS
    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    animation: {
                        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                    }
                }
            }
        }
    </script>
</head>
<body>
    ${content}
    <script>
        // Check for dark mode preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.classList.add('dark');
        }

        // Add animation to sections on scroll
        document.addEventListener('DOMContentLoaded', function() {
            const sections = document.querySelectorAll('section');

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-pulse-slow');
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });

            sections.forEach(section => {
                observer.observe(section);
            });
        });
    </script>
</body>
</html>`;

    // Create a blob and download
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = title.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.html';
    link.click();
}

// Function to toggle dark mode in the preview
function toggleDarkMode() {
    const preview = document.querySelector('.webpage-preview');
    if (preview) {
        preview.classList.toggle('dark');
    }
}

// Initialize webpage functionality when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener to download button if it exists
    const downloadButton = document.getElementById('downloadWebpageButton');
    if (downloadButton) {
        downloadButton.addEventListener('click', downloadWebpage);
    }

    // Add event listener to dark mode toggle if it exists
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
});
