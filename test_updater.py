import sys
import os
from pathlib import Path

# Add current directory to sys.path to import local modules
sys.path.append(str(Path.cwd()))

from utils.updater import Updater
from version import __version__

class MockMaster:
    pass

def test_callback(update_available):
    print(f"\n--- Test Result ---")
    print(f"Update available: {update_available}")
    if updater.latest_version:
        print(f"Latest version found: {updater.latest_version}")
        print(f"Current version: {updater.current_version}")
        print(f"Download URL: {updater.download_url}")
        print(f"Release Notes: {updater.release_notes[:100]}...")
    else:
        print("No version found (error or no releases).")

if __name__ == "__main__":
    print(f"Starting update check test...")
    print(f"Local version: {__version__}")
    
    master = MockMaster()
    updater = Updater(master)
    
    # Manually trigger the worker to see output
    updater._check_worker(test_callback)
