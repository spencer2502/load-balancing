#!/bin/bash

echo "=========================================="
echo "SDN Load Balancer - Starting All Services"
echo "=========================================="

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "Installing tmux..."
    sudo apt-get update && sudo apt-get install -y tmux
fi

# Kill existing session
tmux kill-session -t sdn-lb 2>/dev/null

# Create new session
tmux new-session -d -s sdn-lb -n controller

# Window 1: POX Controller
tmux send-keys -t sdn-lb:controller "cd ~/pox && ./pox.py log.level --INFO openflow.of_01 --port=6633 misc.load_balancer --algorithm=round_robin" C-m

# Wait for controller to start
sleep 3

# Window 2: Mininet
tmux new-window -t sdn-lb -n mininet
tmux send-keys -t sdn-lb:mininet "sudo python3 ~/sdn-loadbalancer/topology.py" C-m

# Window 3: Dashboard instructions
tmux new-window -t sdn-lb -n dashboard
tmux send-keys -t sdn-lb:dashboard "echo '========================================'" C-m
tmux send-keys -t sdn-lb:dashboard "echo 'Open the React dashboard in your browser'" C-m
tmux send-keys -t sdn-lb:dashboard "echo '========================================'" C-m
tmux send-keys -t sdn-lb:dashboard "echo ''" C-m
tmux send-keys -t sdn-lb:dashboard "echo 'The dashboard shows real-time statistics'" C-m
tmux send-keys -t sdn-lb:dashboard "echo 'matching the POX controller output'" C-m
tmux send-keys -t sdn-lb:dashboard "echo ''" C-m
tmux send-keys -t sdn-lb:dashboard "echo 'To generate traffic:'" C-m
tmux send-keys -t sdn-lb:dashboard "echo '1. In Mininet window: xterm client1'" C-m
tmux send-keys -t sdn-lb:dashboard "echo '2. In xterm: python3 ~/sdn-loadbalancer/traffic_generator.py'" C-m
tmux send-keys -t sdn-lb:dashboard "echo ''" C-m
tmux send-keys -t sdn-lb:dashboard "echo 'Or test manually:'" C-m
tmux send-keys -t sdn-lb:dashboard "echo 'mininet> client1 curl 10.0.0.100'" C-m

echo ""
echo "✓ All services started in tmux session 'sdn-lb'"
echo ""
echo "To view:"
echo "  tmux attach -t sdn-lb"
echo ""
echo "Switch between windows:"
echo "  Ctrl+b then 0 (Controller)"
echo "  Ctrl+b then 1 (Mininet)"
echo "  Ctrl+b then 2 (Dashboard Info)"
echo ""
echo "To detach: Ctrl+b then d"
echo "To stop all: tmux kill-session -t sdn-lb"
echo ""

