#!/usr/bin/env python3
"""
Traffic Generator using Mininet API
Save as: ~/sdn-loadbalancer/run_traffic.py
Run: sudo python3 run_traffic.py
(This connects to existing Mininet and generates traffic)
"""

from mininet.cli import CLI
import time
import random
import threading

# Traffic patterns
PATTERNS = {
    "idle": {"rate": 1, "duration": 5},
    "light": {"rate": 3, "duration": 8},
    "medium": {"rate": 8, "duration": 12},
    "heavy": {"rate": 15, "duration": 10},
    "spike": {"rate": 30, "duration": 5}
}

def generate_traffic_thread(net, stop_event):
    """Generate traffic in background thread"""
    clients = [net.get('client1'), net.get('client2'), net.get('client3')]
    virtual_ip = "10.0.0.100"
    
    print("\n" + "="*60)
    print("Automated Traffic Generator Started")
    print("Generating random traffic patterns...")
    print("="*60 + "\n")
    
    cycle = 0
    while not stop_event.is_set():
        # Select random pattern
        pattern_name = random.choice(list(PATTERNS.keys()))
        pattern = PATTERNS[pattern_name]
        
        cycle += 1
        print(f"\n[Cycle {cycle}] Pattern: {pattern_name.upper()} - {pattern['rate']} req/s for {pattern['duration']}s")
        
        start_time = time.time()
        request_count = 0
        
        # Generate requests for this pattern
        while time.time() - start_time < pattern['duration'] and not stop_event.is_set():
            # Select random client
            client = random.choice(clients)
            
            # Send request
            result = client.cmd(f'curl -s -m 1 {virtual_ip} 2>&1 | grep -o "Server [0-9]"')
            request_count += 1
            
            if result.strip():
                print(f"  ✓ Request {request_count}: {client.name} -> {result.strip()}")
            else:
                print(f"  ✗ Request {request_count}: {client.name} -> Failed")
            
            # Sleep to maintain rate
            time.sleep(1.0 / pattern['rate'])
        
        print(f"  Pattern complete: {request_count} requests sent")
        
        # Pause between patterns
        time.sleep(2)

def start_automated_traffic(net):
    """Start automated traffic generation"""
    stop_event = threading.Event()
    
    # Start traffic generator in background thread
    traffic_thread = threading.Thread(
        target=generate_traffic_thread,
        args=(net, stop_event),
        daemon=True
    )
    traffic_thread.start()
    
    print("\nTraffic generator running in background!")
    print("Use Mininet CLI normally, traffic will continue...")
    print("Type 'exit' to stop everything\n")
    
    return stop_event, traffic_thread

# This can be imported and used in topology.py
# Or run standalone to connect to existing Mininet
if __name__ == "__main__":
    print("This script should be imported into your topology.py")
    print("Or modify your topology.py to call start_automated_traffic(net)")