#!/bin/bash
# Run the DeepAgents PrintShop Author Agent

echo "Starting DeepAgents PrintShop Author Agent..."
echo ""

# Navigate to the agents directory
cd /app/agents/research_agent

# Run the agent
python agent.py "$@"
