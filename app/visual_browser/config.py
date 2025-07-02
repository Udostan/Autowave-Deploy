"""
Configuration for the Visual Browser.

This module provides configuration options for the Visual Browser.
"""

import os
import platform
import psutil

# Detect system capabilities
SYSTEM_INFO = {
    'platform': platform.system(),
    'platform_version': platform.version(),
    'processor': platform.processor(),
    'memory_gb': round(psutil.virtual_memory().total / (1024 ** 3), 2),
    'is_old_hardware': False,  # Will be set based on detection
}

# Check if this is older hardware (like Mac 2015)
if SYSTEM_INFO['platform'] == 'Darwin':
    # Check macOS version
    try:
        mac_version = float('.'.join(platform.mac_ver()[0].split('.')[:2]))
        if mac_version < 10.15:  # Older than Catalina
            SYSTEM_INFO['is_old_hardware'] = True
    except:
        pass

    # Check memory
    if SYSTEM_INFO['memory_gb'] < 8:
        SYSTEM_INFO['is_old_hardware'] = True

    # Check processor
    if 'Intel' in SYSTEM_INFO['processor'] and any(x in SYSTEM_INFO['processor'] for x in ['i3', 'i5']):
        SYSTEM_INFO['is_old_hardware'] = True

# Configuration for browser
BROWSER_CONFIG = {
    # Lightweight mode is automatically enabled for old hardware, but can be overridden by env var
    'lightweight_mode': False if os.environ.get('LIGHTWEIGHT_MODE', '').lower() == 'false' else (SYSTEM_INFO['is_old_hardware'] or os.environ.get('LIGHTWEIGHT_MODE', '').lower() in ('1', 'true', 'yes')),

    # Screenshot settings
    'screenshot_interval_ms': int(os.environ.get('SCREENSHOT_INTERVAL_MS', 1000 if SYSTEM_INFO['is_old_hardware'] else 300)),  # Use env var or default
    'disable_screenshots': False if os.environ.get('DISABLE_SCREENSHOTS', '').lower() == 'false' else os.environ.get('DISABLE_SCREENSHOTS', '').lower() in ('1', 'true', 'yes'),

    # Screen recording settings
    'disable_screen_recording': False if os.environ.get('DISABLE_SCREEN_RECORDING', '').lower() == 'false' else (SYSTEM_INFO['is_old_hardware'] or os.environ.get('DISABLE_SCREEN_RECORDING', '').lower() in ('1', 'true', 'yes')),

    # Browser window size
    'window_width': 800 if SYSTEM_INFO['is_old_hardware'] else 1280,
    'window_height': 600 if SYSTEM_INFO['is_old_hardware'] else 800,

    # Memory limits
    'memory_limit_mb': 512 if SYSTEM_INFO['is_old_hardware'] else 1024,

    # Task execution limits
    'max_steps': 5 if SYSTEM_INFO['is_old_hardware'] else 10,
    'execution_timeout_seconds': 30 if SYSTEM_INFO['is_old_hardware'] else 60,
    'step_timeout_seconds': 5 if SYSTEM_INFO['is_old_hardware'] else 15,

    # LLM settings
    'use_llm_for_tasks': not SYSTEM_INFO['is_old_hardware'] and os.environ.get('USE_LLM_FOR_TASKS', '').lower() in ('1', 'true', 'yes', ''),
    'llm_provider': os.environ.get('LLM_PROVIDER', 'gemini'),  # 'gemini' or 'groq'
    'llm_temperature': 0.2,  # Lower temperature for more deterministic results
}

# Print configuration
print(f"System Info: {SYSTEM_INFO}")
print(f"Browser Config: {BROWSER_CONFIG}")
