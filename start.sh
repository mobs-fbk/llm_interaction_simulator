#!/bin/bash

# Start ollama serve in the background and log errors
ollama serve > /dev/null 2> ollama_error.log &

# Keep the container running
tail -f /dev/null