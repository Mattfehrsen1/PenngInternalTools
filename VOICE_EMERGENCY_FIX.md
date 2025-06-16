# 🚨 Voice Streaming Emergency Fix

## 🔍 **Issues Identified**

1. **Wrong Persona ID**: Frontend using `"1"` instead of UUID like `e250046f-b3c3-4d9e-993e-ed790f7d1e73`
2. **API Proxy Issue**: Requests going to `localhost:3001` instead of backend `localhost:8000`

## ⚡ **Quick Fix Solutions**

### **Option 1: Auto-Login + Use Real Persona (Recommended)**

**Step 1**: Open browser console on any Clone Advisor page

**Step 2**: Run this **complete fix script**:
```javascript
// Auto-login and fix persona
fetch('/api/auth/login', {
  method: 'POST', 
  headers: {'Content-Type': 'application/x-www-form-urlencoded'}, 
  body: 'username=demo&password=demo123'
}).then(r => r.json()).then(data => {
  localStorage.setItem('auth_token', data.access_token);
  
  // Navigate to a real persona
  window.location.href = '/chat/e250046f-b3c3-4d9e-993e-ed790f7d1e73';
}).catch(err => {
  console.error('Login failed:', err);
  alert('❌ Login failed. Make sure backend is running on port 8000');
});
```

**Step 3**: After redirect, try the voice button - it should work!

### **Option 2: Direct Backend Test (If frontend proxy broken)**

**Step 1**: Get a fresh token:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo123"
```

**Step 2**: Test voice API directly:
```bash
curl -X POST "http://localhost:8000/api/personas/e250046f-b3c3-4d9e-993e-ed790f7d1e73/voice/stream" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello this should work"}' \
  -o test_voice_final.mp3 -w "Size: %{size_download} bytes\n"
```

**Expected**: Should get > 0 bytes of audio

### **Option 3: Force Frontend to Use Backend URL**

If the Next.js proxy isn't working, override it in browser console:

```javascript
// Override fetch to force backend URL
const originalFetch = window.fetch;
window.fetch = function(url, options) {
  if (url.startsWith('/api/')) {
    url = 'http://localhost:8000' + url;
    console.log('🔧 Redirecting API call to backend:', url);
  }
  return originalFetch(url, options);
};

alert('✅ API calls will now go to backend. Try voice button again.');
```

## 🎯 **Expected Results**

After any fix:
- ✅ Console shows: `[useAudioStream] Starting voice generation for persona e250046f-...`
- ✅ API call goes to `http://localhost:8000/api/personas/e250046f-.../voice/stream`
- ✅ Voice plays within 1-2 seconds
- ✅ No more "Persona not found" errors

## 🔧 **Verify Backend is Running**

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"0.1.0","service":"clone-advisor-api"}
```

## 🆘 **Troubleshooting**

**If backend isn't running:**
```bash
cd backend
source venv310/bin/activate
uvicorn main:app --reload --port 8000
```

**If frontend proxy still broken:**
- Restart frontend: `npm run dev`
- Try incognito browser window
- Clear browser cache and localStorage

**If voice still doesn't work:**
- Check ELEVENLABS_API_KEY is set in backend/.env
- Verify browser audio permissions
- Try different browser (Chrome/Firefox)

---

**🎉 Once fixed, voice streaming should work perfectly across all personas!** 