import requests

url = 'http://127.0.0.1:8000/api/analyze'

# Test 3: Get a challenge
with open('backend/uploads/human.m4a.m4a', 'rb') as f:
    res = requests.post(url, files={'file': f}, data={
        'caller_id': '+15550009999',
        'transaction_amount': 500,
        'recipient_is_new': False,
        'is_international': False
    })
    
call_id = res.json().get("id")
print("Call ID:", call_id)

c_res = requests.post('http://127.0.0.1:8000/api/liveness/challenge', json={"call_record_id": call_id})
print("Challenge res:", c_res.status_code, c_res.text)

if c_res.status_code == 200:
    challenge_id = c_res.json()["challenge_id"]
    with open('backend/uploads/human.m4a.m4a', 'rb') as f:
        v_res = requests.post(f'http://127.0.0.1:8000/api/liveness/verify/{challenge_id}', files={'file': f})
        print("Verify res:", v_res.status_code, v_res.text)

stats_res = requests.get('http://127.0.0.1:8000/api/calls/stats')
print("Stats:")
print(stats_res.json())
