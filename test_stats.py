import requests

try:
    res = requests.get('http://127.0.0.1:8000/api/calls/stats')
    print("Status Code:", res.status_code)
    print(res.json())
except Exception as e:
    print("Error:", e)
