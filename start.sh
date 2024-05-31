#!/bin/bash

# Ensure the logs directory exists with proper permissions
mkdir -p /app/logs
chmod 775 /app/logs

# Start ollama serve in the background and log errors
ollama serve > /dev/null 2> /app/logs/ollama_error.log &

# Keep the container running
tail -f /dev/null
