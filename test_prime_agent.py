#!/usr/bin/env python3
"""
Test script for the Prime Agent.
"""

import requests
import json
import time
import sys

def test_prime_agent():
    """
    Test the Prime Agent functionality.
    """
    print("Starting Prime Agent test...")

    # Define the API endpoint
    api_url = "http://localhost:5001/api/super-agent/execute-task"

    # Define the task
    task = "Research the current Amazon stock price and analyze its performance over the past 3 months. Include price trends, major events affecting the stock, and expert predictions for the next quarter."

    # Define the session ID
    session_id = "test-session-" + str(int(time.time()))

    # Define the request payload
    payload = {
        "task": task,
        "session_id": session_id
    }

    # Send the request
    print(f"Sending task to Prime Agent: {task}")
    try:
        response = requests.post(api_url, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            print("Task submitted successfully!")
            print(f"Response: {response.json()}")

            # Poll for task status
            status_url = f"http://localhost:5001/api/super-agent/task-status?session_id={session_id}"

            print("Polling for task status...")
            max_polls = 30
            poll_count = 0

            while poll_count < max_polls:
                poll_count += 1

                try:
                    status_response = requests.get(status_url)

                    if status_response.status_code == 200:
                        status_data = status_response.json()

                        print(f"Status: {status_data.get('status')}")

                        # Check if the task is complete
                        if status_data.get('status') == 'complete':
                            print("Task completed!")

                            # Get the task summary
                            task_summary = status_data.get('task_summary', '')

                            # Check if the task summary contains image HTML
                            if '<div class="image-container"' in task_summary:
                                print("Task summary contains image HTML!")

                                # Check if the image HTML is properly formatted
                                if '<img src="' in task_summary and 'style="max-width:100%' in task_summary:
                                    print("Image HTML is properly formatted!")

                                    # Save the task summary to a file for inspection
                                    with open("task_summary.html", "w") as f:
                                        f.write(task_summary)

                                    print("Task summary saved to task_summary.html")
                                else:
                                    print("Image HTML is not properly formatted!")
                            else:
                                print("Task summary does not contain image HTML!")

                                # Save the task summary to a file for inspection
                                with open("task_summary.html", "w") as f:
                                    f.write(task_summary)

                                print("Task summary saved to task_summary.html")

                            break

                        # If the task is still in progress, wait and try again
                        print("Task still in progress, waiting...")
                        time.sleep(2)
                    else:
                        print(f"Error getting task status: {status_response.status_code}")
                        print(f"Response: {status_response.text}")
                        break
                except Exception as e:
                    print(f"Error polling for task status: {str(e)}")
                    break

            if poll_count >= max_polls:
                print("Timed out waiting for task to complete!")
        else:
            print(f"Error submitting task: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error sending request: {str(e)}")

    print("Test completed!")

if __name__ == "__main__":
    test_prime_agent()
