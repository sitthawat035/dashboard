import os
import subprocess
import sys
import time
from pathlib import Path

def launch_chrome_debug(port=9222, force_close=True):
    """
    Launch Google Chrome in debug mode for CDP connection.
    """
    if sys.platform != "win32":
        return False, "This script is currently only supported on Windows."

    # 1. Detect Chrome Path
    possible_paths = [
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    
    chrome_path = None
    for p in possible_paths:
        if p.exists():
            chrome_path = p
            break
            
    if not chrome_path:
        return False, "Chrome executable not found at common locations."

    # 2. Define User Data Dir (Standard Profile)
    # Using the default profile ensures cookies and sessions are available
    user_data_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data"

    # 3. Force Close Existing Chrome (Required for port 9222 to take effect)
    if force_close:
        try:
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
            time.sleep(1) # Wait for processes to die
        except:
            pass

    # 4. Launch Chrome
    try:
        # Use Popen to launch and detach
        args = [
            str(chrome_path),
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        
        # Launch without blocking
        # DETACHED_PROCESS = 0x00000008, CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(args, creationflags=0x00000008 | 0x00000200)
        
        return True, f"Chrome launched on port {port} using profile {user_data_dir}"
    except Exception as e:
        return False, f"Failed to launch Chrome: {str(e)}"

if __name__ == "__main__":
    success, message = launch_chrome_debug()
    print(f"{'✅' if success else '❌'} {message}")
