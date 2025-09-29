import requests

url = "https://push.cryptils.com"
data = {"title":"trying"}
post_requests = requests.post(url=url, json=data)

print(post_requests.status_code)
print(post_requests.json())