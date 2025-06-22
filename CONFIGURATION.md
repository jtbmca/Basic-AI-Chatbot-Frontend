# Setting Up Configuration

This application now uses environment variables for configuration to make it portable across different systems.

## Quick Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create your configuration file:**
   ```bash
   cp config.env.example .env
   ```

3. **Edit the .env file:**
   - Set `BERT_MODEL_PATH` to your actual BERT model location
   - Adjust other paths as needed

## Configuration Options

### Required (if using BERT):
- `BERT_MODEL_PATH`: Path to your local BERT model directory

### Optional:
- `OLLAMA_API_URL`: Ollama API endpoint (default: http://localhost:11434/api/generate)
- `CONVERSATIONS_DIR`: Directory for conversation files (default: conversations)
- `CUSTOM_PERSONAS_FILE`: File for custom personas (default: custom_personas.json)
- `HISTORY_FILE`: Legacy history file (default: chat_history.json)

## Example .env file:

```
BERT_MODEL_PATH=/home/username/models/bert-base-uncased-mrpc
OLLAMA_API_URL=http://localhost:11434/api/generate
CONVERSATIONS_DIR=my_conversations
```

## Without .env file:

The application will use sensible defaults and try to detect the model path automatically. If BERT model is not found, the BERT option will show an error message with instructions.

## For Different Operating Systems:

### Windows:
```
BERT_MODEL_PATH=C:\Users\YourName\Documents\models\bert-model
```

### Linux/Mac:
```
BERT_MODEL_PATH=/home/yourname/models/bert-model
```

## Troubleshooting:

If you see "BERT model not found" errors:
1. Check that the path in your .env file is correct
2. Verify the model files exist at that location
3. Make sure you have read permissions to the model directory
