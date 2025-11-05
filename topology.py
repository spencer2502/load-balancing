#!/usr/bin/env python3
"""
SDN Load Balancer Topology with Automated Testing
Save as: ~/sdn-loadbalancer/topology.py
Run with: sudo python3 topology.py [load_profile] [num_requests]

Examples:
    sudo python3 topology.py                    # Interactive mode
    sudo python3 topology.py light              # Light load (50 requests)
    sudo python3 topology.py medium             # Medium load (200 requests)
    sudo python3 topology.py heavy              # Heavy load (500 requests)
    sudo python3 topology.py spike              # Spike test (burst of 100 requests)
    sudo python3 topology.py custom 300         # Custom number of requests
"""
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import time
import os
import threading
import sys

# Load Profile Configurations
LOAD_PROFILES = {
    'light': {
        'total_requests': 50,
        'requests_per_second': 1,
        'concurrent_clients': 1,
        'description': 'Light load - 50 requests at 1 req/sec'
    },
    'medium': {
        'total_requests': 200,
        'requests_per_second': 3,
        'concurrent_clients': 2,
        'description': 'Medium load - 200 requests at 3 req/sec'
    },
    'heavy': {
        'total_requests': 500,
        'requests_per_second': 5,
        'concurrent_clients': 3,
        'description': 'Heavy load - 500 requests at 5 req/sec'
    },
    'spike': {
        'total_requests': 100,
        'requests_per_second': 20,
        'concurrent_clients': 3,
        'description': 'Spike test - 100 requests burst (20 req/sec)'
    }
}

