#!/bin/bash

echo "=========================================="
echo "SDN Load Balancer - Project Setup"
echo "=========================================="

# Create project structure
mkdir -p ~/sdn-loadbalancer
cd ~/sdn-loadbalancer

echo "Creating project files..."

# Create POX controller directory
mkdir -p ~/pox/pox/misc

echo "✓ Project structure created"
echo ""
echo "Next steps:"
echo "1. Save the POX controller code to: ~/pox/pox/misc/load_balancer.py"
echo "2. Save the topology code to: ~/sdn-loadbalancer/topology.py"
echo "3. Save the traffic generator to: ~/sdn-loadbalancer/traffic_generator.py"
echo "4. Run: ./start_all.sh"
echo ""
