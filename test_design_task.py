#!/usr/bin/env python3
"""
Test script for the design task functionality.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

from app.agents.tasks.design_task import DesignTask
from app.utils.web_browser import WebBrowser

def test_webpage_design():
    """Test the webpage design functionality."""
    print("Testing webpage design...")
    
    task = DesignTask(
        task_description="Create a simple webpage for a coffee shop with a menu and contact form",
        web_browser=WebBrowser()
    )
    
    result = task.execute()
    
    print(f"Success: {result['success']}")
    print(f"Steps: {len(result['steps'])}")
    print(f"Step summaries: {len(result['step_summaries'])}")
    
    # Print the task summary
    print("\nTask Summary:")
    print(result['task_summary'][:500] + "...\n")
    
    return result

def test_diagram_design():
    """Test the diagram design functionality."""
    print("Testing diagram design...")
    
    task = DesignTask(
        task_description="Create a flowchart diagram for a user registration process",
        web_browser=WebBrowser()
    )
    
    result = task.execute()
    
    print(f"Success: {result['success']}")
    print(f"Steps: {len(result['steps'])}")
    print(f"Step summaries: {len(result['step_summaries'])}")
    
    # Print the task summary
    print("\nTask Summary:")
    print(result['task_summary'][:500] + "...\n")
    
    return result

def test_pdf_design():
    """Test the PDF design functionality."""
    print("Testing PDF design...")
    
    task = DesignTask(
        task_description="Create a PDF document about the benefits of exercise",
        web_browser=WebBrowser()
    )
    
    result = task.execute()
    
    print(f"Success: {result['success']}")
    print(f"Steps: {len(result['steps'])}")
    print(f"Step summaries: {len(result['step_summaries'])}")
    
    # Print the task summary
    print("\nTask Summary:")
    print(result['task_summary'][:500] + "...\n")
    
    return result

def main():
    """Run the tests."""
    # Test webpage design
    webpage_result = test_webpage_design()
    
    # Test diagram design
    diagram_result = test_diagram_design()
    
    # Test PDF design
    pdf_result = test_pdf_design()
    
    # Print overall results
    print("Overall Results:")
    print(f"Webpage design: {'Success' if webpage_result['success'] else 'Failure'}")
    print(f"Diagram design: {'Success' if diagram_result['success'] else 'Failure'}")
    print(f"PDF design: {'Success' if pdf_result['success'] else 'Failure'}")

if __name__ == "__main__":
    main()
