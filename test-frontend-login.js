// Test script to simulate frontend login behavior
const API_URL = 'http://localhost:8000';

async function testLogin() {
    console.log('🧪 Testing frontend login flow...');
    
    // Step 1: Test the exact same request the frontend makes
    const formData = new FormData();
    formData.append('username', 'demo');
    formData.append('password', 'demo123');

    try {
        console.log('📤 Sending login request...');
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            body: formData,
        });

        console.log('📥 Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.log('❌ Login failed:', errorText);
            return;
        }

        const data = await response.json();
        console.log('✅ Login successful!');
        console.log('🔑 Token received:', data.access_token.substring(0, 20) + '...');
        
        // Step 2: Test using the token
        console.log('🧪 Testing token validation...');
        const meResponse = await fetch(`${API_URL}/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${data.access_token}`
            }
        });
        
        if (meResponse.ok) {
            const user = await meResponse.json();
            console.log('✅ Token validation successful!');
            console.log('👤 User info:', user);
        } else {
            console.log('❌ Token validation failed');
        }
        
    } catch (error) {
        console.log('❌ Network error:', error.message);
    }
}

// Run the test
testLogin();
