#!/bin/bash

echo "=========================================="
echo "Starting Mininet Topology"
echo "=========================================="
echo "Make sure POX controller is running first!"
echo ""

# Clean up any existing mininet
sudo mn -c

# Start topology
sudo python3 ~/sdn-loadbalancer/topology.py

