#!/usr/bin/env python3
"""
HTTP API Server for SDN Load Balancer Dashboard
Save as: ~/sdn-loadbalancer/api_server.py
Run with: python3 api_server.py

This server bridges POX controller and the web dashboard
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import threading
from collections import deque

# Shared stats storage
stats_data = {
    "total_requests": 0,
    "start_time": time.time(),
    "servers": {
        "10.0.0.1": {"requests": 0, "response_times": deque(maxlen=50)},
        "10.0.0.2": {"requests": 0, "response_times": deque(maxlen=50)},
        "10.0.0.3": {"requests": 0, "response_times": deque(maxlen=50)}
    },
    "recent_requests": deque(maxlen=50)
}

class APIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Calculate stats
            response = self.calculate_stats()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/update':
            # Receive update from POX controller
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            self.update_stats(data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        
        elif self.path == '/reset':
            self.reset_stats()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "reset"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()

    def calculate_stats(self):
        """Calculate current statistics"""
        total = stats_data["total_requests"]
        elapsed = time.time() - stats_data["start_time"]
        rps = total / elapsed if elapsed > 0 else 0
        
        # Calculate server stats
        servers = {}
        all_response_times = []
        
        for ip, data in stats_data["servers"].items():
            times = list(data["response_times"])
            avg_response = sum(times) / len(times) if times else 0
            all_response_times.extend(times)
            
            servers[ip] = {
                "requests": data["requests"],
                "avg_response": avg_response
            }
        
        # Overall average response time
        avg_response = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        # Calculate balance score (how evenly distributed)
        if total > 0:
            ideal = total / 3
            variance = sum((s["requests"] - ideal) ** 2 for s in servers.values()) / 3
            balance_score = max(0, 100 - (variance / ideal * 10)) if ideal > 0 else 100
        else:
            balance_score = 100
        
        return {
            "total_requests": total,
            "rps": rps,
            "avg_response": avg_response,
            "balance_score": balance_score,
            "servers": servers,
            "recent_requests": list(stats_data["recent_requests"])
        }

    def update_stats(self, data):
        """Update stats from POX controller"""
        stats_data["total_requests"] += 1
        
        server_ip = data.get("server_ip")
        if server_ip in stats_data["servers"]:
            stats_data["servers"][server_ip]["requests"] += 1
            
            # Add response time (simulated for now)
            response_time = data.get("response_time", 50 + (hash(str(time.time())) % 50))
            stats_data["servers"][server_ip]["response_times"].append(response_time)
        
        # Add to recent requests
        stats_data["recent_requests"].appendleft({
            "timestamp": time.time(),
            "client": data.get("client_ip", "unknown"),
            "server": server_ip
        })

    def reset_stats(self):
        """Reset all statistics"""
        stats_data["total_requests"] = 0
        stats_data["start_time"] = time.time()
        for server in stats_data["servers"].values():
            server["requests"] = 0
            server["response_times"].clear()
        stats_data["recent_requests"].clear()

    def log_message(self, format, *args):
        """Override to reduce log spam"""
        pass

def run_server(port=8080):
    """Start the HTTP API server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    
    print("="*60)
    print("SDN Load Balancer API Server")
    print("="*60)
    print(f"Server running on http://localhost:{port}")
    print(f"Dashboard: Open dashboard.html in your browser")
    print(f"Stats endpoint: http://localhost:{port}/stats")
    print(f"Update endpoint: http://localhost:{port}/update (POST)")
    print("="*60)
    print("Press Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()