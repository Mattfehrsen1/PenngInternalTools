#!/usr/bin/env python3
"""
Quick Cache Performance Test
Shows the dramatic improvement from Redis caching
"""

import requests
import time
import json

def test_cache_performance():
    """Test the same query twice to show cache performance improvement"""
    
    url = "http://localhost:8000/elevenlabs/function-call"
    headers = {
        "X-Service-Token": "NVhAvjqhHixz8liX47R4qJze9l236Rquu7pjfL7fLD0",
        "Content-Type": "application/json"
    }
    
    # Test with a knowledge base query
    payload = {
        "function_name": "query_persona_knowledge",
        "parameters": {
            "query": "What is your expertise and background?",
            "persona_id": "e250046f-b3c3-4d9e-993e-ed790f7d1e73"  # Hormozi persona
        }
    }
    
    print("🚀 Redis Cache Performance Test")
    print("=" * 50)
    
    # First call (should be cache miss)
    print("📋 First call (cache miss expected)...")
    start_time = time.time()
    try:
        response1 = requests.post(url, json=payload, headers=headers, timeout=30)
        first_latency = (time.time() - start_time) * 1000
        
        if response1.status_code == 200:
            data1 = response1.json()
            result1 = data1.get('result', {})
            
            print(f"✅ First call successful:")
            print(f"   ⏱️  Latency: {first_latency:.2f}ms")
            print(f"   🎯 Cache hit: {result1.get('cache_hit', 'unknown')}")
            print(f"   📝 Content: {result1.get('content', '')[:80]}...")
            
            # Small delay to ensure cache is stored
            time.sleep(1)
            
            # Second call (should be cache hit)
            print(f"\n📋 Second call (cache hit expected)...")
            start_time = time.time()
            response2 = requests.post(url, json=payload, headers=headers, timeout=30)
            second_latency = (time.time() - start_time) * 1000
            
            if response2.status_code == 200:
                data2 = response2.json()
                result2 = data2.get('result', {})
                
                print(f"✅ Second call successful:")
                print(f"   ⏱️  Latency: {second_latency:.2f}ms")
                print(f"   🎯 Cache hit: {result2.get('cache_hit', 'unknown')}")
                print(f"   📝 Content: {result2.get('content', '')[:80]}...")
                
                # Calculate improvement
                if first_latency > 0 and second_latency > 0:
                    improvement = ((first_latency - second_latency) / first_latency) * 100
                    time_saved = first_latency - second_latency
                    
                    print(f"\n🎯 PERFORMANCE RESULTS:")
                    print(f"   📊 Before: {first_latency:.2f}ms")
                    print(f"   📊 After:  {second_latency:.2f}ms")
                    print(f"   ⚡ Improvement: {improvement:.1f}%")
                    print(f"   💰 Time saved: {time_saved:.2f}ms")
                    
                    if improvement > 70:
                        print(f"   🚀 EXCELLENT: Cape Town deployment ready!")
                    elif improvement > 50:
                        print(f"   ✅ GOOD: Significant improvement achieved")
                    elif improvement > 20:
                        print(f"   ⚠️  MODERATE: Some improvement")
                    else:
                        print(f"   ❌ MINIMAL: Cache may not be working optimally")
                    
                    # Extrapolate Cape Town performance
                    cape_town_base = 250  # ms network latency
                    cape_town_before = cape_town_base + first_latency
                    cape_town_after = cape_town_base + second_latency
                    cape_town_improvement = ((cape_town_before - cape_town_after) / cape_town_before) * 100
                    
                    print(f"\n🌍 CAPE TOWN IMPACT PROJECTION:")
                    print(f"   📍 Before: {cape_town_before:.0f}ms (250ms network + {first_latency:.0f}ms processing)")
                    print(f"   📍 After:  {cape_town_after:.0f}ms (250ms network + {second_latency:.0f}ms processing)")
                    print(f"   🎯 Total improvement: {cape_town_improvement:.1f}%")
            else:
                print(f"❌ Second call failed: {response2.status_code}")
        else:
            print(f"❌ First call failed: {response1.status_code}")
            if response1.status_code == 401:
                print("   💡 Tip: Make sure the service token is correct")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("   💡 Make sure the server is running: uvicorn main:app --reload --port 8000")

def get_cache_stats():
    """Get current cache statistics"""
    try:
        response = requests.get("http://localhost:8000/elevenlabs/cache/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            cache_info = stats.get('cache_stats', {})
            
            print(f"\n📊 REDIS CACHE STATISTICS:")
            print(f"   🔌 Status: {'✅ Connected' if cache_info.get('enabled') else '❌ Disconnected'}")
            print(f"   👥 Connections: {cache_info.get('connected_clients', 0)}")
            print(f"   💾 Memory: {cache_info.get('used_memory_human', 'Unknown')}")
            print(f"   🎯 Hit rate: {cache_info.get('hit_rate', 0)}%")
            print(f"   📈 Hits: {cache_info.get('keyspace_hits', 0)}")
            print(f"   📉 Misses: {cache_info.get('keyspace_misses', 0)}")
        else:
            print(f"❌ Cache stats unavailable: {response.status_code}")
    except Exception as e:
        print(f"❌ Cache stats error: {str(e)}")

if __name__ == "__main__":
    get_cache_stats()
    test_cache_performance()
    get_cache_stats()  # Show updated stats 