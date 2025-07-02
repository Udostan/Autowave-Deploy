"""
Design Tools for MCP Server.
These tools handle code generation, diagram creation, and other design tasks.
"""

import logging
import json
import base64
import re
import os
import tempfile
import subprocess
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DesignTools:
    """
    Tools for generating code, diagrams, and other design artifacts.
    """
    
    def __init__(self):
        """Initialize the design tools."""
        self.logger = logging.getLogger(__name__)
        
        # Load API keys from environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize supported diagram types
        self.diagram_types = {
            "flowchart": self._generate_mermaid_flowchart,
            "sequence": self._generate_mermaid_sequence,
            "class": self._generate_mermaid_class,
            "entity-relationship": self._generate_mermaid_er,
            "gantt": self._generate_mermaid_gantt,
            "pie": self._generate_mermaid_pie,
            "mindmap": self._generate_mermaid_mindmap,
            "uml": self._generate_plantuml
        }
    
    def generate_webpage(self, description: str, complexity: str = "medium") -> Dict[str, Any]:
        """
        Generate a complete webpage based on a description.
        
        Args:
            description: Description of the webpage to generate
            complexity: Complexity level (simple, medium, complex)
            
        Returns:
            Dictionary containing HTML, CSS, and JS code
        """
        self.logger.info(f"Generating webpage: {description} (complexity: {complexity})")
        
        # Generate the files
        files = self._generate_web_files(description, complexity)
        
        # Generate a preview image
        preview_image = self._generate_html_preview(files.get("index.html", ""), 
                                                   files.get("styles.css", ""),
                                                   files.get("app.js", ""))
        
        return {
            "files": files,
            "preview": preview_image,
            "type": "webpage"
        }
    
    def generate_diagram(self, description: str, diagram_type: str = "flowchart") -> Dict[str, Any]:
        """
        Generate a diagram based on a description.
        
        Args:
            description: Description of the diagram to generate
            diagram_type: Type of diagram (flowchart, sequence, class, etc.)
            
        Returns:
            Dictionary containing diagram code and rendered image
        """
        self.logger.info(f"Generating {diagram_type} diagram: {description}")
        
        # Normalize diagram type
        diagram_type = diagram_type.lower().strip()
        
        # Map common terms to supported types
        diagram_type_mapping = {
            "flow": "flowchart",
            "flow chart": "flowchart",
            "sequence diagram": "sequence",
            "class diagram": "class",
            "er diagram": "entity-relationship",
            "entity relationship": "entity-relationship",
            "gantt chart": "gantt",
            "pie chart": "pie",
            "mind map": "mindmap",
            "uml diagram": "uml"
        }
        
        # Apply mapping if needed
        if diagram_type in diagram_type_mapping:
            diagram_type = diagram_type_mapping[diagram_type]
        
        # Default to flowchart if type not supported
        if diagram_type not in self.diagram_types:
            self.logger.warning(f"Diagram type '{diagram_type}' not supported, defaulting to flowchart")
            diagram_type = "flowchart"
        
        # Generate the diagram code
        generator_func = self.diagram_types[diagram_type]
        diagram_code = generator_func(description)
        
        # Render the diagram to an image
        diagram_image = self._render_diagram(diagram_code, diagram_type)
        
        return {
            "code": diagram_code,
            "image": diagram_image,
            "type": diagram_type
        }
    
    def generate_pdf(self, content: str, title: str = "Generated PDF") -> Dict[str, Any]:
        """
        Generate a PDF document based on content.
        
        Args:
            content: Markdown content for the PDF
            title: Title of the PDF
            
        Returns:
            Dictionary containing PDF data and preview image
        """
        self.logger.info(f"Generating PDF: {title}")
        
        # Convert markdown to HTML
        html_content = self._markdown_to_html(content, title)
        
        # Generate PDF using a temporary HTML file
        pdf_data = self._html_to_pdf(html_content)
        
        # Generate a preview image of the first page
        preview_image = self._generate_pdf_preview(pdf_data)
        
        return {
            "pdf_base64": base64.b64encode(pdf_data).decode('utf-8'),
            "preview": preview_image,
            "title": title
        }
    
    def _generate_web_files(self, description: str, complexity: str) -> Dict[str, str]:
        """
        Generate HTML, CSS, and JS files for a webpage.
        
        Args:
            description: Description of the webpage
            complexity: Complexity level
            
        Returns:
            Dictionary of file contents
        """
        # For now, we'll use a template-based approach
        # In a production system, this would call an LLM API
        
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
        js = """// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
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
        
        # Return the generated files
        return {
            "index.html": html,
            "styles.css": css,
            "app.js": js
        }
    
    def _generate_mermaid_flowchart(self, description: str) -> str:
        """Generate Mermaid flowchart code based on description."""
        # This is a simplified implementation
        # In a production system, this would call an LLM API
        
        # Extract potential nodes from the description
        words = re.findall(r'\b[A-Z][a-z]+\b', description)
        nodes = list(set(words))[:5]  # Limit to 5 nodes for simplicity
        
        if len(nodes) < 2:
            nodes = ["Start", "Process", "Decision", "End"]
        
        # Generate flowchart code
        code = "```mermaid\nflowchart TD\n"
        
        # Add nodes
        for i, node in enumerate(nodes):
            code += f"    A{i}[{node}]\n"
        
        # Add connections
        for i in range(len(nodes) - 1):
            code += f"    A{i} --> A{i+1}\n"
        
        # Add a decision node if there are enough nodes
        if len(nodes) >= 4:
            code += f"    A1 --> A{len(nodes)-1}\n"
        
        code += "```"
        return code
    
    def _generate_mermaid_sequence(self, description: str) -> str:
        """Generate Mermaid sequence diagram code based on description."""
        # Simplified implementation
        actors = ["User", "System", "Database"]
        
        code = "```mermaid\nsequenceDiagram\n"
        for actor in actors:
            code += f"    participant {actor}\n"
        
        code += "    User->>System: Request Data\n"
        code += "    System->>Database: Query Data\n"
        code += "    Database-->>System: Return Results\n"
        code += "    System-->>User: Display Results\n"
        code += "```"
        return code
    
    def _generate_mermaid_class(self, description: str) -> str:
        """Generate Mermaid class diagram code based on description."""
        # Simplified implementation
        code = "```mermaid\nclassDiagram\n"
        code += "    class User {\n"
        code += "        +String username\n"
        code += "        +String email\n"
        code += "        +login()\n"
        code += "        +logout()\n"
        code += "    }\n"
        code += "    class Product {\n"
        code += "        +String name\n"
        code += "        +Number price\n"
        code += "        +getDetails()\n"
        code += "    }\n"
        code += "    User --> Product: purchases\n"
        code += "```"
        return code
    
    def _generate_mermaid_er(self, description: str) -> str:
        """Generate Mermaid entity-relationship diagram code based on description."""
        # Simplified implementation
        code = "```mermaid\nerDiagram\n"
        code += "    CUSTOMER ||--o{ ORDER : places\n"
        code += "    ORDER ||--|{ LINE-ITEM : contains\n"
        code += "    CUSTOMER }|..|{ DELIVERY-ADDRESS : uses\n"
        code += "```"
        return code
    
    def _generate_mermaid_gantt(self, description: str) -> str:
        """Generate Mermaid Gantt chart code based on description."""
        # Simplified implementation
        code = "```mermaid\ngantt\n"
        code += "    title Project Schedule\n"
        code += "    dateFormat  YYYY-MM-DD\n"
        code += "    section Planning\n"
        code += "    Research           :a1, 2023-01-01, 7d\n"
        code += "    Design             :a2, after a1, 5d\n"
        code += "    section Development\n"
        code += "    Implementation     :a3, after a2, 10d\n"
        code += "    Testing            :a4, after a3, 5d\n"
        code += "```"
        return code
    
    def _generate_mermaid_pie(self, description: str) -> str:
        """Generate Mermaid pie chart code based on description."""
        # Simplified implementation
        code = "```mermaid\npie\n"
        code += "    title Distribution\n"
        code += "    \"Category A\" : 42.5\n"
        code += "    \"Category B\" : 27.8\n"
        code += "    \"Category C\" : 29.7\n"
        code += "```"
        return code
    
    def _generate_mermaid_mindmap(self, description: str) -> str:
        """Generate Mermaid mindmap code based on description."""
        # Simplified implementation
        code = "```mermaid\nmindmap\n"
        code += "  root((Main Topic))\n"
        code += "    Topic 1\n"
        code += "      Subtopic 1.1\n"
        code += "      Subtopic 1.2\n"
        code += "    Topic 2\n"
        code += "      Subtopic 2.1\n"
        code += "      Subtopic 2.2\n"
        code += "```"
        return code
    
    def _generate_plantuml(self, description: str) -> str:
        """Generate PlantUML diagram code based on description."""
        # Simplified implementation
        code = "```plantuml\n"
        code += "@startuml\n"
        code += "class User {\n"
        code += "  +String username\n"
        code += "  +String email\n"
        code += "  +login()\n"
        code += "  +logout()\n"
        code += "}\n"
        code += "class Product {\n"
        code += "  +String name\n"
        code += "  +Number price\n"
        code += "  +getDetails()\n"
        code += "}\n"
        code += "User --> Product: purchases\n"
        code += "@enduml\n"
        code += "```"
        return code
    
    def _render_diagram(self, diagram_code: str, diagram_type: str) -> str:
        """
        Render a diagram to an image.
        
        Args:
            diagram_code: The diagram code (Mermaid or PlantUML)
            diagram_type: The type of diagram
            
        Returns:
            Base64-encoded image data
        """
        # For now, return a placeholder image
        # In a production system, this would use a rendering service
        
        # Extract the actual diagram code (remove markdown code block markers)
        code_pattern = r'```(?:mermaid|plantuml)?\n(.*?)```'
        match = re.search(code_pattern, diagram_code, re.DOTALL)
        if match:
            actual_code = match.group(1)
        else:
            actual_code = diagram_code
        
        # For now, return a placeholder image
        # In a production environment, you would use a proper rendering service
        placeholder_svg = f"""<svg width="500" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f0f0f0"/>
            <text x="50%" y="50%" font-family="Arial" font-size="16" text-anchor="middle">
                {diagram_type.capitalize()} Diagram Preview
            </text>
            <text x="50%" y="70%" font-family="monospace" font-size="12" text-anchor="middle">
                (Actual rendering would be implemented in production)
            </text>
        </svg>"""
        
        # Convert SVG to base64
        svg_bytes = placeholder_svg.encode('utf-8')
        base64_svg = base64.b64encode(svg_bytes).decode('utf-8')
        
        return f"data:image/svg+xml;base64,{base64_svg}"
    
    def _generate_html_preview(self, html: str, css: str, js: str) -> str:
        """
        Generate a preview image of an HTML page.
        
        Args:
            html: HTML content
            css: CSS content
            js: JavaScript content
            
        Returns:
            Base64-encoded image data
        """
        # For now, return a placeholder image
        # In a production system, this would use a headless browser
        
        # Create a simplified preview
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
        
        return f"data:image/svg+xml;base64,{base64_svg}"
    
    def _markdown_to_html(self, markdown: str, title: str) -> str:
        """Convert markdown to HTML."""
        # Simple conversion for now
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #444; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        code {{ font-family: monospace; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {self._simple_markdown_to_html(markdown)}
</body>
</html>"""
        return html
    
    def _simple_markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        # Convert headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', markdown, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Convert paragraphs (simple approach)
        paragraphs = html.split('\n\n')
        for i, p in enumerate(paragraphs):
            if not p.startswith('<h') and not p.startswith('<ul') and not p.startswith('<ol') and not p.startswith('<pre'):
                paragraphs[i] = f'<p>{p}</p>'
        
        html = '\n\n'.join(paragraphs)
        
        # Convert bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Convert code blocks
        html = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        
        return html
    
    def _html_to_pdf(self, html: str) -> bytes:
        """
        Convert HTML to PDF.
        
        Args:
            html: HTML content
            
        Returns:
            PDF data as bytes
        """
        # For now, return a placeholder PDF
        # In a production system, this would use a PDF generation library
        
        # Create a minimal PDF
        pdf_data = b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 612 792]/Resources<<>>/Contents 4 0 R/Parent 2 0 R>>\nendobj\n4 0 obj\n<</Length 22>>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Placeholder PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000212 00000 n\ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n284\n%%EOF'
        
        return pdf_data
    
    def _generate_pdf_preview(self, pdf_data: bytes) -> str:
        """
        Generate a preview image of a PDF.
        
        Args:
            pdf_data: PDF data
            
        Returns:
            Base64-encoded image data
        """
        # For now, return a placeholder image
        # In a production system, this would use a PDF rendering library
        
        # Create a simplified preview
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
        
        return f"data:image/svg+xml;base64,{base64_svg}"
