#!/usr/bin/env python3
import requests
import json
from jose import jwt, JWTError
from datetime import datetime

def test_token_validity():
    # Login and get token
    print("🔐 Logging in...")
    login_response = requests.post('http://localhost:8000/auth/login', data={'username': 'demo', 'password': 'demo123'})
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()['access_token']
    print(f'🔐 Got token: {token[:50]}...')

    # Decode token to check expiration
    try:
        unverified_claims = jwt.get_unverified_claims(token)
        exp = unverified_claims.get('exp')
        if exp:
            exp_date = datetime.fromtimestamp(exp)
            print(f'📅 Token expires: {exp_date}')
            print(f'⏰ Current time: {datetime.now()}')
            time_diff = exp_date - datetime.now()
            print(f'⏳ Time until expiry: {time_diff}')
        else:
            print('❌ No expiration claim found')
            
        print(f'📄 Full claims: {unverified_claims}')
    except Exception as e:
        print(f'❌ Error decoding token: {e}')

    # Test token with various endpoints
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n🧪 Testing endpoints:")
    
    # Test persona list
    personas_response = requests.get('http://localhost:8000/persona/list', headers=headers)
    print(f'📋 Persona list: {personas_response.status_code}')
    if personas_response.status_code != 200:
        print(f'   ❌ Error: {personas_response.text}')
    
    # Test upload endpoint with empty data (to see auth validation)
    upload_response = requests.post('http://localhost:8000/persona/upload', 
                                   headers={'Authorization': f'Bearer {token}'}, 
                                   files={})
    print(f'📤 Upload test: {upload_response.status_code}')
    if upload_response.status_code == 401:
        print(f'   ❌ Auth Error: {upload_response.text}')
    elif upload_response.status_code == 422:
        print(f'   ✅ Auth OK, validation error (expected): {upload_response.json().get("detail", "Unknown")}')
    else:
        print(f'   📝 Response: {upload_response.text}')

if __name__ == "__main__":
    test_token_validity() 