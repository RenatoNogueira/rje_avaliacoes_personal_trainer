import sys
import os
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add current directory to sys.path
sys.path.append(str(Path.cwd()))

from utils.updater import Updater
import version

class MockMaster:
    pass

def test_updater_with_mock():
    print("--- Starting Mocked Update Check Test ---")
    
    # Mock version to be older than the remote one
    version.__version__ = "1.0.18"
    
    master = MockMaster()
    updater = Updater(master)
    
    # Prepare mock API response
    mock_response_data = {
        "tag_name": "v1.0.19",
        "body": "Fixed critical bugs and improved performance.",
        "assets": [
            {
                "name": "RJE_Avaliacoes_v1.0.19.zip",
                "url": "https://api.github.com/repos/RenatoNogueira/rje_avaliacoes_personal_trainer/releases/assets/12345"
            }
        ],
        "zipball_url": "https://api.github.com/repos/RenatoNogueira/rje_avaliacoes_personal_trainer/zipball/v1.0.19"
    }
    
    # Mock urllib.request.urlopen
    with patch('urllib.request.urlopen') as mock_urlopen:
        # Configure mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Mock sys.frozen to simulate EXE mode
        with patch('sys.frozen', True, create=True):
            print("\nSimulating EXE mode (sys.frozen = True):")
            updater._check_worker(lambda available: print(f"  Update available: {available}"))
            print(f"  Latest version found: {updater.latest_version}")
            print(f"  Download URL: {updater.download_url}")
            assert updater.latest_version == "1.0.19"
            assert "assets/12345" in updater.download_url
            
        # Mock sys.frozen to simulate Source mode
        with patch('sys.frozen', False, create=True):
            print("\nSimulating Source mode (sys.frozen = False):")
            # Reset updater search state
            updater.download_url = None
            updater._check_worker(lambda available: print(f"  Update available: {available}"))
            print(f"  Latest version found: {updater.latest_version}")
            print(f"  Download URL: {updater.download_url}")
            assert updater.latest_version == "1.0.19"
            assert "zipball" in updater.download_url

    print("\n--- Mock Test Completed Successfully ---")

if __name__ == "__main__":
    try:
        test_updater_with_mock()
    except Exception as e:
        print(f"\nTest FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
