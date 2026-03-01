
import json
import urllib.request
import os
import sys
from pathlib import Path

# Simulating Updater variables
GITHUB_REPO = "RenatoNogueira/rje_avaliacoes_personal_trainer"
GITHUB_TOKEN = "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"

def test_updater_logic():
    repo = GITHUB_REPO
    github_token = GITHUB_TOKEN
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    
    # Simulating the EXACT way Updater makes the request
    try:
        req = urllib.request.Request(api_url)
        
        # Adding headers one by one like Updater does
        if github_token:
            req.add_header("Authorization", f"token {github_token}")
        
        req.add_header("Accept", "application/vnd.github.v3+json")
        
        # MISSING User-Agent (Let's see if this causes 404 or something else)
        print(f"Requesting: {api_url}")
        print(f"Headers: {req.headers}")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print("SUCCESS!")
            print(f"Latest tag: {data.get('tag_name')}")
            
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR {e.code}: {e.reason}")
        # Let's see if adding User-Agent fixes it
        print("Retrying WITH User-Agent...")
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)") 
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                print("SUCCESS with User-Agent!")
        except Exception as e2:
            print(f"Retry failed: {e2}")
    except Exception as e:
        print(f"GENERIC ERROR: {e}")

if __name__ == "__main__":
    test_updater_logic()
