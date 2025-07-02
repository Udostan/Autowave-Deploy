"""
Test script for OpenManus integration.
This script simulates the OpenManus functionality without relying on the Flask server.
"""

import os
import sys
import json
import time
import webbrowser
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def simulate_openmanus_task(prompt):
    """
    Simulate the execution of an OpenManus task.
    
    Args:
        prompt: The task prompt.
        
    Returns:
        A dictionary with the task execution results.
    """
    print(f"Executing OpenManus task: {prompt}")
    
    # Simulate task execution steps
    print("Step 1: Analyzing task and planning execution steps...")
    time.sleep(1)
    
    print("Step 2: Gathering necessary information...")
    time.sleep(1)
    
    print("Step 3: Processing data and generating results...")
    time.sleep(1)
    
    print("Step 4: Task completed.")
    
    # Generate a sample result based on the prompt
    if "business plan" in prompt.lower():
        result = """
# Business Plan: SolarHome Solutions

## Executive Summary
SolarHome Solutions aims to revolutionize residential solar energy by providing affordable, efficient, and aesthetically pleasing solar panel systems for homeowners. Our innovative approach combines cutting-edge technology with simplified installation processes to reduce costs and increase adoption.

## Market Analysis
- The residential solar market is projected to grow at 15% annually through 2030
- Only 3% of eligible US homes currently have solar installations
- Primary barriers: upfront costs, aesthetic concerns, and installation complexity

## Product Offering
1. **SolarTile™ System**: Sleek, low-profile solar panels that integrate with existing roof designs
2. **SmartEnergy™ Hub**: AI-powered energy management system that optimizes energy usage
3. **Installation & Maintenance Services**: Professional installation and ongoing maintenance plans

## Financial Projections
- Year 1: $1.2M revenue, -$300K profit (investment phase)
- Year 3: $5.8M revenue, $1.2M profit
- Year 5: $12.4M revenue, $3.8M profit

## Funding Requirements
- Seed Round: $2.5M for product development and initial market entry
- Series A: $8M for scaling operations and expanding market reach

## Sustainability Impact
- Average customer will reduce carbon footprint by 8.5 tons CO2 annually
- 5-year goal: 50,000 installations, equivalent to planting 4.25 million trees

## Implementation Timeline
- Q1-Q2 2025: Product development and testing
- Q3 2025: Pilot program in California and Arizona
- Q1 2026: Full market launch in sunbelt states
- Q3 2026: Nationwide expansion

## Competitive Advantage
- Proprietary panel design with 22% efficiency (industry avg: 18%)
- Simplified installation reduces labor costs by 35%
- AI-powered energy management increases system value by 25%
"""
    elif "travel" in prompt.lower() or "trip" in prompt.lower():
        result = """
# Travel Itinerary: 7-Day Japan Adventure

## Overview
This comprehensive travel plan covers Tokyo, Kyoto, and Hakone, balancing urban exploration with natural beauty and cultural experiences.

## Day-by-Day Itinerary

### Day 1: Tokyo Arrival
- Morning: Arrive at Narita Airport, transfer to hotel in Shinjuku
- Afternoon: Explore Shinjuku area, visit Tokyo Metropolitan Government Building for city views
- Evening: Dinner at Omoide Yokocho (Memory Lane) for authentic yakitori

### Day 2: Tokyo Exploration
- Morning: Tsukiji Outer Market food tour
- Afternoon: Harajuku and Shibuya, including Meiji Shrine and Takeshita Street
- Evening: Shibuya Crossing and dinner at a local izakaya

### Day 3: Tokyo to Hakone
- Morning: Shinkansen to Hakone
- Afternoon: Hakone Open Air Museum
- Evening: Traditional ryokan stay with onsen (hot spring) experience

### Day 4: Hakone to Kyoto
- Morning: Hakone Ropeway with Mt. Fuji views
- Afternoon: Shinkansen to Kyoto
- Evening: Gion district walking tour, potential geisha sighting

### Day 5: Kyoto Temples
- Morning: Fushimi Inari Shrine (thousand torii gates)
- Afternoon: Kinkaku-ji (Golden Pavilion) and Ryoan-ji Zen garden
- Evening: Pontocho Alley for dinner

### Day 6: Kyoto Cultural Day
- Morning: Arashiyama Bamboo Grove and monkey park
- Afternoon: Traditional tea ceremony experience
- Evening: Kaiseki dinner (traditional multi-course meal)

### Day 7: Departure
- Morning: Final shopping in Kyoto
- Afternoon: Shinkansen to Tokyo
- Evening: Departure from Narita Airport

## Budget Breakdown
- Flights: $1,200 (round-trip from major US city)
- Accommodations: $1,400 (mix of hotels and one ryokan stay)
- Transportation: $300 (JR Pass and local transit)
- Food: $700 ($100/day)
- Activities: $400 (entrance fees and experiences)
- Miscellaneous: $200 (souvenirs, contingency)
- Total: $4,200

## Travel Tips
- Purchase a 7-day JR Pass before arriving in Japan
- Book the ryokan experience at least 3 months in advance
- Download Google Translate and a subway map app
- Bring comfortable walking shoes for temple visits
- Consider portable WiFi rental for navigation
"""
    else:
        result = """
# Task Analysis Report

## Overview
Based on your request, I've analyzed the key components and developed a comprehensive solution approach.

## Key Findings
- The task involves multiple interconnected systems
- Several technical challenges need to be addressed
- Implementation can be phased for optimal results

## Detailed Analysis

### Component 1: Primary Framework
The core system requires a robust architecture that supports:
- Scalable data processing
- Real-time analytics
- Secure user authentication

### Component 2: Integration Layer
Several integration points need to be established:
- API connections to external services
- Data synchronization mechanisms
- Event-driven communication protocols

## Recommendations

Based on my analysis, I recommend the following approach:

1. **Phase 1**: Foundation Development
   - Establish core architecture
   - Implement basic functionality
   - Set up testing framework

2. **Phase 2**: Feature Expansion
   - Add advanced capabilities
   - Optimize performance
   - Enhance user experience

3. **Phase 3**: Scaling & Refinement
   - Deploy to production environment
   - Implement monitoring systems
   - Gather user feedback for improvements

## Implementation Timeline
- Weeks 1-4: Architecture and planning
- Weeks 5-8: Core development
- Weeks 9-12: Testing and refinement
- Weeks 13-16: Deployment and monitoring

## Resource Requirements
- Development team: 3-5 engineers
- Infrastructure: Cloud-based deployment
- Testing: Automated test suite with CI/CD pipeline

## Next Steps
1. Finalize requirements specification
2. Establish development environment
3. Create project roadmap with milestones
4. Begin implementation of core components
"""
    
    return {
        "success": True,
        "task_id": "openmanus-task-123",
        "status": "completed",
        "result": result
    }

