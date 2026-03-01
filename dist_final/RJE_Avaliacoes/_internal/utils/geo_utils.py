import requests

def get_current_city() -> str | None:
    """
    Detects the current city based on the user's public IP address.
    Uses the ip-api.com service.
    """
    try:
        # ip-api.com returns a JSON with city, country, etc.
        # No API key required for low volume.
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("city")
    except Exception as e:
        print(f"Error detecting geolocation: {e}")
    return None
