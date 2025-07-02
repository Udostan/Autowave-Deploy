# Live Browser - Lightweight Mode

This document explains how to use the Live Browser in lightweight mode to prevent system crashes on older hardware.

## Overview

The Live Browser has been updated to include a lightweight mode that significantly reduces resource usage, making it suitable for older hardware like Mac 2015 computers. This mode:

1. Limits memory usage
2. Disables resource-intensive features
3. Reduces the number of steps in task execution
4. Adds timeouts to prevent infinite loops
5. Optimizes browser settings for lower resource consumption

## Configuration

The lightweight mode is automatically enabled on older hardware, but you can manually control it using environment variables:

```bash
# Enable lightweight mode
export LIGHTWEIGHT_MODE=true

# Disable screenshots to further reduce resource usage
export DISABLE_SCREENSHOTS=true

# Disable screen recording
export DISABLE_SCREEN_RECORDING=true
```

## Resource Limits

The following resource limits are applied in lightweight mode:

- Memory limit: 512MB
- Maximum steps per task: 5
- Execution timeout: 30 seconds
- Step timeout: 5 seconds
- Screenshot interval: 1 second (vs 300ms in normal mode)
- Browser window size: 800x600 (vs 1280x800 in normal mode)

## Browser Optimizations

In lightweight mode, the browser is configured with the following optimizations:

- Disabled images
- Disabled 3D APIs
- Disabled accelerated canvas
- Disabled background networking
- Disabled various other resource-intensive features

## Using the Live Browser

When using the Live Browser in lightweight mode:

1. Keep tasks simple and concise
2. Avoid complex multi-step tasks
3. Be patient with task execution
4. Monitor system resource usage

## API Endpoints

The Live Browser API has been updated to support asynchronous task execution:

- `POST /api/live-browser/execute-task` - Execute a task and return a task ID
- `GET /api/live-browser/task-status/<task_id>` - Check the status of a task

## Troubleshooting

If you still experience system crashes:

1. Try setting `DISABLE_SCREENSHOTS=true` and `DISABLE_SCREEN_RECORDING=true`
2. Reduce the number of browser tabs and applications running
3. Restart the application
4. If all else fails, consider using a more powerful computer

## Example Usage

```python
# Execute a simple task
response = requests.post('http://localhost:5009/api/live-browser/execute-task', json={
    'task_type': 'natural_language',
    'task_data': {
        'task': 'Go to Google and search for Python programming'
    }
})

# Get the task ID
task_id = response.json()['task_id']

# Check the task status
response = requests.get(f'http://localhost:5009/api/live-browser/task-status/{task_id}')
status = response.json()
```
