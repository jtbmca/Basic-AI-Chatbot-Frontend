#!/bin/bash
# Simple setup script for the chat interface

echo "Setting up Tibs Chat Interface..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating configuration file..."
    cp config.env.example .env
    echo "Configuration file created as .env"
    echo "Please edit .env to set your BERT model path and other settings"
else
    echo ".env file already exists"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file to set your BERT model path"
echo "2. Make sure Ollama is running"
echo "3. Run: streamlit run app.py"
