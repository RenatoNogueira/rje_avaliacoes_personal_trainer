import urllib.request
import json
import os

token = "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"
repo = "RenatoNogueira/rje_avaliacoes_personal_trainer"

def check_url(url, description):
    print(f"\nChecking {description}: {url}")
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('User-Agent', 'Updater-Test')
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Status: {resp.status}")
            print(f"Scopes: {resp.getheader('X-OAuth-Scopes')}")
            data = json.loads(resp.read().decode())
            if isinstance(data, list):
                print(f"Data count: {len(data)}")
                if len(data) > 0:
                    print(f"First item: {data[0].get('name') or data[0].get('tag_name') or data[0].get('full_name')}")
            else:
                print(f"Data: {data.get('full_name') or data.get('tag_name') or 'Object returned'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_url("https://api.github.com/user", "Current User")
    check_url(f"https://api.github.com/repos/{repo}", "Repository Info")
    check_url(f"https://api.github.com/repos/{repo}/releases", "Releases")
    check_url(f"https://api.github.com/repos/{repo}/tags", "Tags")
    
    alternative_repo = "RenatoNogueira/rjeavaliacoes"
    check_url(f"https://api.github.com/repos/{alternative_repo}/releases", "Alt Releases")
    check_url(f"https://api.github.com/repos/{alternative_repo}/tags", "Alt Tags")
