#!/usr/bin/env python3
"""
Test script for the Live Browser API step-by-step execution.
"""

import time
import json
import requests

def test_api_step_by_step():
    """
    Test the Live Browser API step-by-step execution with a complex prompt.
    """
    print("Starting API step-by-step test...")
    
    # Base URL for the API
    base_url = "http://localhost:5009/api/live-browser"
    
    # Step 1: Check if the browser is running
    print("Checking browser status...")
    response = requests.get(f"{base_url}/status")
    status_data = response.json()
    print(f"Status response: {json.dumps(status_data, indent=2)}")
    
    if not status_data.get("is_running", False):
        # Start the browser if it's not running
        print("Browser is not running. Starting browser...")
        response = requests.post(f"{base_url}/start")
        start_data = response.json()
        print(f"Start response: {json.dumps(start_data, indent=2)}")
        
        if not start_data.get("success", False):
            print(f"Failed to start browser: {start_data.get('error', 'Unknown error')}")
            return
        
        print("Browser started successfully")
        time.sleep(5)  # Wait for browser to initialize
    else:
        print("Browser is already running")
    
    # Step 2: Execute a complex task
    complex_task = "Go to Wikipedia, search for quantum computing, and find the section about quantum algorithms"
    print(f"Executing complex task: {complex_task}")
    
    response = requests.post(
        f"{base_url}/execute-task",
        json={
            "task_type": "natural_language",
            "task_data": {
                "task": complex_task
            }
        }
    )
    
    task_data = response.json()
    print(f"Task execution response: {json.dumps(task_data, indent=2)}")
    
    if not task_data.get("success", False):
        print(f"Failed to execute task: {task_data.get('error', 'Unknown error')}")
        return
    
    task_id = task_data.get("task_id")
    print(f"Task queued with ID: {task_id}")
    
    # Step 3: Poll for task status
    max_attempts = 60
    attempts = 0
    
    while attempts < max_attempts:
        print(f"Checking task status (attempt {attempts + 1}/{max_attempts})...")
        response = requests.get(f"{base_url}/task-status/{task_id}")
        status_data = response.json()
        
        if not status_data.get("success", False):
            print(f"Failed to get task status: {status_data.get('error', 'Unknown error')}")
            attempts += 1
            time.sleep(2)
            continue
        
        status = status_data.get("status")
        print(f"Task status: {status}")
        
        # Print progress
        progress = status_data.get("progress", [])
        for step in progress:
            print(f"- {step.get('message', 'No message')} ({step.get('timestamp', 'No timestamp')})")
        
        # Check if task is completed or has error
        if status in ["completed", "error"]:
            print(f"Task {status}")
            
            # Print result if available
            result = status_data.get("result")
            if result:
                print("\nTask Result:")
                print(f"Success: {result.get('success', False)}")
                print(f"Original Task: {result.get('original_task', 'N/A')}")
                print(f"Task Type: {result.get('task_type', 'N/A')}")
                print(f"Steps Executed: {result.get('steps_executed', 0)}/{result.get('total_steps', 0)}")
                
                # Print execution log
                execution_log = result.get("execution_log", [])
                if execution_log:
                    print("\nExecution Log:")
                    for i, step in enumerate(execution_log):
                        success = "✓" if step.get("success", False) else "✗"
                        action = step.get("action", "unknown")
                        message = step.get("message", "No details")
                        print(f"{i+1}. [{success}] {action}: {message}")
                
                # Print screenshots
                screenshots = result.get("screenshots", [])
                if screenshots:
                    print("\nScreenshots:")
                    for i, screenshot in enumerate(screenshots):
                        print(f"{i+1}. {screenshot}")
                        
                # Save the full result to a file
                with open("task_result.json", "w") as f:
                    json.dump(result, f, indent=2)
                print("\nFull result saved to task_result.json")
            
            break
        
        attempts += 1
        time.sleep(2)
    
    if attempts >= max_attempts:
        print("Timed out waiting for task to complete.")
    
    print("Test completed!")

if __name__ == "__main__":
    test_api_step_by_step()
