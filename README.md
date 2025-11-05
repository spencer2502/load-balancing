# ⚡ SDN Load Balancer with Real-Time Dashboard (Mininet + POX Controller)

A Software-Defined Networking (SDN) load balancer example using the POX controller and Mininet, with a live web dashboard that visualizes traffic flow, load distribution and performance metrics in real time.

---

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Execution Steps](#execution-steps)
- [Dashboard Access](#dashboard-access)
- [Mininet Commands](#mininet-commands)
- [API Endpoints](#api-endpoints)
- [Cautions & Notes](#cautions--notes)
- [Sample Workflow](#sample-workflow)
- [Author](#author)
- [License](#license)

---

## Overview
This project:
- Distributes traffic among backend servers using a POX-based load balancer.
- Exposes runtime stats via a lightweight HTTP API server.
- Provides a static dashboard (dashboard.html) that polls the API and visualizes metrics and recent requests.
- Includes Mininet topology and test profiles to simulate traffic (light, medium, heavy, spike).

## Architecture
Dashboard → API Server → POX Controller → Mininet Topology

      ┌──────────────────────────┐
      │   Dashboard (HTML/JS)    │
      │  → http://localhost:8080 │
      └────────────┬─────────────┘
                   ▼
         ┌────────────────────┐
         │  API Server (Python)│
         │     api_server.py   │
         └────────┬────────────┘
                    ▼
          ┌─────────────────────┐
          │   POX Controller    │
          │  load_balancer.py   │
          └────────┬────────────┘
                   ▼
           ┌──────────────────┐
           │   Mininet Topo    │
           │   topology.py     │
           └──────────────────┘

## Features
- Round-robin and least-connections strategies (controller)
- Real-time stats and request log (dashboard)
- Automated Mininet test profiles: light, medium, heavy, spike
- Simple HTTP API for stats and updates

## Project Structure
sdn-loadbalancer/
- api_server.py        — REST API server (dashboard backend)
- topology.py          — Mininet topology + test harness
- dashboard.html       — Static dashboard UI
- load_balancer.py     — POX controller module (place under ~/pox/pox/misc/)

## Requirements
- Ubuntu 20.04+ (or similar)
- Python 3.8+
- Mininet (2.3+)
- POX controller
- Open vSwitch (ovs)
- curl (optional)

## Installation
1. Clone repo:
```bash
cd ~
git clone https://github.com/<your-username>/sdn-loadbalancer.git
cd sdn-loadbalancer
```

2. Install Mininet (if not installed):
```bash
sudo apt update
sudo apt install mininet -y
```

3. Get POX (if not present):
```bash
cd ~
git clone https://github.com/noxrepo/pox.git
```

4. Copy controller module into POX:
```bash
cp ~/sdn-loadbalancer/load_balancer.py ~/pox/pox/misc/
# ensure file is ~/pox/pox/misc/load_balancer.py
```

## Execution Steps

1) Start API server (dashboard backend):
```bash
cd ~/sdn-loadbalancer
python3 api_server.py
# runs on http://localhost:8080
```

2) Launch POX controller (new terminal):
```bash
cd ~/pox
./pox.py log.level --DEBUG misc.load_balancer --algorithm=round_robin
# or --algorithm=least_connections
```

3) Start Mininet topology (new terminal):
```bash
cd ~/sdn-loadbalancer
sudo python3 topology.py medium
# profiles: light, medium, heavy, spike, custom <N>
```

4) Open dashboard:
- Open file: file:///home/spencer/sdn-loadbalancer/dashboard.html
- Or check API: http://localhost:8080/stats



## Mininet Commands (use in mininet> prompt)
- pingall
- ping between clients/servers:
  client1 ping -c 2 10.0.0.1
- curl from a client:
  client1 curl 10.0.0.100

Programmatic test hooks inside topology.py:
```python
py run_profile_test(net, "light")
py run_profile_test(net, "medium")
py run_profile_test(net, "heavy")
py run_profile_test(net, "spike")
py run_profile_test(net, "custom", 300)
```

## API Endpoints
- GET /stats — Return aggregated stats for dashboard
- POST /update — Controller posts per-request updates (used by POX)
- POST /reset — Reset statistics


## Cautions & Notes
- Start api_server.py before launching POX and Mininet.
- Use sudo when running topology.py.
- Ensure port 8080 is free for the API server.
- If dashboard shows "Disconnected", confirm API server is running and reachable.
- Clean Mininet state if needed:
```bash
sudo mn -c
```

## Sample Workflow
Terminal 1 — API Server:
```bash
cd ~/sdn-loadbalancer
python3 api_server.py
```

Terminal 2 — POX Controller:
```bash
cd ~/pox
./pox.py log.level --DEBUG misc.load_balancer --algorithm=round_robin
```

Terminal 3 — Mininet Topology:
```bash
cd ~/sdn-loadbalancer
sudo python3 topology.py medium
```

Open dashboard:
file:///home/spencer/sdn-loadbalancer/dashboard.html

## Author
Spencer — B.Tech Final Year Student

## License
MIT License — free to use and modify with attribution.

## Tip
Use Chrome or Edge for best dashboard rendering. To quickly validate API connectivity:
http://localhost:8080/stats

