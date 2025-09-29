import requests

url = "https://push.cryptils.com/send"
params = {"title": "trying"}

try:
    response = requests.get(url, params=params, timeout=10)
    print(response.status_code)
    if response.headers.get('Content-Type', '').startswith('application/json') and response.text.strip():
        print(response.json())
    else:
        print({'status': 'success' if response.ok else 'error', 'body': response.text.strip()})
    response.raise_for_status()
except requests.exceptions.RequestException as exc:
    print({'status': 'error', 'message': str(exc)})
