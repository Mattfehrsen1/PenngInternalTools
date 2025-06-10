from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

router = APIRouter()

@router.get("/test-sse")
async def test_sse():
    async def generate():
        # EventSourceResponse expects a dict with 'event' and 'data' keys
        # Send a test citation
        yield {
            "event": "citations",
            "data": json.dumps([{'id': 1, 'text': 'Test citation', 'source': 'test.txt', 'score': 0.9}])
        }
        
        # Send some tokens
        test_message = "Hello, this is a test streaming response!"
        for word in test_message.split():
            yield {
                "event": "token", 
                "data": json.dumps({'token': word + ' '})
            }
            await asyncio.sleep(0.1)  # Small delay to see streaming
            
        # Send done event
        yield {
            "event": "done",
            "data": json.dumps({'status': 'complete', 'tokens': 10})
        }
    
    return EventSourceResponse(generate())
