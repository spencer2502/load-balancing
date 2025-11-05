#!/usr/bin/env python3
"""
Traffic Generator for Load Balancer Testing
Save as: ~/sdn-loadbalancer/traffic_generator.py
Run inside Mininet CLI: xterm client1
Then in the xterm: python3 ~/sdn-loadbalancer/traffic_generator.py
"""

import requests
import time
import random
import sys
from datetime import datetime

VIRTUAL_IP = "http://10.0.0.100"
PATTERNS = {
    "idle": {"min_rps": 0, "max_rps": 2, "duration": 5},
    "light": {"min_rps": 2, "max_rps": 5, "duration": 10},
    "medium": {"min_rps": 5, "max_rps": 15, "duration": 15},
    "heavy": {"min_rps": 15, "max_rps": 30, "duration": 10},
    "spike": {"min_rps": 30, "max_rps": 50, "duration": 5}
}

class TrafficGenerator:
    def __init__(self):
        self.total_requests = 0
        self.successful = 0
        self.failed = 0
        self.start_time = time.time()
    
    def send_request(self):
        """Send a single HTTP request"""
        try:
            response = requests.get(VIRTUAL_IP, timeout=2)
            self.total_requests += 1
            if response.status_code == 200:
                self.successful += 1
                server = "Unknown"
                if "Server 1" in response.text:
                    server = "10.0.0.1"
                elif "Server 2" in response.text:
                    server = "10.0.0.2"
                elif "Server 3" in response.text:
                    server = "10.0.0.3"
                return True, server
            else:
                self.failed += 1
                return False, None
        except Exception as e:
            self.failed += 1
            self.total_requests += 1
            return False, str(e)
    
    def generate_pattern(self, pattern_name):
        """Generate traffic for a specific pattern"""
        pattern = PATTERNS[pattern_name]
        rps = random.randint(pattern["min_rps"], pattern["max_rps"])
        
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Pattern: {pattern_name.upper()}")
        print(f"Target RPS: {rps}, Duration: {pattern['duration']}s")
        print(f"{'='*60}")
        
        start = time.time()
        requests_sent = 0
        
        while time.time() - start < pattern["duration"]:
            if rps > 0:
                success, server = self.send_request()
                requests_sent += 1
                
                if success:
                    print(f"✓ Request #{self.total_requests} -> Server {server}")
                else:
                    print(f"✗ Request #{self.total_requests} failed: {server}")
                
                # Sleep to maintain target RPS
                time.sleep(1.0 / rps if rps > 0 else 1)
            else:
                time.sleep(1)
        
        print(f"\nPattern complete: {requests_sent} requests sent")
    
    def run_random_patterns(self):
        """Run random traffic patterns continuously"""
        print("\n" + "="*60)
        print("SDN Load Balancer - Traffic Generator")
        print("="*60)
        print(f"Target: {VIRTUAL_IP}")
        print("Generating random traffic patterns...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Randomly select a pattern
                pattern = random.choice(list(PATTERNS.keys()))
                self.generate_pattern(pattern)
                
                # Show statistics
                uptime = time.time() - self.start_time
                avg_rps = self.total_requests / uptime if uptime > 0 else 0
                success_rate = (self.successful / self.total_requests * 100) if self.total_requests > 0 else 0
                
                print(f"\n{'='*60}")
                print(f"Statistics:")
                print(f"  Total Requests: {self.total_requests}")
                print(f"  Successful: {self.successful}")
                print(f"  Failed: {self.failed}")
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Average RPS: {avg_rps:.2f}")
                print(f"  Uptime: {uptime:.1f}s")
                print(f"{'='*60}\n")
                
                # Short pause between patterns
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nTraffic generation stopped.")
            print(f"\nFinal Statistics:")
            print(f"  Total Requests: {self.total_requests}")
            print(f"  Successful: {self.successful}")
            print(f"  Failed: {self.failed}")
            print(f"  Success Rate: {success_rate:.1f}%")
    
    def run_specific_pattern(self, pattern_name):
        """Run a specific traffic pattern"""
        if pattern_name not in PATTERNS:
            print(f"Error: Unknown pattern '{pattern_name}'")
            print(f"Available patterns: {', '.join(PATTERNS.keys())}")
            return
        
        print(f"\nRunning {pattern_name} pattern...")
        self.generate_pattern(pattern_name)


def main():
    generator = TrafficGenerator()
    
    if len(sys.argv) > 1:
        # Run specific pattern
        pattern = sys.argv[1].lower()
        generator.run_specific_pattern(pattern)
    else:
        # Run random patterns
        generator.run_random_patterns()


if __name__ == "__main__":
    main()