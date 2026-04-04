#!/bin/bash
# Initialize Ollama with a default model

echo "Waiting for Ollama to start..."
sleep 10

echo "Pulling llama2 model..."
ollama pull llama2

echo "Ollama initialization complete!"
echo "Available models:"
ollama list