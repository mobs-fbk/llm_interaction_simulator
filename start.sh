#!/bin/bash

# Start ollama serve in the background
ollama serve > /dev/null 2>&1 &

# Keep the container running
tail -f /dev/null