def run_profile_test(net, profile_name='light', custom_requests=None):
    """
    Run load test based on predefined profile or custom requests
    
    Args:
        net: Mininet network object
        profile_name: Profile name (light/medium/heavy/spike) or 'custom'
        custom_requests: Number of custom requests (only used if profile_name='custom')
    """
    if profile_name == 'custom' and custom_requests:
        profile = {
            'total_requests': custom_requests,
            'requests_per_second': min(5, max(1, custom_requests // 50)),
            'concurrent_clients': min(3, max(1, custom_requests // 100)),
            'description': f'Custom load - {custom_requests} requests'
        }
    elif profile_name in LOAD_PROFILES:
        profile = LOAD_PROFILES[profile_name]
    else:
        info(f'Unknown profile: {profile_name}, using "light" profile\n')
        profile = LOAD_PROFILES['light']
    
    info('\n' + '='*60 + '\n')
    info(f'*** Load Profile: {profile_name.upper()}\n')
    info(f'    {profile["description"]}\n')
    info(f'    Concurrent clients: {profile["concurrent_clients"]}\n')
    info('='*60 + '\n\n')
    
    clients = [net.get('client1'), net.get('client2'), net.get('client3')]
    results = []
    lock = threading.Lock()
    start_time = time.time()
    
    def send_requests(client, num_requests, delay):
        for i in range(num_requests):
            result = client.cmd('curl -s 10.0.0.100 2>/dev/null')
            if 'Server' in result:
                server_num = result.split('Server ')[1][0] if 'Server ' in result else '?'
                with lock:
                    results.append((client.name, server_num, time.time() - start_time))
                    if len(results) % 10 == 0 or len(results) == profile['total_requests']:
                        info(f'[{time.time() - start_time:6.2f}s] Progress: {len(results)}/{profile["total_requests"]} requests\n')
            time.sleep(delay)
    
    # Calculate distribution
    requests_per_client = profile['total_requests'] // profile['concurrent_clients']
    delay = 1.0 / profile['requests_per_second']
    
    # Start threads
    threads = []
    for i in range(profile['concurrent_clients']):
        client = clients[i % len(clients)]
        t = threading.Thread(target=send_requests, args=(client, requests_per_client, delay))
        t.start()
        threads.append(t)
    
    # Wait for completion
    for t in threads:
        t.join()
    
    elapsed_time = time.time() - start_time
    
    # Display results
    info('\n' + '='*60 + '\n')
    info(f'*** Test Results for {profile_name.upper()} Profile\n')
    info('='*60 + '\n')
    info(f'Total requests: {len(results)}\n')
    info(f'Duration: {elapsed_time:.2f} seconds\n')
    info(f'Actual RPS: {len(results)/elapsed_time:.2f}\n')
    info('-'*60 + '\n')
    
    # Count per server
    server_counts = {}
    for _, server, _ in results:
        server_counts[server] = server_counts.get(server, 0) + 1
    
    info('*** Load Distribution:\n')
    for server in sorted(server_counts.keys()):
        count = server_counts[server]
        percentage = (count / len(results)) * 100
        bar = '█' * int(percentage / 2)
        info(f'    Server {server}: {count:3d} requests ({percentage:5.1f}%) {bar}\n')
    
    # Calculate balance score (ideal is 33.33% per server)
    ideal_percentage = 100.0 / 3
    variance = sum((server_counts.get(str(i), 0) / len(results) * 100 - ideal_percentage) ** 2 for i in range(1, 4)) / 3
    balance_score = max(0, 100 - variance)
    
    info('-'*60 + '\n')
    info(f'Balance Score: {balance_score:.1f}/100 (100 = perfect distribution)\n')
    info('='*60 + '\n\n')

def run_load_test(net, duration=30, requests_per_second=2):
    """
    Run automated load test
    
    Args:
        net: Mininet network object
        duration: Test duration in seconds
        requests_per_second: Number of requests per second
    """
    info('\n*** Starting automated load test\n')
    info(f'    Duration: {duration} seconds\n')
    info(f'    Rate: {requests_per_second} requests/second\n')
    info(f'    Total requests: {duration * requests_per_second}\n')
    info('='*60 + '\n')
    
    clients = [net.get('client1'), net.get('client2'), net.get('client3')]
    interval = 1.0 / requests_per_second
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration:
        # Round-robin through clients
        client = clients[request_count % len(clients)]
        
        # Send request
        result = client.cmd('curl -s 10.0.0.100')
        
        # Extract server info
        if 'Server' in result:
            server_num = result.split('Server ')[1][0] if 'Server ' in result else '?'
            elapsed = time.time() - start_time
            info(f'[{elapsed:6.2f}s] {client.name} -> VIP -> Server {server_num}\n')
        
        request_count += 1
        time.sleep(interval)
    
    info('='*60 + '\n')
    info(f'*** Load test completed: {request_count} requests sent\n')
    info('='*60 + '\n')

def run_concurrent_test(net, total_requests=50, concurrent_clients=3):
    """
    Run concurrent load test with multiple clients
    
    Args:
        net: Mininet network object
        total_requests: Total number of requests
        concurrent_clients: Number of concurrent clients
    """
    info('\n*** Starting concurrent load test\n')
    info(f'    Total requests: {total_requests}\n')
    info(f'    Concurrent clients: {concurrent_clients}\n')
    info('='*60 + '\n')
    
    clients = [net.get('client1'), net.get('client2'), net.get('client3')]
    results = []
    lock = threading.Lock()
    
    def send_requests(client, num_requests):
        for i in range(num_requests):
            result = client.cmd('curl -s 10.0.0.100 2>/dev/null')
            if 'Server' in result:
                server_num = result.split('Server ')[1][0] if 'Server ' in result else '?'
                with lock:
                    results.append((client.name, server_num))
                    info(f'{client.name} -> Server {server_num} (Request {len(results)}/{total_requests})\n')
            time.sleep(0.1)
    
    # Calculate requests per client
    requests_per_client = total_requests // concurrent_clients
    
    # Start threads
    threads = []
    for i in range(concurrent_clients):
        client = clients[i % len(clients)]
        t = threading.Thread(target=send_requests, args=(client, requests_per_client))
        t.start()
        threads.append(t)
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Display results
    info('='*60 + '\n')
    info(f'*** Concurrent test completed: {len(results)} requests\n')
    
    # Count per server
    server_counts = {}
    for _, server in results:
        server_counts[server] = server_counts.get(server, 0) + 1
    
    info('*** Distribution:\n')
    for server, count in sorted(server_counts.items()):
        percentage = (count / len(results)) * 100
        info(f'    Server {server}: {count} requests ({percentage:.1f}%)\n')
    info('='*60 + '\n')

def show_load_profiles():
    """Display available load profiles"""
    info('\n' + '='*60 + '\n')
    info('*** Available Load Profiles:\n')
    info('='*60 + '\n')
    for name, config in LOAD_PROFILES.items():
        info(f'  {name:10s} - {config["description"]}\n')
    info('\n  custom N   - Custom load with N requests\n')
    info('='*60 + '\n\n')

def create_topology(auto_test=None, custom_requests=None):
    """Create network topology for load balancer demo"""
    
    info('*** Creating network\n')
    net = Mininet(
        controller=RemoteController,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=True
    )
    
    info('*** Adding controller\n')
    c0 = net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633
    )
    
    info('*** Adding switch\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow10')
    
    info('*** Adding backend servers\n')
    # Backend servers
    h1 = net.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
    h3 = net.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')
    
    info('*** Adding client hosts\n')
    # Client hosts
    client1 = net.addHost('client1', ip='10.0.0.10/24', mac='00:00:00:00:00:10')
    client2 = net.addHost('client2', ip='10.0.0.11/24', mac='00:00:00:00:00:11')
    client3 = net.addHost('client3', ip='10.0.0.12/24', mac='00:00:00:00:00:12')
    
    info('*** Creating links\n')
    # Connect servers to switch (ports 1, 2, 3)
    net.addLink(h1, s1, port2=1)
    net.addLink(h2, s1, port2=2)
    net.addLink(h3, s1, port2=3)
    
    # Connect clients to switch (ports 4, 5, 6)
    net.addLink(client1, s1, port2=4)
    net.addLink(client2, s1, port2=5)
    net.addLink(client3, s1, port2=6)
    
    info('*** Starting network\n')
    net.start()
    
    # Wait for controller connection
    info('*** Waiting for controller connection...\n')
    time.sleep(2)
    
    info('*** Configuring hosts\n')
    
    # Set default gateway for all hosts to go through switch
    for host in [h1, h2, h3, client1, client2, client3]:
        host.cmd('ip route add default dev %s-eth0' % host.name)
    
    # Add ARP entries for virtual IP on all clients
    for client in [client1, client2, client3]:
        client.cmd('arp -s 10.0.0.100 00:00:00:00:00:FF')
    
    info('*** Starting HTTP servers on backend hosts\n')
    # Create web content
    h1.cmd('mkdir -p /tmp/www1')
    h1.cmd('echo "<html><body><h1>Server 1 (h1)</h1><p>IP: 10.0.0.1</p><p>Port: 80</p><p>Time: $(date)</p></body></html>" > /tmp/www1/index.html')
    
    h2.cmd('mkdir -p /tmp/www2')
    h2.cmd('echo "<html><body><h1>Server 2 (h2)</h1><p>IP: 10.0.0.2</p><p>Port: 80</p><p>Time: $(date)</p></body></html>" > /tmp/www2/index.html')
    
    h3.cmd('mkdir -p /tmp/www3')
    h3.cmd('echo "<html><body><h1>Server 3 (h3)</h1><p>IP: 10.0.0.3</p><p>Port: 80</p><p>Time: $(date)</p></body></html>" > /tmp/www3/index.html')
    
    # Start HTTP servers
    h1.cmd('cd /tmp/www1 && python3 -m http.server 80 > /tmp/h1-http.log 2>&1 &')
    h2.cmd('cd /tmp/www2 && python3 -m http.server 80 > /tmp/h2-http.log 2>&1 &')
    h3.cmd('cd /tmp/www3 && python3 -m http.server 80 > /tmp/h3-http.log 2>&1 &')
    
    time.sleep(2)
    
    # Verify servers are running
    info('*** Verifying HTTP servers...\n')
    for i, host in enumerate([h1, h2, h3], 1):
        result = host.cmd('netstat -tulpn | grep :80')
        if ':80' in result:
            info(f'    ✓ Server {i} (h{i}) HTTP server running\n')
        else:
            info(f'    ✗ Server {i} (h{i}) HTTP server FAILED\n')
    
    info('\n*** Network ready!\n')
    info('='*60 + '\n')
    info('*** Configuration:\n')
    info('    Virtual IP: 10.0.0.100 (Load Balancer)\n')
    info('    Backend Servers:\n')
    info('      - h1: 10.0.0.1 (MAC: 00:00:00:00:00:01, Port: 1)\n')
    info('      - h2: 10.0.0.2 (MAC: 00:00:00:00:00:02, Port: 2)\n')
    info('      - h3: 10.0.0.3 (MAC: 00:00:00:00:00:03, Port: 3)\n')
    info('    Clients:\n')
    info('      - client1: 10.0.0.10 (Port: 4)\n')
    info('      - client2: 10.0.0.11 (Port: 5)\n')
    info('      - client3: 10.0.0.12 (Port: 6)\n')
    info('='*60 + '\n')
    info('\n*** Test commands:\n')
    info('    pingall                          - Test connectivity\n')
    info('    client1 ping -c 2 10.0.0.1       - Ping server directly\n')
    info('    client1 curl 10.0.0.1            - Test server directly\n')
    info('    client1 curl 10.0.0.100          - Test load balancer\n')
    info('    client1 curl -v 10.0.0.100       - Verbose test\n')
    info('    xterm client1                    - Open terminal\n')
    info('\n*** Automated test commands:\n')
    info('    py run_profile_test(net, "light")       - Light load test\n')
    info('    py run_profile_test(net, "medium")      - Medium load test\n')
    info('    py run_profile_test(net, "heavy")       - Heavy load test\n')
    info('    py run_profile_test(net, "spike")       - Spike load test\n')
    info('    py run_profile_test(net, "custom", 300) - Custom 300 requests\n')
    info('    py show_load_profiles()                 - Show all profiles\n')
    info('    py run_load_test(net, duration=30, requests_per_second=2)\n')
    info('    py run_concurrent_test(net, total_requests=50, concurrent_clients=3)\n')
    info('\n*** Debug commands:\n')
    info('    dpctl dump-flows                 - Show OpenFlow rules\n')
    info('    sh ovs-ofctl dump-flows s1       - Show switch flows\n')
    info('\n')
    
    # Run automated test if specified
    if auto_test:
        if auto_test == 'custom' and custom_requests:
            info(f'*** Running automated CUSTOM test ({custom_requests} requests)...\n')
            time.sleep(2)
            run_profile_test(net, 'custom', custom_requests)
        elif auto_test in LOAD_PROFILES:
            info(f'*** Running automated {auto_test.upper()} load test...\n')
            time.sleep(2)
            run_profile_test(net, auto_test)
        else:
            info(f'*** Unknown profile: {auto_test}\n')
            show_load_profiles()
    else:
        # Run initial quick test
        info('*** Running quick automated test (10 requests)...\n')
        time.sleep(1)
        
        clients = [client1, client2, client3]
        for i in range(10):
            client = clients[i % len(clients)]
            result = client.cmd('curl -s 10.0.0.100 2>/dev/null')
            if 'Server' in result:
                server_num = result.split('Server ')[1][0] if 'Server ' in result else '?'
                info(f'Request {i+1}: {client.name} -> Server {server_num}\n')
            time.sleep(0.5)
        
        info('='*60 + '\n')
        info('*** Quick test completed!\n')
    
    info('='*60 + '\n')
    info('*** Entering CLI - use "py run_profile_test(net, \'medium\')" for tests\n')
    info('='*60 + '\n\n')
    
    CLI(net)
    
    info('*** Stopping network\n')
    # Cleanup
    h1.cmd('pkill -f "python3 -m http.server"')
    h2.cmd('pkill -f "python3 -m http.server"')
    h3.cmd('pkill -f "python3 -m http.server"')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    # Clean up any existing mininet
    os.system('sudo mn -c > /dev/null 2>&1')
    
    # Parse command line arguments
    auto_test = None
    custom_requests = None
    
    if len(sys.argv) > 1:
        profile = sys.argv[1].lower()
        
        if profile in ['light', 'medium', 'heavy', 'spike']:
            auto_test = profile
        elif profile == 'custom' and len(sys.argv) > 2:
            auto_test = 'custom'
            try:
                custom_requests = int(sys.argv[2])
                if custom_requests <= 0:
                    info('Error: Number of requests must be positive\n')
                    sys.exit(1)
            except ValueError:
                info('Error: Invalid number of requests\n')
                info('Usage: sudo python3 topology.py custom <number>\n')
                sys.exit(1)
        elif profile in ['help', '-h', '--help']:
            info('\n' + '='*60 + '\n')
            info('SDN Load Balancer - Usage\n')
            info('='*60 + '\n')
            info('Interactive mode:\n')
            info('  sudo python3 topology.py\n\n')
            info('Automated load tests:\n')
            info('  sudo python3 topology.py light       # 50 requests, 1 req/s\n')
            info('  sudo python3 topology.py medium      # 200 requests, 3 req/s\n')
            info('  sudo python3 topology.py heavy       # 500 requests, 5 req/s\n')
            info('  sudo python3 topology.py spike       # 100 requests burst\n')
            info('  sudo python3 topology.py custom 300  # Custom 300 requests\n')
            info('='*60 + '\n\n')
            sys.exit(0)
        else:
            info(f'\nError: Unknown profile "{profile}"\n')
            info('Available profiles: light, medium, heavy, spike, custom\n')
            info('Use "sudo python3 topology.py help" for more info\n\n')
            sys.exit(1)
    
    create_topology(auto_test, custom_requests)