
import json
import urllib.request
import os

token = "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"
repo = "RenatoNogueira/rje_avaliacoes_personal_trainer"

def check_github():
    print(f"Checking Repo: {repo}")
    
    # 1. Check if repo exists
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}")
    req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"Repo Found! Private: {data.get('private')}")
    except Exception as e:
        print(f"Repo Error: {e}")
        return

    # 2. Check releases
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases")
    req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            releases = json.loads(resp.read().decode())
            print(f"Found {len(releases)} releases.")
            for r in releases:
                print(f"- {r.get('tag_name')} (Latest: {r.get('name')})")
    except Exception as e:
        print(f"Releases Error: {e}")

    # 3. Check latest release specifically
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/latest")
    req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            latest = json.loads(resp.read().decode())
            print(f"Latest Release: {latest.get('tag_name')}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("Latest Release Error: 404 (This usually means NO releases have been published yet)")
        else:
            print(f"Latest Release Error: {e}")

if __name__ == "__main__":
    check_github()
