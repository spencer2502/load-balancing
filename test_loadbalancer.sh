#!/bin/bash

echo "=========================================="
echo "Testing Load Balancer"
echo "=========================================="

VIRTUAL_IP="10.0.0.100"

echo "Sending 10 requests to load balancer..."
echo ""

for i in {1..10}; do
    echo "Request $i:"
    curl -s $VIRTUAL_IP | grep -E "<h1>|<p>IP:"
    echo ""
    sleep 1
done

echo "Test complete!"
echo "Check POX controller logs to see load distribution"

