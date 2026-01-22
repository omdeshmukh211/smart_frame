"""
System Controls Module
Handles system-level controls like volume and brightness.
"""

import subprocess
import os

# Path to scripts directory
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'scripts')


def set_volume(percent: int) -> bool:
    """
    Set the system volume.
    
    Args:
        percent: Volume level (0-100)
        
    Returns:
        True if volume was set successfully
    """
    # Clamp to valid range
    percent = max(0, min(100, percent))
    
    try:
        script_path = os.path.join(SCRIPTS_DIR, 'set_volume.sh')
        
        result = subprocess.run(
            ['/bin/bash', script_path, str(percent)],
            capture_output=True,
            timeout=5
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error setting volume: {e}")
        return False


def set_brightness(percent: int) -> bool:
    """
    Set the display brightness.
    
    Args:
        percent: Brightness level (0-100)
        
    Returns:
        True if brightness was set successfully
    """
    # Clamp to valid range
    percent = max(0, min(100, percent))
    
    try:
        # Use xrandr for brightness control (common on Linux)
        # Adjust the output name as needed for your system
        brightness_value = percent / 100.0
        
        result = subprocess.run(
            ['xrandr', '--output', 'HDMI-1', '--brightness', str(brightness_value)],
            capture_output=True,
            timeout=5
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error setting brightness: {e}")
        return False


def get_volume() -> int:
    """
    Get the current system volume.
    
    Returns:
        Current volume level (0-100) or -1 on error
    """
    try:
        result = subprocess.run(
            ['amixer', 'get', 'Master'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse output to extract volume percentage
            output = result.stdout
            # Look for pattern like [70%]
            import re
            match = re.search(r'\[(\d+)%\]', output)
            if match:
                return int(match.group(1))
        
        return -1
    except Exception as e:
        print(f"Error getting volume: {e}")
        return -1


def get_brightness() -> int:
    """
    Get the current display brightness.
    
    Returns:
        Current brightness level (0-100) or -1 on error
    """
    try:
        result = subprocess.run(
            ['xrandr', '--verbose'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse output to extract brightness
            import re
            match = re.search(r'Brightness:\s*([\d.]+)', result.stdout)
            if match:
                return int(float(match.group(1)) * 100)
        
        return -1
    except Exception as e:
        print(f"Error getting brightness: {e}")
        return -1


def set_bluetooth(enabled: bool) -> bool:
    """
    Enable or disable Bluetooth.
    
    Args:
        enabled: True to enable, False to disable
        
    Returns:
        True if bluetooth was toggled successfully
    """
    try:
        action = 'power on' if enabled else 'power off'
        
        # Use bluetoothctl to control bluetooth
        result = subprocess.run(
            ['bluetoothctl', action],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return True
        
        # Fallback: use rfkill
        rfkill_action = 'unblock' if enabled else 'block'
        result = subprocess.run(
            ['rfkill', rfkill_action, 'bluetooth'],
            capture_output=True,
            timeout=5
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error toggling bluetooth: {e}")
        return False


def get_bluetooth_status() -> bool:
    """
    Get the current Bluetooth status.
    
    Returns:
        True if bluetooth is enabled, False otherwise
    """
    try:
        result = subprocess.run(
            ['bluetoothctl', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return 'Powered: yes' in result.stdout
        
        return False
    except Exception as e:
        print(f"Error getting bluetooth status: {e}")
        return False