def create_html_result(prompt):
    """
    Create an HTML file with the OpenManus task results.
    
    Args:
        prompt: The task prompt.
        
    Returns:
        The path to the HTML file.
    """
    result = simulate_openmanus_task(prompt)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenManus Task Results</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body {{
            background-color: #121212;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .card {{
            background-color: #1e1e1e;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .card-header {{
            background-color: #ffffff;
            color: #000000;
            padding: 1rem;
            font-weight: bold;
        }}
        .card-body {{
            padding: 1.5rem;
        }}
        .prose {{
            color: #e0e0e0;
        }}
        .prose h1, .prose h2, .prose h3, .prose h4, .prose h5, .prose h6 {{
            color: #ffffff;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }}
        .prose h1 {{
            font-size: 1.875rem;
            border-bottom: 1px solid #333;
            padding-bottom: 0.5rem;
        }}
        .prose h2 {{
            font-size: 1.5rem;
            border-bottom: 1px solid #333;
            padding-bottom: 0.3rem;
        }}
        .prose h3 {{
            font-size: 1.25rem;
        }}
        .prose p {{
            margin-top: 1rem;
            margin-bottom: 1rem;
        }}
        .prose ul, .prose ol {{
            margin-top: 1rem;
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }}
        .prose li {{
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }}
        .prose blockquote {{
            border-left: 4px solid #333;
            padding-left: 1rem;
            margin-left: 0;
            color: #aaa;
        }}
        .prose code {{
            background-color: #2d2d2d;
            padding: 0.2rem 0.4rem;
            border-radius: 0.25rem;
            font-family: monospace;
        }}
        .prose pre {{
            background-color: #2d2d2d;
            padding: 1rem;
            border-radius: 0.25rem;
            overflow-x: auto;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }}
        .prose pre code {{
            background-color: transparent;
            padding: 0;
        }}
        .prose table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }}
        .prose th, .prose td {{
            border: 1px solid #333;
            padding: 0.5rem;
            text-align: left;
        }}
        .prose th {{
            background-color: #2d2d2d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-white mb-2">OpenManus Task Results</h1>
            <p class="text-gray-400">Task: {prompt}</p>
        </div>
        
        <div class="grid grid-cols-1 gap-6">
            <!-- Execution Log -->
            <div class="card">
                <div class="card-header">
                    <h2 class="text-xl">Execution Log</h2>
                </div>
                <div class="card-body">
                    <div class="prose max-w-none">
                        <p>Step 1: Analyzing task and planning execution steps...</p>
                        <p>Step 2: Gathering necessary information...</p>
                        <p>Step 3: Processing data and generating results...</p>
                        <p>Step 4: Task completed.</p>
                    </div>
                </div>
            </div>
            
            <!-- Results -->
            <div class="card">
                <div class="card-header">
                    <h2 class="text-xl">Results</h2>
                </div>
                <div class="card-body">
                    <div id="results" class="prose max-w-none">
                        <!-- Results will be rendered here -->
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Render the Markdown content
        document.addEventListener('DOMContentLoaded', function() {{
            const resultsElement = document.getElementById('results');
            const markdownContent = `{result['result'].replace('`', '\\`')}`;
            resultsElement.innerHTML = marked(markdownContent);
        }});
    </script>
</body>
</html>
    """
    
    # Save the HTML file
    output_path = os.path.join(os.path.dirname(__file__), 'openmanus_result.html')
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    return output_path

def main():
    """
    Main function to run the OpenManus test.
    """
    # Get the prompt from command line arguments or use a default prompt
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = "Create a comprehensive business plan for a sustainable energy startup focusing on solar panel technology for residential use"
    
    # Create the HTML result
    output_path = create_html_result(prompt)
    
    # Open the HTML file in a browser
    print(f"Opening result in browser: {output_path}")
    webbrowser.open(f"file://{output_path}")

if __name__ == "__main__":
    main()
