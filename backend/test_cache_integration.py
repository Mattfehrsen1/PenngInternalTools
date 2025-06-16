#!/usr/bin/env python3
"""
Quick test script to verify Redis cache integration
Phase 4.3: Test cache performance improvements
"""

import asyncio
import time
import requests
from services.cache_service import cache_service

async def test_cache_service():
    """Test Redis cache service directly"""
    print("🧪 Testing Redis Cache Service...")
    
    # Test cache connection
    stats = cache_service.get_cache_stats()
    print(f"📊 Cache Status: {stats}")
    
    if not stats.get('enabled', False):
        print("❌ Redis not available - caching disabled")
        return False
    
    # Test cache operations
    test_query = "What is your background?"
    test_persona = "test-persona-123"
    
    # Test caching a response
    test_response = {
        "content": "This is a test response",
        "persona_name": "Test Persona",
        "latency_ms": 100.0
    }
    
    print(f"💾 Caching test response...")
    success = await cache_service.cache_response(test_query, test_persona, test_response)
    print(f"Cache store success: {success}")
    
    # Test retrieving cached response
    print(f"📋 Retrieving cached response...")
    cached = await cache_service.get_cached_response(test_query, test_persona)
    
    if cached:
        print(f"✅ Cache hit! Content: {cached.get('content', '')[:50]}...")
        return True
    else:
        print(f"❌ Cache miss - no data found")
        return False

def test_api_endpoint():
    """Test the cache stats API endpoint"""
    print("\n🌐 Testing Cache Stats API Endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/elevenlabs/cache/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {data}")
            return data.get('success', False)
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Connection failed: {str(e)}")
        return False

def test_function_call_performance():
    """Test actual function call performance with caching"""
    print("\n⚡ Testing Function Call Performance...")
    
    test_payload = {
        "function_name": "query_persona_knowledge",
        "parameters": {
            "query": "What is your expertise?",
            "persona_id": "e250046f-b3c3-4d9e-993e-ed790f7d1e73"  # Hormozi persona
        }
    }
    
    headers = {
        "X-Service-Token": "elevenlabs-clone-advisor-webhook-token-2024",
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Making first function call (cache miss expected)...")
        start_time = time.time()
        response1 = requests.post(
            "http://localhost:8000/elevenlabs/function-call",
            json=test_payload,
            headers=headers,
            timeout=30
        )
        first_latency = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"✅ First call successful - {first_latency:.2f}ms")
            print(f"   Cache hit: {data1.get('result', {}).get('cache_hit', 'unknown')}")
            
            # Second call should be cached
            print("🚀 Making second function call (cache hit expected)...")
            start_time = time.time()
            response2 = requests.post(
                "http://localhost:8000/elevenlabs/function-call",
                json=test_payload,
                headers=headers,
                timeout=30
            )
            second_latency = (time.time() - start_time) * 1000
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"✅ Second call successful - {second_latency:.2f}ms")
                print(f"   Cache hit: {data2.get('result', {}).get('cache_hit', 'unknown')}")
                
                # Calculate performance improvement
                if first_latency > 0 and second_latency > 0:
                    improvement = ((first_latency - second_latency) / first_latency) * 100
                    print(f"🎯 Performance improvement: {improvement:.1f}%")
                    print(f"   Before: {first_latency:.2f}ms")
                    print(f"   After: {second_latency:.2f}ms")
                    
                    if improvement > 50:
                        print("🚀 EXCELLENT: >50% improvement achieved!")
                        return True
                    elif improvement > 20:
                        print("✅ GOOD: >20% improvement achieved")
                        return True
                    else:
                        print("⚠️ MODERATE: Some improvement but below target")
                        return False
                
            else:
                print(f"❌ Second call failed: {response2.status_code}")
                return False
        else:
            print(f"❌ First call failed: {response1.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        return False

async def main():
    """Run all cache integration tests"""
    print("🧪 Redis Cache Integration Test - Phase 4.3")
    print("=" * 50)
    
    results = []
    
    # Test 1: Direct cache service
    results.append(await test_cache_service())
    
    # Test 2: API endpoint
    results.append(test_api_endpoint())
    
    # Test 3: Performance improvement
    results.append(test_function_call_performance())
    
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    print(f"Cache Service: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"API Endpoint: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"Performance: {'✅ PASS' if results[2] else '❌ FAIL'}")
    
    overall_success = all(results)
    print(f"\n🎯 OVERALL: {'✅ SUCCESS - Redis caching integrated!' if overall_success else '❌ ISSUES DETECTED'}")
    
    if overall_success:
        print("\n🚀 Next Steps:")
        print("   - Redis caching is working")
        print("   - Performance improvements verified")
        print("   - Ready for Cape Town deployment!")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main()) 