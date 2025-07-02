#!/usr/bin/env python3
"""
Test script for the Live Browser frontend step-by-step execution.
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def test_frontend_step_by_step():
    """
    Test the frontend step-by-step execution with a complex prompt.
    """
    print("Starting frontend step-by-step test...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Create a new Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navigate to the Live Browser page
        print("Navigating to Live Browser page...")
        driver.get("http://localhost:5009/live-browser")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "live-browser-task"))
        )
        
        # Check if the browser is running
        print("Checking if browser is running...")
        try:
            status_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "browser-status"))
            )
            
            if "not running" in status_element.text.lower():
                print("Browser is not running. Starting browser...")
                start_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "live-browser-start"))
                )
                start_button.click()
                
                # Wait for the browser to start
                time.sleep(5)
        except:
            print("Could not find browser status element. Assuming browser is running.")
        
        # Enter a complex task
        complex_task = "Go to Wikipedia, search for quantum computing, and find the section about quantum algorithms"
        print(f"Entering complex task: {complex_task}")
        
        task_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "live-browser-task"))
        )
        task_input.clear()
        task_input.send_keys(complex_task)
        
        # Take a screenshot before clicking the button
        screenshots_dir = "test_screenshots"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        
        driver.save_screenshot(f"{screenshots_dir}/before_execution.png")
        print(f"Screenshot saved to {screenshots_dir}/before_execution.png")
        
        # Click the execute task button
        print("Clicking execute task button...")
        execute_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "live-browser-execute-task"))
        )
        execute_button.click()
        
        # Wait for the task to start processing
        time.sleep(2)
        driver.save_screenshot(f"{screenshots_dir}/execution_started.png")
        print(f"Screenshot saved to {screenshots_dir}/execution_started.png")
        
        # Wait for the task to complete (up to 60 seconds)
        print("Waiting for task to complete...")
        max_wait_time = 60
        start_time = time.time()
        
        progress_updates = []
        
        while time.time() - start_time < max_wait_time:
            try:
                # Look for the progress text element
                progress_element = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, "live-browser-progress-text"))
                )
                
                current_progress = progress_element.text
                
                # Check if we have a new progress update
                if current_progress and current_progress not in progress_updates:
                    progress_updates.append(current_progress)
                    print(f"Progress update: {len(progress_updates)}")
                    
                    # Take a screenshot of the progress
                    driver.save_screenshot(f"{screenshots_dir}/progress_{len(progress_updates)}.png")
                    print(f"Screenshot saved to {screenshots_dir}/progress_{len(progress_updates)}.png")
                
                # Check if task is completed
                if "Task execution completed" in current_progress:
                    print("Task execution completed!")
                    break
                
                time.sleep(2)
            except Exception as e:
                print(f"Error checking progress: {str(e)}")
                time.sleep(2)
        
        # Take a final screenshot
        driver.save_screenshot(f"{screenshots_dir}/final_result.png")
        print(f"Final screenshot saved to {screenshots_dir}/final_result.png")
        
        # Print all progress updates
        print("\nProgress Updates:")
        for i, update in enumerate(progress_updates):
            print(f"\n--- Update {i+1} ---")
            print(update)
        
        if time.time() - start_time >= max_wait_time:
            print("Timed out waiting for task to complete.")
        
        # Wait a moment to see the final state
        time.sleep(5)
        
    finally:
        # Close the browser
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    test_frontend_step_by_step()
