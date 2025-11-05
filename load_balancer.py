"""
SDN Load Balancer Controller for POX with Dashboard Integration
Save as: ~/pox/pox/misc/load_balancer.py
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
from pox.lib.packet.arp import arp
from pox.lib.recoco import Timer
import time
import json

try:
    import urllib.request
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

log = core.getLogger()

# Configuration
VIRTUAL_IP = IPAddr("10.0.0.100")
VIRTUAL_MAC = EthAddr("00:00:00:00:00:FF")
API_SERVER = "http://localhost:8080"

SERVERS = [
    {"ip": IPAddr("10.0.0.1"), "mac": EthAddr("00:00:00:00:00:01"), "port": 1},
    {"ip": IPAddr("10.0.0.2"), "mac": EthAddr("00:00:00:00:00:02"), "port": 2},
    {"ip": IPAddr("10.0.0.3"), "mac": EthAddr("00:00:00:00:00:03"), "port": 3}
]

class LoadBalancer:
    def __init__(self, connection, algorithm="round_robin"):
        self.connection = connection
        self.algorithm = algorithm
        self.server_index = 0
        self.stats = {
            "total_requests": 0,
            "servers": {str(s["ip"]): {"requests": 0, "load": 0} for s in SERVERS},
            "start_time": time.time()
        }
        
        connection.addListeners(self)
        
        log.info("="*60)
        log.info("Load Balancer Controller initialized")
        log.info("Algorithm: %s", algorithm)
        log.info("Virtual IP: %s (MAC: %s)", VIRTUAL_IP, VIRTUAL_MAC)
        log.info("Backend Servers:")
        for i, srv in enumerate(SERVERS, 1):
            log.info("  %d. %s (MAC: %s, Port: %d)", i, srv["ip"], srv["mac"], srv["port"])
        if HAS_URLLIB:
            log.info("Dashboard API: %s", API_SERVER)
        else:
            log.info("Dashboard API: Disabled (urllib not available)")
        log.info("="*60)
        
        # Start periodic stats reporting
        Timer(5, self._report_stats, recurring=True)
    
    def _get_next_server(self):
        """Select next server based on algorithm"""
        if self.algorithm == "round_robin":
            server = SERVERS[self.server_index]
            self.server_index = (self.server_index + 1) % len(SERVERS)
            return server
        elif self.algorithm == "least_connections":
            # Find server with least requests
            server = min(SERVERS, key=lambda s: self.stats["servers"][str(s["ip"])]["requests"])
            return server
        else:
            # Default to round-robin
            server = SERVERS[self.server_index]
            self.server_index = (self.server_index + 1) % len(SERVERS)
            return server
    
    def _send_to_dashboard(self, data):
        """Send stats update to dashboard API"""
        if not HAS_URLLIB:
            return
        
        try:
            req = urllib.request.Request(
                f"{API_SERVER}/update",
                data=json.dumps(data).encode(),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=1)
        except (urllib.error.URLError, Exception) as e:
            # Silently ignore connection errors to not spam logs
            pass
    
    def _report_stats(self):
        """Report current statistics"""
        uptime = time.time() - self.stats["start_time"]
        rps = self.stats["total_requests"] / uptime if uptime > 0 else 0
        
        log.info("="*60)
        log.info("Load Balancer Statistics")
        log.info("Total requests: %d, RPS: %.2f", self.stats["total_requests"], rps)
        for server_ip, data in self.stats["servers"].items():
            percentage = (data["requests"] / self.stats["total_requests"] * 100) if self.stats["total_requests"] > 0 else 0
            log.info("  Server %s: %d requests (%.1f%%)", server_ip, data["requests"], percentage)
        log.info("="*60)
    
    def _handle_PacketIn(self, event):
        """Handle incoming packets"""
        packet = event.parsed
        
        if not packet.parsed:
            return
        
        # Handle ARP requests
        if packet.type == ethernet.ARP_TYPE:
            arp_packet = packet.payload
            if arp_packet.protodst == VIRTUAL_IP and arp_packet.opcode == arp.REQUEST:
                self._handle_arp(event, arp_packet)
                return
        
        # Handle IP packets
        if packet.type == ethernet.IP_TYPE:
            ip_packet = packet.payload
            
            # Request to virtual IP
            if ip_packet.dstip == VIRTUAL_IP:
                self._handle_request(event, packet, ip_packet)
                return
            
            # Response from server
            elif any(ip_packet.srcip == srv["ip"] for srv in SERVERS):
                self._handle_response(event, packet, ip_packet)
                return
    
    def _handle_arp(self, event, arp_packet):
        """Handle ARP requests for virtual IP"""
        log.info("ARP request for %s from %s", VIRTUAL_IP, arp_packet.protosrc)
        
        # Create ARP reply
        arp_reply = arp()
        arp_reply.hwsrc = VIRTUAL_MAC
        arp_reply.hwdst = arp_packet.hwsrc
        arp_reply.opcode = arp.REPLY
        arp_reply.protosrc = VIRTUAL_IP
        arp_reply.protodst = arp_packet.protosrc
        
        # Wrap in ethernet frame
        ether = ethernet()
        ether.type = ethernet.ARP_TYPE
        ether.dst = arp_packet.hwsrc
        ether.src = VIRTUAL_MAC
        ether.payload = arp_reply
        
        # Send packet
        msg = of.ofp_packet_out()
        msg.data = ether.pack()
        msg.actions.append(of.ofp_action_output(port=event.port))
        self.connection.send(msg)
        
        log.info("ARP reply sent: %s is at %s", VIRTUAL_IP, VIRTUAL_MAC)
    
    def _handle_request(self, event, packet, ip_packet):
        """Handle request to virtual IP - load balance to server"""
        
        # Select server
        server = self._get_next_server()
        
        # Update statistics
        self.stats["total_requests"] += 1
        self.stats["servers"][str(server["ip"])]["requests"] += 1
        
        log.info("Request #%d: %s -> %s (forwarding to %s via port %d)", 
                self.stats["total_requests"], ip_packet.srcip, VIRTUAL_IP, 
                server["ip"], server["port"])
        
        # Send to dashboard
        self._send_to_dashboard({
            "client_ip": str(ip_packet.srcip),
            "server_ip": str(server["ip"]),
            "timestamp": time.time()
        })
        
        # Install flow rule
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 10
        msg.hard_timeout = 30
        msg.priority = 100
        
        # Rewrite destination to selected server
        msg.actions.append(of.ofp_action_dl_addr.set_dst(server["mac"]))
        msg.actions.append(of.ofp_action_nw_addr.set_dst(server["ip"]))
        msg.actions.append(of.ofp_action_output(port=server["port"]))
        
        msg.data = event.ofp
        self.connection.send(msg)
    
    def _handle_response(self, event, packet, ip_packet):
        """Handle response from server - rewrite to virtual IP"""
        
        server = next((s for s in SERVERS if ip_packet.srcip == s["ip"]), None)
        if not server:
            return
        
        log.info("Response: %s -> %s (rewriting source to %s)", 
                server["ip"], ip_packet.dstip, VIRTUAL_IP)
        
        # Install reverse flow
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 10
        msg.hard_timeout = 30
        msg.priority = 100
        
        # Rewrite source to virtual IP
        msg.actions.append(of.ofp_action_nw_addr.set_src(VIRTUAL_IP))
        msg.actions.append(of.ofp_action_dl_addr.set_src(VIRTUAL_MAC))
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        
        msg.data = event.ofp
        self.connection.send(msg)


def launch(algorithm="round_robin"):
    """
    Launch the load balancer
    
    Args:
        algorithm: Load balancing algorithm (round_robin or least_connections)
    """
    def start_switch(event):
        log.info("Switch %s connected", event.connection)
        LoadBalancer(event.connection, algorithm)
    
    log.info("="*60)
    log.info("Starting SDN Load Balancer Controller")
    log.info("Algorithm: %s", algorithm)
    log.info("="*60)
    
    core.openflow.addListenerByName("ConnectionUp", start_switch)