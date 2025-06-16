#!/usr/bin/env python3
"""
Real-time Redis Cache Monitor
Watch cache performance while testing the UI
"""

import requests
import time
import os
import json
from datetime import datetime

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_cache_stats():
    """Get current cache statistics"""
    try:
        response = requests.get("http://localhost:8000/elevenlabs/cache/stats", timeout=2)
        if response.status_code == 200:
            return response.json().get('cache_stats', {})
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def format_cache_display(stats, previous_stats=None):
    """Format cache statistics for display"""
    if 'error' in stats:
        return f"❌ Cache Error: {stats['error']}"
    
    if not stats.get('enabled', False):
        return "❌ Redis Cache: DISABLED"
    
    # Calculate changes
    hit_change = ""
    miss_change = ""
    if previous_stats and previous_stats.get('enabled'):
        hit_diff = stats.get('keyspace_hits', 0) - previous_stats.get('keyspace_hits', 0)
        miss_diff = stats.get('keyspace_misses', 0) - previous_stats.get('keyspace_misses', 0)
        
        if hit_diff > 0:
            hit_change = f" (+{hit_diff})"
        if miss_diff > 0:
            miss_change = f" (+{miss_diff})"
    
    return f"""
🚀 REDIS CACHE MONITOR - Clone Advisor
{'='*50}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}

🔌 Status: ✅ CONNECTED
👥 Connections: {stats.get('connected_clients', 0)}
💾 Memory Used: {stats.get('used_memory_human', 'Unknown')}

📊 PERFORMANCE METRICS:
   🎯 Hit Rate: {stats.get('hit_rate', 0):.1f}%
   📈 Cache Hits: {stats.get('keyspace_hits', 0)}{hit_change}
   📉 Cache Misses: {stats.get('keyspace_misses', 0)}{miss_change}

💡 HOW TO TEST IN UI:
   1. Open http://localhost:3000
   2. Start a voice conversation with a persona
   3. Ask questions about their knowledge base
   4. Ask similar questions again
   5. Watch cache hits increase here!

⚡ WHAT TO LOOK FOR:
   - First question: Cache miss (+1 miss)
   - Same question: Cache hit (+1 hit)
   - Hit rate should increase over time
   - Conversations should feel faster

Press Ctrl+C to stop monitoring...
"""

def main():
    """Main monitoring loop"""
    print("🚀 Starting Redis Cache Monitor...")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:3000")
    print("   Starting monitor in 3 seconds...")
    time.sleep(3)
    
    previous_stats = None
    
    try:
        while True:
            clear_screen()
            current_stats = get_cache_stats()
            print(format_cache_display(current_stats, previous_stats))
            
            previous_stats = current_stats
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print("\n\n✅ Cache monitoring stopped.")
        print("🎯 Final cache stats:")
        final_stats = get_cache_stats()
        if final_stats.get('enabled'):
            print(f"   Hit Rate: {final_stats.get('hit_rate', 0):.1f}%")
            print(f"   Total Hits: {final_stats.get('keyspace_hits', 0)}")
            print(f"   Total Misses: {final_stats.get('keyspace_misses', 0)}")

if __name__ == "__main__":
    main() 