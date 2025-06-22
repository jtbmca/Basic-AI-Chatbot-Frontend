# Tibs Chat Interface

A local Streamlit-based chat client with robust conversation management, persona system, and multi-model AI support.

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure paths:**
   ```bash
   cp config.env.example .env
   # Edit .env file with your settings
   ```

3. **Start the application:**
   ```bash
   streamlit run app.py
   ```

## ⚙️ Configuration

The application now uses environment variables for configuration. See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions.

### Key Environment Variables:

- `BERT_MODEL_PATH`: Path to your local BERT model (required for BERT functionality)
- `OLLAMA_API_URL`: Ollama API endpoint (default: http://localhost:11434/api/generate)
- `CONVERSATIONS_DIR`: Directory for conversation storage (default: conversations)

### Example .env file:
```
BERT_MODEL_PATH=/home/username/models/bert-base-uncased-mrpc
OLLAMA_API_URL=http://localhost:11434/api/generate
CONVERSATIONS_DIR=my_conversations
```

## 🎯 Features

- **Multi-Model Support**: Ollama, HuggingFace, local BERT, API-ready for OpenAI/Anthropic
- **Conversation Management**: Multiple conversations, search, import/export
- **Persona System**: Predefined and custom AI personalities
- **Portable Configuration**: Environment variable based setup
- **Error Handling**: Graceful degradation when models aren't available

## 📁 Project Structure

```
├── app.py                  # Main application
├── requirements.txt        # Python dependencies  
├── config.env.example     # Configuration template
├── setup.sh/.bat          # Setup scripts
├── CONFIGURATION.md       # Detailed configuration guide
├── conversations/         # Conversation storage
├── custom_personas.json   # Custom AI personas
└── chat_history.json      # Legacy history file
```

## 🔧 Troubleshooting

### "BERT model not found" Error

1. Set the correct path in your `.env` file:
   ```
   BERT_MODEL_PATH=/path/to/your/bert/model
   ```

2. Or disable BERT by not selecting it in the interface

### "Cannot write to conversations directory" Error

1. Check file permissions on the conversations directory
2. Set a different directory in `.env`:
   ```
   CONVERSATIONS_DIR=/path/to/writable/directory
   ```

### Ollama Connection Issues

1. Make sure Ollama is running: `ollama serve`
2. Check the API URL in your `.env` file
3. Test with: `curl http://localhost:11434/api/tags`

## 📖 Documentation ( In Documentation Folder)

- [Configuration Guide](CONFIGURATION.md) - Detailed setup instructions
- [Custom Personas](CUSTOM_PERSONAS.md) - Persona management features  
- [Conversation Management](CONVERSATION_MANAGEMENT.md) - Multi-conversation features
- [Features Overview](FEATURES_OVERVIEW.md) - Complete feature list

## 🆕 Recent Changes

- **Portable Configuration**: Removed hardcoded paths, added environment variable support
- **Better Error Handling**: Graceful degradation when models aren't available
- **Setup Scripts**: Automated setup for Windows and Unix systems
- **Configuration Validation**: Real-time validation with helpful error messages

## 🔒 Security Notes

- All file paths are now configurable via environment variables
- Input validation and error handling improved
- No sensitive data hardcoded in the application

## 📋 Requirements

- Python 3.8+
- Streamlit
- PyTorch + Transformers (for local models)
- Ollama (for Ollama models)
- python-dotenv (for .env file support)

## 🎮 Usage

1. **Select Model**: Choose from available Ollama models or local models
2. **Set Persona**: Pick predefined personas or create custom ones
3. **Start Chatting**: Type messages and get AI responses
4. **Manage Conversations**: Create, rename, search, and organize conversations
5. **Export/Import**: Backup and share conversations and personas

---

*Built for users who need professional conversation management with local AI models.*
