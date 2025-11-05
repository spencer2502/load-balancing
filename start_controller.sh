#!/bin/bash

echo "=========================================="
echo "Starting POX Load Balancer Controller"
echo "=========================================="

cd ~/pox

# Kill any existing POX instances
pkill -f pox.py

# Start POX with load balancer
./pox.py log.level --DEBUG openflow.of_01 --port=6633 misc.load_balancer --algorithm=round_robin

