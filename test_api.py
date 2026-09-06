import requests

url = 'http://127.0.0.1:8000/api/analyze'

# Test 1: human.m4a (Benign)
with open('backend/uploads/human.m4a.m4a', 'rb') as f:
    res = requests.post(url, files={'file': f}, data={
        'caller_id': '+15550009999',
        'transaction_amount': 500,
        'recipient_is_new': False,
        'is_international': False
    })
    print("Test 1 status:", res.status_code)

# Test 2: neural.mp3 (Suspicious)
with open('backend/uploads/neural.mp3', 'rb') as f:
    res = requests.post(url, files={'file': f}, data={
        'caller_id': '+15550009999',
        'transaction_amount': 25000,
        'recipient_is_new': True,
        'is_international': True
    })
    print("Test 2 status:", res.status_code)

# Let's hit the liveness challenge for Test 2
if res.status_code == 200:
    data = res.json()
    call_id = data.get("id")
    if call_id:
        c_res = requests.post('http://127.0.0.1:8000/api/liveness/challenge', json={"call_record_id": call_id})
        print("Challenge status:", c_res.status_code)
        if c_res.status_code == 200:
            c_data = c_res.json()
            # Verify challenge
            with open('backend/uploads/human.m4a.m4a', 'rb') as f:
                v_res = requests.post(f'http://127.0.0.1:8000/api/liveness/verify/{c_data["challenge_id"]}', files={'file': f})
                print("Verify status:", v_res.status_code)

# Print stats
stats_res = requests.get('http://127.0.0.1:8000/api/calls/stats')
print("Stats:")
print(stats_res.json())
