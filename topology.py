#!/usr/bin/env python3
"""
Fixed SDN Load Balancer Topology
Save as: ~/sdn-loadbalancer/topology.py
Run with: sudo python3 topology.py
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import time
import os

def create_topology():
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
    info('\n*** Debug commands:\n')
    info('    dpctl dump-flows                 - Show OpenFlow rules\n')
    info('    sh ovs-ofctl dump-flows s1       - Show switch flows\n')
    info('\n')
    
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
    create_topology()