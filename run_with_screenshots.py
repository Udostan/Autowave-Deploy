"""
Run the application with screenshots enabled.

This script runs the application with screenshots enabled, regardless of hardware.
"""

import os
import sys

# Set environment variables to enable screenshots
os.environ['DISABLE_SCREENSHOTS'] = 'false'
os.environ['DISABLE_SCREEN_RECORDING'] = 'false'
os.environ['SCREENSHOT_INTERVAL_MS'] = '300'  # 3 FPS
os.environ['LIGHTWEIGHT_MODE'] = 'false'

# Import and run the application
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import main

if __name__ == '__main__':
    main()
