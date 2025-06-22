# System Prompt/Persona Features

## Overview
The chat interface now includes comprehensive system prompt and persona functionality to customize how the AI assistant behaves.

## Features Added

### 🎭 Predefined Personas
Choose from 8 predefined personas in the sidebar:
- **Default**: No system prompt (original behavior)
- **Helpful Assistant**: Polite and accurate information provider
- **Code Expert**: Expert programmer with technical explanations
- **Creative Writer**: Assists with storytelling and creative expression
- **Teacher**: Patient educator with examples and comprehension checks
- **Scientist**: Evidence-based explanations and scientific thinking
- **Philosopher**: Explores deep questions about existence and ethics
- **Comedian**: Witty humor while remaining helpful
- **Professional**: Formal business assistant focused on practical solutions

### ✏️ Custom System Prompts
- Text area for writing custom system prompts
- Overrides selected persona when custom text is provided
- Real-time preview of active system prompt
- Persistent across sessions (saved with chat history)

### 🔄 Integration with All Model Types
System prompts now work with:
- **Ollama models**: Added to conversation context as system message
- **HuggingFace models**: Prepended to input for context-aware generation
- **BERT models**: (Not applicable for generative tasks)
- **API models**: Ready for integration when API keys are configured

### 💾 Enhanced Data Persistence
- Chat history format upgraded to include system prompts
- Backwards compatibility with old history files
- Export includes system prompt information
- Clear conversation resets both messages and system prompt

### 🎨 UI Improvements
- **Sidebar organization**: System prompt controls in dedicated section
- **Active prompt indicator**: Shows current system prompt in main chat area
- **Expandable preview**: View full system prompt text
- **Reset functionality**: Quick reset button for persona settings
- **Enhanced export**: Includes system prompt in JSON exports

## Usage Examples

### Setting a Code Expert Persona
1. Select "Code Expert" from the persona dropdown
2. The system prompt automatically loads: "You are an expert programmer..."
3. Start chatting - the assistant will provide code examples and technical explanations

### Creating a Custom Persona
1. Type your custom instructions in the "Custom System Prompt" text area
2. Example: "You are a helpful cooking assistant who provides easy recipes..."
3. The custom prompt overrides any selected persona
4. Chat normally - responses will follow your custom instructions

### Switching Personas Mid-Conversation
1. Change the persona selection or edit the custom prompt
2. New system prompt takes effect immediately for subsequent messages
3. Previous conversation history is preserved
4. Export or clear to start fresh with new persona

## Technical Implementation

### Data Structure
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "system_prompt": "You are a helpful assistant..."
}
```

### Model Integration
- **Ollama**: System prompt prepended to conversation context
- **HuggingFace**: System prompt + user input format for coherent generation
- **Future APIs**: Ready for OpenAI/Anthropic system message integration

## Benefits
- **Consistent Behavior**: AI maintains character throughout conversation
- **Task Specialization**: Optimized responses for specific use cases
- **User Control**: Full customization of AI personality and expertise
- **Session Persistence**: Persona settings saved and restored
- **Export Capability**: Share conversations with context intact
