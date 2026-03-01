import urllib.request
import json
import sys

# Ensure stdout uses utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

token = "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"
repo = "RenatoNogueira/rje_avaliacoes_personal_trainer"

def check_url(url, description):
    print(f"\n--- Checking {description} ---")
    print(f"URL: {url}")
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('User-Agent', 'Updater-Test')
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"Status: {resp.status}")
            scopes = resp.getheader('X-OAuth-Scopes')
            print(f"Scopes: {scopes}")
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list):
                print(f"Data type: List, Count: {len(data)}")
                if len(data) > 0:
                    item = data[0]
                    name = item.get('name') or item.get('tag_name') or item.get('full_name')
                    print(f"First item name/tag: {name}")
            else:
                print(f"Data type: Object")
                print(f"Full Name: {data.get('full_name')}")
                print(f"Latest tag: {data.get('tag_name')}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_url("https://api.github.com/user", "Current User")
    check_url(f"https://api.github.com/repos/{repo}", "Repository Info")
    check_url(f"https://api.github.com/repos/{repo}/releases/latest", "Latest Release")
    check_url(f"https://api.github.com/repos/{repo}/tags", "Tags")
    
    alternative_repo = "RenatoNogueira/rjeavaliacoes"
    check_url(f"https://api.github.com/repos/{alternative_repo}/releases/latest", "Alt Latest Release")
    check_url(f"https://api.github.com/repos/{alternative_repo}/tags", "Alt Tags")
