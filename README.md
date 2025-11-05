# SDN Load Balancer Project

A complete Software Defined Networking (SDN) load balancer implementation using Mininet and POX controller with real-time visualization dashboard.

## Features

- **Load Balancing Algorithms**: Round Robin, Least Connections
- **Real-time Dashboard**: Interactive visualization of traffic and server loads
- **Traffic Patterns**: Simulates idle, light, medium, heavy, and spike traffic
- **Network Topology**: 3 backend servers, 3 clients, 1 switch
- **Monitoring**: Real-time stats and connection logs

## Architecture

```
Clients (10.0.0.10-12)
         |
         v
    Load Balancer (10.0.0.100)
         |
    +---------+---------+
    |         |         |
   S1        S2        S3
(10.0.0.1) (10.0.0.2) (10.0.0.3)
```

## Installation

1. Install dependencies:
```bash
sudo apt-get update
sudo apt-get install -y mininet python3-pip tmux
pip3 install requests
```

2. Clone/Download POX:
```bash
cd ~
git clone https://github.com/noxrepo/pox.git
```

3. Setup project:
```bash
cd ~/sdn-loadbalancer
chmod +x *.sh
./setup_project.sh
```

## Usage

### Quick Start (Recommended)

Start everything at once using tmux:
```bash
./start_all.sh
```

Then attach to the session:
```bash
tmux attach -t sdn-lb
```

### Manual Start

1. Start POX Controller (Terminal 1):
```bash
./start_controller.sh
```

2. Start Mininet Topology (Terminal 2):
```bash
./start_topology.sh
```

3. Open Dashboard (Browser):
   - Open the React dashboard artifact
   - Watch real-time stats

4. Generate Traffic (Terminal 3 or Mininet xterm):
```bash
# In Mininet CLI
mininet> xterm client1

# In the xterm window
python3 ~/sdn-loadbalancer/traffic_generator.py
```

### Testing

Quick test from Mininet CLI:
```bash
mininet> client1 curl 10.0.0.100
mininet> client2 curl 10.0.0.100
mininet> client3 curl 10.0.0.100
```

Or use the test script:
```bash
./test_loadbalancer.sh
```

## Traffic Patterns

The traffic generator simulates realistic patterns:

- **Idle**: 0-2 RPS (5 seconds)
- **Light**: 2-5 RPS (10 seconds)
- **Medium**: 5-15 RPS (15 seconds)
- **Heavy**: 15-30 RPS (10 seconds)
- **Spike**: 30-50 RPS (5 seconds)

Generate specific pattern:
```bash
python3 traffic_generator.py spike
python3 traffic_generator.py heavy
```

## Dashboard Features

- **Real-time Stats**: Total requests, RPS, traffic pattern
- **Server Visualization**: Live load bars for each server
- **Traffic History**: 20-second rolling graph
- **Connection Log**: Recent packet forwarding events
- **Animated Packets**: Visual representation of traffic flow

## Troubleshooting

### Port Already in Use
```bash
sudo netstat -tulpn | grep 6633
pkill -f pox.py
```

### Mininet Cleanup
```bash
sudo mn -c
```

### View All Processes
```bash
tmux attach -t sdn-lb
# Ctrl+b then 0/1/2 to switch windows
# Ctrl+b then d to detach
```

### Stop Everything
```bash
tmux kill-session -t sdn-lb
sudo mn -c
```

## File Structure

```
~/sdn-loadbalancer/
├── topology.py              # Mininet network topology
├── traffic_generator.py     # Traffic simulation
├── start_controller.sh      # POX startup script
├── start_topology.sh        # Mininet startup script
├── start_all.sh            # Start everything with tmux
├── test_loadbalancer.sh    # Quick test script
└── README.md               # This file

~/pox/pox/misc/
└── load_balancer.py        # POX controller code
```

## Configuration

Edit `~/pox/pox/misc/load_balancer.py` to change:
- Virtual IP address
- Server IPs and MACs
- Load balancing algorithm

Edit `~/sdn-loadbalancer/topology.py` to modify:
- Network topology
- Bandwidth and delay
- Number of servers/clients

## Algorithms

### Round Robin
Distributes requests evenly across all servers in rotation.

### Least Connections
Routes to the server with the fewest active connections.

Change algorithm:
```bash
./pox.py misc.load_balancer --algorithm=least_connections
```

## Monitoring

Watch POX controller logs:
```bash
tmux attach -t sdn-lb
# Switch to controller window (Ctrl+b then 0)
```

Watch Mininet:
```bash
tmux attach -t sdn-lb
# Switch to mininet window (Ctrl+b then 1)
```

## Credits

Built with:
- Mininet - Network emulator
- POX - OpenFlow controller
- React - Dashboard UI

