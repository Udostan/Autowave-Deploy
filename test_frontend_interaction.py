#!/usr/bin/env python3
"""
Test script for interacting with the Live Browser frontend.
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def test_frontend_interaction():
    """
    Test the frontend interaction with the Live Browser.
    """
    print("Starting frontend interaction test...")
    
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
        status_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "browser-status"))
        )
        
        if "not running" in status_element.text.lower():
            print("Browser is not running. Starting browser...")
            start_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "live-browser-start"))
            )
            start_button.click()
            
            # Wait for the browser to start
            time.sleep(5)
        
        # Enter a complex task
        complex_task = "Go to Wikipedia, search for quantum computing, and find the section about quantum algorithms"
        print(f"Entering complex task: {complex_task}")
        
        task_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "live-browser-task"))
        )
        task_input.clear()
        task_input.send_keys(complex_task)
        
        # Click the execute task button
        print("Clicking execute task button...")
        execute_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "live-browser-execute-task"))
        )
        execute_button.click()
        
        # Wait for the task to complete (up to 60 seconds)
        print("Waiting for task to complete...")
        max_wait_time = 60
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                progress_text = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, "live-browser-progress-text"))
                )
                
                if "Task execution completed" in progress_text.text:
                    print("Task execution completed!")
                    print("\nExecution log:")
                    print(progress_text.text)
                    break
                
                print("Task still in progress...")
                time.sleep(5)
            except:
                print("Could not find progress text element.")
                time.sleep(5)
        
        if time.time() - start_time >= max_wait_time:
            print("Timed out waiting for task to complete.")
        
        # Take a screenshot of the result
        print("Taking screenshot of the result...")
        driver.save_screenshot("live_browser_test_result.png")
        print("Screenshot saved to live_browser_test_result.png")
        
        # Wait a moment to see the final state
        time.sleep(5)
        
    finally:
        # Close the browser
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    test_frontend_interaction()
