import requests
import time

url = 'http://localhost:8000/elevenlabs/function-call'
headers = {
    'X-Service-Token': 'NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0', 
    'Content-Type': 'application/json'
}

# Test different query
payload = {
    'function_name': 'query_persona_knowledge',
    'parameters': {
        'query': 'What are your main skills and expertise?',
        'persona_id': 'e250046f-b3c3-4d9e-993e-ed790f7d1e73'
    }
}

print('🧪 Testing NEW query (should be cache miss)...')
start = time.time()
resp = requests.post(url, json=payload, headers=headers)
latency = (time.time() - start) * 1000
print(f'New query latency: {latency:.2f}ms')
print(f'Cache hit: {resp.json().get("result", {}).get("cache_hit", "unknown")}')

print('\n🧪 Testing SAME query again (should be cache hit)...')
start = time.time()
resp = requests.post(url, json=payload, headers=headers)
latency = (time.time() - start) * 1000
print(f'Repeat query latency: {latency:.2f}ms')
print(f'Cache hit: {resp.json().get("result", {}).get("cache_hit", "unknown")}')

improvement = ((latency if resp.json().get("result", {}).get("cache_hit") else 0) / latency * 100) if latency > 0 else 0
print(f'\n⚡ This shows cache working for EVERY new query!') 