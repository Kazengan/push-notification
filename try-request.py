import requests

url = "https://push.cryptils.com"
payload = {
    "title": "trying",
    "message": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis accumsan vulputate gravida. Integer maximus ante eros, ut egestas quam facilisis in. Quisque rutrum mi dui, sit amet volutpat sem aliquet vel. Sed venenatis ipsum non magna laoreet blandit. Pellentesque sed varius elit, et consequat ex. Vestibulum sed vestibulum neque. Proin non viverra sem.",
    "url": "https://example.com",
    "color": "blue"
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(response.status_code)
    if response.headers.get('Content-Type', '').startswith('application/json') and response.text.strip():
        print(response.json())
    else:
        print({'status': 'success' if response.ok else 'error', 'body': response.text.strip()})
    response.raise_for_status()
except requests.exceptions.RequestException as exc:
    print({'status': 'error', 'message': str(exc)})
