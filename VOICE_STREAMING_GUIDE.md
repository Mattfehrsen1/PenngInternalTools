# 🎙️ Voice Streaming - User Testing Guide

## ✅ Status: FULLY FUNCTIONAL 
The ElevenLabs voice streaming feature is now working correctly with your API key.

## 🚀 Quick Test Instructions

### 1. **Start Backend** (if not already running)
```bash
cd backend
source venv310/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. **Start Frontend**
```bash
cd frontend
npm run dev
```

### 3. **Test Voice Streaming**
1. Navigate to the chat interface: `http://localhost:3000/chat/[persona-name]`
2. Send a message to get an AI response
3. Click the **🔊 voice button** next to any AI message
4. **Expected**: Audio should start playing within 500ms

## 🔧 Available Voices
Your ElevenLabs account has access to **21 voices** including:
- **Sarah** (default) - `EXAVITQu4vr4xnSDxMaL`
- **Aria** - `9BWtsMINqrJLrRacOk9x`
- **Laura** - `FGY2WhTYpPnrIDTdsKH5`
- **Charlie** - `IKne3meq5aSn9XLyUdCD`
- **George** - `JBFqnCBsd6RMkjVDRZzb`
- And 16 more voices...

## 🎯 Expected Behavior
- **Loading**: Voice button shows spinner while generating
- **Streaming**: Audio plays in real-time as chunks arrive
- **Quality**: High-quality audio using `eleven_flash_v2_5` model
- **Speed**: First audio chunk within 500ms
- **Fallback**: If voice fails, text remains visible

## 🐛 Troubleshooting

### If voice button doesn't work:
1. **Check browser console** for JavaScript errors
2. **Verify API endpoint**: Look for calls to `/api/personas/{id}/voice/stream`
3. **Check backend logs** for voice generation errors
4. **Test with different persona** (some may not have voice settings)

### If audio doesn't play:
1. **Check browser audio permissions**
2. **Verify audio codec support** (we use MP3)
3. **Test with headphones** to rule out speaker issues
4. **Try different voice ID** in persona settings

### If voice is slow/choppy:
1. **Check internet connection** (streaming requires stable connection)
2. **Verify ElevenLabs API quota** (check your account limits)
3. **Try shorter messages** (long text takes more time to generate)

## 📊 Technical Details
- **Model**: `eleven_flash_v2_5` (optimized for speed)
- **Format**: MP3 22kHz 32kbps
- **Streaming**: Real-time chunk delivery
- **Retry Logic**: 3 attempts with exponential backoff
- **Error Handling**: Graceful fallback to text-only

## 🎉 Success Indicators
✅ Voice button appears on AI messages  
✅ Clicking shows loading spinner  
✅ Audio starts within 500ms  
✅ Voice quality is clear and natural  
✅ Multiple messages can play sequentially  

---

**Note**: This feature uses your ElevenLabs API key and will consume character quota based on message length. 