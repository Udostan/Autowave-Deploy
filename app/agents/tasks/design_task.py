"""
Design Task Handler for Super Agent.
Handles tasks related to code generation, diagram creation, and other design tasks.
"""

import logging
import json
import re
import base64
import os
from typing import Dict, List, Any, Optional

from app.agents.tasks.base_task import BaseTask
from app.utils.mcp_client import MCPClient
from app.utils.web_browser import WebBrowser

class DesignTask(BaseTask):
    """
    Task handler for design-related tasks like code generation and diagram creation.
    """

    def __init__(self, task_description: str, web_browser: WebBrowser = None, **kwargs):
        """
        Initialize the design task handler.

        Args:
            task_description: Description of the task to perform
            web_browser: Web browser instance for browsing
            **kwargs: Additional arguments
        """
        super().__init__(task_description, **kwargs)
        self.web_browser = web_browser or WebBrowser()
        self.mcp_client = MCPClient()
        self.logger = logging.getLogger(__name__)

        # Detect design task type
        self.design_type = self._detect_design_type(task_description)
        print(f"Detected design type: {self.design_type}")

    def execute(self) -> Dict[str, Any]:
        """
        Execute the design task.

        Returns:
            Task execution results
        """
        print(f"Executing design task: {self.task_description}")

        try:
            # Step 1: Analyze the task and gather requirements
            step1 = {"description": "Analyze requirements", "action": "analyze_requirements"}
            self.add_step(**step1)

            requirements = self._analyze_requirements()

            self.add_step_summary(
                description="Step 1: Analyze - Identifying key requirements",
                summary=f"Identified key requirements for the {self.design_type} task",
                success=True
            )

            self.add_result(
                step=step1,
                result={
                    "requirements": requirements,
                    "success": True
                }
            )

            # Step 2: Generate the design
            step2 = {"description": "Generate design", "action": "generate_design"}
            self.add_step(**step2)

            design_result = self._generate_design(requirements)

            self.add_step_summary(
                description=f"Step 2: Generate - Creating {self.design_type}",
                summary=f"Successfully generated {self.design_type}",
                success=True
            )

            self.add_result(
                step=step2,
                result={
                    "design": design_result,
                    "success": True
                }
            )

            # Generate a comprehensive task summary
            task_summary = self._generate_task_summary(design_result)
            self.set_task_summary(task_summary)
            self.set_success(True)

            return self.get_result()

        except Exception as e:
            print(f"Error executing design task: {str(e)}")
            self.set_task_summary(f"Error: {str(e)}")
            self.set_success(False)
            return self.get_result()

    def _detect_design_type(self, task_description: str) -> str:
        """
        Detect the type of design task from the description.

        Args:
            task_description: The task description

        Returns:
            The detected design type (webpage, diagram, pdf)
        """
        task_lower = task_description.lower()

        # Check for webpage creation
        webpage_patterns = [
            r'create\s+(?:a\s+)?(?:web)?page',
            r'build\s+(?:a\s+)?(?:web)?page',
            r'design\s+(?:a\s+)?(?:web)?page',
            r'make\s+(?:a\s+)?(?:web)?site',
            r'develop\s+(?:a\s+)?(?:web)?site',
            r'html',
            r'css',
            r'website',
            r'webpage',
            r'landing page'
        ]

        for pattern in webpage_patterns:
            if re.search(pattern, task_lower):
                return "webpage"

        # Check for diagram creation
        diagram_patterns = [
            r'create\s+(?:a\s+)?diagram',
            r'draw\s+(?:a\s+)?diagram',
            r'make\s+(?:a\s+)?diagram',
            r'design\s+(?:a\s+)?diagram',
            r'flowchart',
            r'sequence diagram',
            r'class diagram',
            r'er diagram',
            r'entity relationship',
            r'uml',
            r'mindmap',
            r'gantt'
        ]

        for pattern in diagram_patterns:
            if re.search(pattern, task_lower):
                return "diagram"

        # Check for PDF creation
        pdf_patterns = [
            r'create\s+(?:a\s+)?pdf',
            r'generate\s+(?:a\s+)?pdf',
            r'make\s+(?:a\s+)?pdf',
            r'pdf document',
            r'pdf report'
        ]

        for pattern in pdf_patterns:
            if re.search(pattern, task_lower):
                return "pdf"

        # Default to webpage if no specific type is detected
        return "webpage"

    def _analyze_requirements(self) -> Dict[str, Any]:
        """
        Analyze the task description to extract requirements.

        Returns:
            Dictionary of requirements
        """
        task_lower = self.task_description.lower()

        # Extract complexity
        complexity = "medium"  # Default
        if any(term in task_lower for term in ["simple", "basic", "easy"]):
            complexity = "simple"
        elif any(term in task_lower for term in ["complex", "advanced", "sophisticated"]):
            complexity = "complex"

        # Extract specific design type for diagrams
        diagram_type = "flowchart"  # Default
        if self.design_type == "diagram":
            if "flow" in task_lower:
                diagram_type = "flowchart"
            elif "sequence" in task_lower:
                diagram_type = "sequence"
            elif "class" in task_lower:
                diagram_type = "class"
            elif "er" in task_lower or "entity" in task_lower:
                diagram_type = "entity-relationship"
            elif "gantt" in task_lower:
                diagram_type = "gantt"
            elif "pie" in task_lower:
                diagram_type = "pie"
            elif "mind" in task_lower:
                diagram_type = "mindmap"
            elif "uml" in task_lower:
                diagram_type = "uml"

        # Return the requirements
        return {
            "design_type": self.design_type,
            "complexity": complexity,
            "diagram_type": diagram_type if self.design_type == "diagram" else None,
            "description": self.task_description
        }

    def _generate_design(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the design based on requirements.

        Args:
            requirements: The requirements dictionary

        Returns:
            The generated design
        """
        design_type = requirements["design_type"]

        if design_type == "webpage":
            return self._generate_webpage(requirements)
        elif design_type == "diagram":
            return self._generate_diagram(requirements)
        elif design_type == "pdf":
            return self._generate_pdf(requirements)
        else:
            raise ValueError(f"Unsupported design type: {design_type}")

    def _generate_webpage(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a webpage based on requirements.

        Args:
            requirements: The requirements dictionary

        Returns:
            The generated webpage
        """
        try:
            # Use the MCP client to call the generate_webpage tool
            result = self.mcp_client.execute_tool("generate_webpage", {
                "description": requirements["description"],
                "complexity": requirements["complexity"]
            })

            if result.get("status") == "success":
                return result.get("result", {})
            else:
                self.logger.error(f"Error generating webpage: {result.get('error', 'Unknown error')}")
                # Fall back to local generation if MCP server fails
                return self._generate_webpage_fallback(requirements)
        except Exception as e:
            self.logger.error(f"Error calling MCP server: {str(e)}")
            # Fall back to local generation if MCP server is unavailable
            return self._generate_webpage_fallback(requirements)

    def _generate_diagram(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a diagram based on requirements.

        Args:
            requirements: The requirements dictionary

        Returns:
            The generated diagram
        """
        try:
            # Use the MCP client to call the generate_diagram tool
            result = self.mcp_client.execute_tool("generate_diagram", {
                "description": requirements["description"],
                "diagram_type": requirements["diagram_type"]
            })

            if result.get("status") == "success":
                return result.get("result", {})
            else:
                self.logger.error(f"Error generating diagram: {result.get('error', 'Unknown error')}")
                # Fall back to local generation if MCP server fails
                return self._generate_diagram_fallback(requirements)
        except Exception as e:
            self.logger.error(f"Error calling MCP server: {str(e)}")
            # Fall back to local generation if MCP server is unavailable
            return self._generate_diagram_fallback(requirements)

    def _generate_pdf(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a PDF based on requirements.

        Args:
            requirements: The requirements dictionary

        Returns:
            The generated PDF
        """
        # First, generate content for the PDF
        content = self._generate_pdf_content(requirements["description"])

        try:
            # Use the MCP client to call the generate_pdf tool
            result = self.mcp_client.execute_tool("generate_pdf", {
                "content": content,
                "title": requirements["description"]
            })

            if result.get("status") == "success":
                return result.get("result", {})
            else:
                self.logger.error(f"Error generating PDF: {result.get('error', 'Unknown error')}")
                # Fall back to local generation if MCP server fails
                return self._generate_pdf_fallback(requirements, content)
        except Exception as e:
            self.logger.error(f"Error calling MCP server: {str(e)}")
            # Fall back to local generation if MCP server is unavailable
            return self._generate_pdf_fallback(requirements, content)

    def _generate_pdf_content(self, description: str) -> str:
        """
        Generate content for a PDF based on description.

        Args:
            description: The PDF description

        Returns:
            Markdown content for the PDF
        """
        # This is a simplified implementation
        # In a production system, this would call an LLM API

        # Extract a title from the description
        title_match = re.search(r'(?:about|on|for)\s+([^,.]+)', description, re.IGNORECASE)
        title = title_match.group(1) if title_match else description

        # Generate simple markdown content
        content = f"""# {title}

## Introduction

This document was automatically generated based on the request: "{description}".

## Content

This is a placeholder content section. In a real implementation, this would contain
detailed information about {title}.

## Conclusion

This document demonstrates the PDF generation capabilities of the Super Agent.
"""

        return content

    def _generate_task_summary(self, design_result: Dict[str, Any]) -> str:
        """
        Generate a comprehensive task summary.

        Args:
            design_result: The design generation result

        Returns:
            Markdown-formatted task summary
        """
        design_type = design_result.get("type", "")

        if design_type == "webpage":
            return self._generate_webpage_summary(design_result)
        elif design_type in ["flowchart", "sequence", "class", "entity-relationship", "gantt", "pie", "mindmap", "uml"]:
            return self._generate_diagram_summary(design_result)
        else:
            return self._generate_pdf_summary(design_result)

    def _generate_webpage_summary(self, design_result: Dict[str, Any]) -> str:
        """
        Generate a summary for a webpage design.

        Args:
            design_result: The webpage generation result

        Returns:
            Markdown-formatted summary
        """
        files = design_result.get("files", {})
        preview = design_result.get("preview", "")

        # Create a summary with code blocks and preview
        summary = f"""# Webpage Design

## Preview

![Webpage Preview]({preview})

## HTML Code

```html
{files.get("index.html", "")}
```

## CSS Code

```css
{files.get("styles.css", "")}
```

## JavaScript Code

```javascript
{files.get("app.js", "")}
```

## How to Use

1. Copy the HTML, CSS, and JavaScript code into separate files
2. Save them with the correct extensions (.html, .css, .js)
3. Open the HTML file in a web browser to view the webpage

You can also modify the code to customize the design according to your needs.
"""

        return summary

    def _generate_diagram_summary(self, design_result: Dict[str, Any]) -> str:
        """
        Generate a summary for a diagram design.

        Args:
            design_result: The diagram generation result

        Returns:
            Markdown-formatted summary
        """
        code = design_result.get("code", "")
        image = design_result.get("image", "")
        diagram_type = design_result.get("type", "diagram")

        # Create a summary with code and rendered diagram
        summary = f"""# {diagram_type.capitalize()} Diagram

## Rendered Diagram

![{diagram_type.capitalize()} Diagram]({image})

## Diagram Code

{code}

## How to Use

1. Copy the diagram code
2. Paste it into a Mermaid or PlantUML editor
3. Render the diagram to see the result

You can also modify the code to customize the diagram according to your needs.
"""

        return summary

    def _generate_pdf_summary(self, design_result: Dict[str, Any]) -> str:
        """
        Generate a summary for a PDF design.

        Args:
            design_result: The PDF generation result

        Returns:
            Markdown-formatted summary
        """
        preview = design_result.get("preview", "")
        title = design_result.get("title", "Generated PDF")
        pdf_base64 = design_result.get("pdf_base64", "")

        # Create a summary with preview and download link
        summary = f"""# PDF Document: {title}

## Preview

![PDF Preview]({preview})

## Download

[Download PDF](data:application/pdf;base64,{pdf_base64})

## Description

This PDF document was generated based on your request. You can download it using the link above.
"""

        return summary

    def _generate_webpage_fallback(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a webpage locally when MCP server is unavailable.

        Args:
            requirements: The requirements dictionary

        Returns:
            The generated webpage
        """
        description = requirements["description"]
        complexity = requirements["complexity"]

        # Basic HTML template
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{description}</h1>
            <nav>
                <ul>
                    <li><a href="#home">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </header>

        <main>
            <section id="home">
                <h2>Welcome</h2>
                <p>This is a generated webpage based on your description: "{description}"</p>
                <button id="actionButton">Click Me</button>
                <div id="result"></div>
            </section>

            <section id="about">
                <h2>About</h2>
                <p>This webpage was automatically generated by the Super Agent.</p>
                <div class="features">
                    <div class="feature">
                        <h3>Feature 1</h3>
                        <p>Description of feature 1</p>
                    </div>
                    <div class="feature">
                        <h3>Feature 2</h3>
                        <p>Description of feature 2</p>
                    </div>
                    <div class="feature">
                        <h3>Feature 3</h3>
                        <p>Description of feature 3</p>
                    </div>
                </div>
            </section>

            <section id="contact">
                <h2>Contact</h2>
                <form id="contactForm">
                    <div class="form-group">
                        <label for="name">Name</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="message">Message</label>
                        <textarea id="message" name="message" rows="5" required></textarea>
                    </div>
                    <button type="submit">Send Message</button>
                </form>
            </section>
        </main>

        <footer>
            <p>&copy; 2023 Generated Webpage. All rights reserved.</p>
        </footer>
    </div>

    <script src="app.js"></script>
</body>
</html>"""

        # Basic CSS template
        css = """/* Reset and base styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header styles */
header {
    background-color: #333;
    color: #fff;
    padding: 20px 0;
}

header h1 {
    margin-bottom: 10px;
}

nav ul {
    display: flex;
    list-style: none;
}

nav ul li {
    margin-right: 20px;
}

nav ul li a {
    color: #fff;
    text-decoration: none;
    transition: color 0.3s;
}

nav ul li a:hover {
    color: #f8f8f8;
}

/* Main content styles */
main {
    padding: 40px 0;
}

section {
    margin-bottom: 40px;
}

h2 {
    margin-bottom: 20px;
    color: #333;
}

p {
    margin-bottom: 15px;
}

button {
    background-color: #333;
    color: #fff;
    border: none;
    padding: 10px 20px;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #555;
}

#result {
    margin-top: 20px;
    padding: 15px;
    background-color: #f0f0f0;
    border-radius: 5px;
    display: none;
}

/* Features section */
.features {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    margin-top: 20px;
}

.feature {
    flex-basis: calc(33.333% - 20px);
    background-color: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.feature h3 {
    margin-bottom: 10px;
    color: #333;
}

/* Contact form */
.form-group {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 5px;
}

input, textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
}

/* Footer styles */
footer {
    background-color: #333;
    color: #fff;
    text-align: center;
    padding: 20px 0;
}

/* Responsive styles */
@media (max-width: 768px) {
    .features {
        flex-direction: column;
    }

    .feature {
        flex-basis: 100%;
        margin-bottom: 20px;
    }

    nav ul {
        flex-direction: column;
    }

    nav ul li {
        margin-right: 0;
        margin-bottom: 10px;
    }
}"""

        # Basic JS template
        js = """document.addEventListener('DOMContentLoaded', function() {
    // Get references to elements
    const actionButton = document.getElementById('actionButton');
    const resultDiv = document.getElementById('result');
    const contactForm = document.getElementById('contactForm');

    // Add click event listener to the action button
    if (actionButton) {
        actionButton.addEventListener('click', function() {
            // Show the result div
            if (resultDiv) {
                resultDiv.style.display = 'block';
                resultDiv.textContent = 'Button clicked at ' + new Date().toLocaleTimeString();

                // Add a fade-in effect
                resultDiv.style.opacity = '0';
                resultDiv.style.transition = 'opacity 0.5s ease';

                setTimeout(function() {
                    resultDiv.style.opacity = '1';
                }, 10);
            }
        });
    }

    // Add submit event listener to the contact form
    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            // Prevent the default form submission
            event.preventDefault();

            // Get form values
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const message = document.getElementById('message').value;

            // Validate form (simple validation)
            if (!name || !email || !message) {
                alert('Please fill in all fields');
                return;
            }

            // In a real application, you would send this data to a server
            // For now, just show a success message
            alert(`Thank you, ${name}! Your message has been received.`);

            // Reset the form
            contactForm.reset();
        });
    }

    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            // Get the target section
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);

            if (targetSection) {
                event.preventDefault();

                // Scroll smoothly to the target section
                targetSection.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});"""

        # Create a preview image (SVG as base64)
        preview_svg = """<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#ffffff"/>
            <rect x="0" y="0" width="100%" height="60" fill="#333333"/>
            <text x="20" y="35" font-family="Arial" font-size="16" fill="white">Website Preview</text>
            <rect x="20" y="80" width="760" height="100" fill="#f0f0f0"/>
            <text x="40" y="120" font-family="Arial" font-size="24" fill="#333333">Welcome</text>
            <rect x="20" y="200" width="760" height="300" fill="#f8f8f8"/>
            <text x="40" y="240" font-family="Arial" font-size="18" fill="#333333">Content Area</text>
            <rect x="0" y="520" width="100%" height="80" fill="#333333"/>
        </svg>"""

        # Convert SVG to base64
        svg_bytes = preview_svg.encode('utf-8')
        base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
        preview_url = f"data:image/svg+xml;base64,{base64_svg}"

        # Return the generated files and preview
        return {
            "files": {
                "index.html": html,
                "styles.css": css,
                "app.js": js
            },
            "preview": preview_url,
            "type": "webpage"
        }

    def _generate_diagram_fallback(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a diagram locally when MCP server is unavailable.

        Args:
            requirements: The requirements dictionary

        Returns:
            The generated diagram
        """
        description = requirements["description"]
        diagram_type = requirements["diagram_type"]

        # Generate diagram code based on type
        if diagram_type == "flowchart":
            code = "```mermaid\nflowchart TD\n"
            code += "    A[Start] --> B[Process]\n"
            code += "    B --> C{Decision}\n"
            code += "    C -->|Yes| D[Action 1]\n"
            code += "    C -->|No| E[Action 2]\n"
            code += "    D --> F[End]\n"
            code += "    E --> F\n"
            code += "```"
        elif diagram_type == "sequence":
            code = "```mermaid\nsequenceDiagram\n"
            code += "    participant User\n"
            code += "    participant System\n"
            code += "    participant Database\n\n"
            code += "    User->>System: Request Data\n"
            code += "    System->>Database: Query Data\n"
            code += "    Database-->>System: Return Results\n"
            code += "    System-->>User: Display Results\n"
            code += "```"
        elif diagram_type == "class":
            code = "```mermaid\nclassDiagram\n"
            code += "    class User {\n"
            code += "        +String username\n"
            code += "        +String email\n"
            code += "        +login()\n"
            code += "        +logout()\n"
            code += "    }\n\n"
            code += "    class Product {\n"
            code += "        +String name\n"
            code += "        +Number price\n"
            code += "        +getDetails()\n"
            code += "    }\n\n"
            code += "    User --> Product: purchases\n"
            code += "```"
        elif diagram_type == "entity-relationship":
            code = "```mermaid\nerDiagram\n"
            code += "    CUSTOMER ||--o{ ORDER : places\n"
            code += "    ORDER ||--|{ LINE-ITEM : contains\n"
            code += "    CUSTOMER }|..|{ DELIVERY-ADDRESS : uses\n"
            code += "```"
        else:
            # Default to flowchart for other types
            code = "```mermaid\nflowchart TD\n"
            code += "    A[Start] --> B[Process]\n"
            code += "    B --> C{Decision}\n"
            code += "    C -->|Yes| D[Action 1]\n"
            code += "    C -->|No| E[Action 2]\n"
            code += "    D --> F[End]\n"
            code += "    E --> F\n"
            code += "```"

        # Create a preview image (SVG as base64)
        preview_svg = f"""<svg width="500" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f0f0f0"/>
            <text x="50%" y="50%" font-family="Arial" font-size="16" text-anchor="middle">
                {diagram_type.capitalize()} Diagram Preview
            </text>
            <text x="50%" y="70%" font-family="monospace" font-size="12" text-anchor="middle">
                (Diagram visualization would be shown here)
            </text>
        </svg>"""

        # Convert SVG to base64
        svg_bytes = preview_svg.encode('utf-8')
        base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
        preview_url = f"data:image/svg+xml;base64,{base64_svg}"

        # Return the generated diagram and preview
        return {
            "code": code,
            "image": preview_url,
            "type": diagram_type
        }

    def _generate_pdf_fallback(self, requirements: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        Generate a PDF locally when MCP server is unavailable.

        Args:
            requirements: The requirements dictionary
            content: The PDF content

        Returns:
            The generated PDF
        """
        title = requirements["description"]

        # Create a preview image (SVG as base64)
        preview_svg = """<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#ffffff"/>
            <rect x="0" y="0" width="100%" height="60" fill="#f0f0f0"/>
            <text x="20" y="35" font-family="Arial" font-size="16" fill="#333333">PDF Preview</text>
            <rect x="20" y="80" width="760" height="500" fill="#ffffff" stroke="#cccccc" stroke-width="1"/>
            <text x="400" y="300" font-family="Arial" font-size="24" fill="#333333" text-anchor="middle">PDF Document Preview</text>
        </svg>"""

        # Convert SVG to base64
        svg_bytes = preview_svg.encode('utf-8')
        base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
        preview_url = f"data:image/svg+xml;base64,{base64_svg}"

        # Create a minimal PDF (just a placeholder)
        pdf_data = b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 22>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Placeholder PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n284\n%%EOF'
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

        # Return the generated PDF and preview
        return {
            "title": title,
            "preview": preview_url,
            "pdf_base64": pdf_base64
        }