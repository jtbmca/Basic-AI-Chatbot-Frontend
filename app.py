import streamlit as st
import requests
import os
import json
import uuid
from datetime import datetime
# HuggingFace imports for BERT
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM
import torch

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue without it
    pass

# Ollama API endpoint and file paths
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
HISTORY_FILE = os.getenv('HISTORY_FILE', 'chat_history.json')
CONVERSATIONS_DIR = os.getenv('CONVERSATIONS_DIR', 'conversations')
CUSTOM_PERSONAS_FILE = os.getenv('CUSTOM_PERSONAS_FILE', 'custom_personas.json')

# Configuration validation
def validate_configuration():
    """Validate configuration and provide user feedback"""
    issues = []
    
    # Check BERT model path
    if not os.path.exists(BERT_MODEL_PATH):
        issues.append({
            "type": "warning",
            "message": f"BERT model not found at: {BERT_MODEL_PATH}",
            "suggestion": "Set BERT_MODEL_PATH environment variable or disable BERT model in the interface."
        })
    
    # Check if conversations directory is writable  
    try:
        # We'll check this later when ensure_conversations_dir is defined
        pass
    except Exception as e:
        issues.append({
            "type": "error", 
            "message": f"Cannot write to conversations directory: {CONVERSATIONS_DIR}",
            "suggestion": f"Check permissions or set CONVERSATIONS_DIR environment variable. Error: {e}"
        })
    
    return issues

# Dynamically fetch Ollama models
def get_ollama_models():
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return [
            {"name": m["name"], "id": m["model"], "type": "ollama"}
            for m in data.get("models", [])
        ]
    except Exception:
        return []

# Add OpenAI and Anthropic support (API key required for real use)
STATIC_MODELS = [
    {"name": "Intel BERT MRPC (Local)", "id": "bert-mrpc", "type": "bert"},
    {"name": "HuggingFace Hub (gpt2)", "id": "gpt2", "type": "hf_hub"},
    {"name": "OpenAI GPT-4.1 (API)", "id": "openai-gpt-4.1", "type": "openai"},
    {"name": "Anthropic Claude (API)", "id": "anthropic-claude", "type": "anthropic"}
]

AVAILABLE_MODELS = get_ollama_models() + STATIC_MODELS

# Predefined personas/system prompts
PREDEFINED_PERSONAS = {
    "Default": "",
    "Helpful Assistant": "You are a helpful, harmless, and honest AI assistant. Always be polite and provide accurate information.",
    "Code Expert": "You are an expert programmer and software engineer. Provide clear, well-commented code examples and technical explanations.",
    "Creative Writer": "You are a creative writing assistant. Help with storytelling, character development, and creative expression.",
    "Teacher": "You are a patient and encouraging teacher. Explain concepts clearly with examples and check for understanding.",
    "Scientist": "You are a knowledgeable scientist. Provide evidence-based explanations and encourage scientific thinking.",
    "Philosopher": "You are a thoughtful philosopher. Explore deep questions about existence, ethics, and meaning.",
    "Comedian": "You are a witty comedian. Be humorous while still being helpful and appropriate.",
    "Professional": "You are a professional business assistant. Be formal, efficient, and focused on practical solutions."
}

# Configuration - Use environment variables with fallbacks
BERT_MODEL_PATH = os.getenv(
    'BERT_MODEL_PATH', 
    os.path.join(os.path.expanduser('~'), 'Documents', 'GitHub', 'Python', 'HFBERt', 'Intel', 'huggingface_Intel_bert-base-uncased-mrpc_v1')
)
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
CONVERSATIONS_DIR = os.getenv('CONVERSATIONS_DIR', 'conversations')
CUSTOM_PERSONAS_FILE = os.getenv('CUSTOM_PERSONAS_FILE', 'custom_personas.json')
HISTORY_FILE = os.getenv('HISTORY_FILE', 'chat_history.json')

# Load BERT model and tokenizer only once
@st.cache_resource
def load_bert():
    """Load BERT model with proper error handling"""
    try:
        if not os.path.exists(BERT_MODEL_PATH):
            raise FileNotFoundError(f"BERT model not found at: {BERT_MODEL_PATH}")
        
        tokenizer = AutoTokenizer.from_pretrained(BERT_MODEL_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(BERT_MODEL_PATH)
        return tokenizer, model
    except Exception as e:
        st.error(f"Failed to load BERT model: {e}")
        st.info(f"Expected model path: {BERT_MODEL_PATH}")
        st.info("Set BERT_MODEL_PATH environment variable to specify model location")
        raise

@st.cache_resource
def load_hf_model(model_id):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    return tokenizer, model

def bert_infer(user_input):
    """BERT inference with error handling"""
    try:
        tokenizer, model = load_bert()
        # For MRPC, we need two sentences. We'll use the user input as both for demo.
        inputs = tokenizer(user_input, user_input, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            pred = torch.argmax(logits, dim=1).item()
        # MRPC is a paraphrase task: 1=paraphrase, 0=not paraphrase
        return f"BERT MRPC prediction: {'Paraphrase' if pred==1 else 'Not paraphrase'}"
    except Exception as e:
        return f"BERT model error: {str(e)}. Please check model path configuration."

def hf_infer(user_input, model_id, system_prompt=""):
    tokenizer, model = load_hf_model(model_id)
    
    # Prepare input with system prompt if provided
    if system_prompt:
        full_input = f"System: {system_prompt}\nUser: {user_input}\nAssistant:"
    else:
        full_input = user_input
    
    inputs = tokenizer(full_input, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=100, pad_token_id=tokenizer.eos_token_id)
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract just the generated part
    if system_prompt and reply.startswith(full_input):
        return reply[len(full_input):].strip()
    elif reply.startswith(user_input):
        return reply[len(user_input):].strip()
    else:
        return reply

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both old format (just messages) and new format (with system_prompt)
            if isinstance(data, list):
                return {"messages": data, "system_prompt": ""}
            return data
    return {"messages": [], "system_prompt": ""}

def save_history(history_data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

# === CONVERSATION MANAGEMENT FUNCTIONS ===

def ensure_conversations_dir():
    """Ensure the conversations directory exists"""
    if not os.path.exists(CONVERSATIONS_DIR):
        os.makedirs(CONVERSATIONS_DIR)

def get_conversation_file(conversation_id):
    """Get the file path for a conversation"""
    ensure_conversations_dir()
    return os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")

def load_conversation(conversation_id):
    """Load a specific conversation by ID"""
    file_path = get_conversation_file(conversation_id)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "id": conversation_id,
        "name": "New Conversation",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "messages": [],
        "system_prompt": ""
    }

def is_conversation_empty(conversation_data):
    """Check if a conversation is empty (no messages and no system prompt)"""
    return (
        len(conversation_data.get("messages", [])) == 0 and 
        not conversation_data.get("system_prompt", "").strip()
    )

def clear_conversation_if_empty(conversation_data):
    """Clear conversation and delete file if it becomes empty"""
    if is_conversation_empty(conversation_data):
        file_path = get_conversation_file(conversation_data["id"])
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    else:
        save_conversation(conversation_data, force_save=True)
        return False

def save_conversation(conversation_data, force_save=False):
    """Save a conversation to file only if it has content or force_save is True"""
    # Don't save empty conversations unless explicitly forced
    if not force_save and is_conversation_empty(conversation_data):
        return False
    
    conversation_data["updated_at"] = datetime.now().isoformat()
    file_path = get_conversation_file(conversation_data["id"])
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, ensure_ascii=False, indent=2)
    return True

def list_conversations():
    """Get list of all conversations with metadata"""
    ensure_conversations_dir()
    conversations = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith('.json'):
            conversation_id = filename[:-5]  # Remove .json extension
            try:
                conv_data = load_conversation(conversation_id)
                conversations.append({
                    "id": conversation_id,
                    "name": conv_data.get("name", "Unnamed Conversation"),
                    "updated_at": conv_data.get("updated_at", ""),
                    "message_count": len(conv_data.get("messages", [])),
                    "system_prompt": conv_data.get("system_prompt", "")[:50] + ("..." if len(conv_data.get("system_prompt", "")) > 50 else "")
                })
            except Exception:
                continue
    # Sort by updated_at descending
    conversations.sort(key=lambda x: x["updated_at"], reverse=True)
    return conversations

def delete_conversation(conversation_id):
    """Delete a conversation"""
    file_path = get_conversation_file(conversation_id)
    if os.path.exists(file_path):
        os.remove(file_path)

def create_new_conversation():
    """Create a new conversation with unique ID (not saved until it has content)"""
    conversation_id = str(uuid.uuid4())
    conversation_data = {
        "id": conversation_id,
        "name": "New Conversation",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "messages": [],
        "system_prompt": ""
    }
    # Don't save empty conversation immediately - will be saved when content is added
    return conversation_id

def migrate_old_history():
    """Migrate old single conversation to new system"""
    if os.path.exists(HISTORY_FILE):
        old_data = load_history()
        if old_data["messages"] or old_data["system_prompt"]:
            # Create a conversation from old data
            conversation_id = str(uuid.uuid4())
            conversation_data = {
                "id": conversation_id,
                "name": "Migrated Conversation",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": old_data["messages"],
                "system_prompt": old_data["system_prompt"]
            }
            save_conversation(conversation_data, force_save=True)
            # Clear old file
            save_history({"messages": [], "system_prompt": ""})
            return conversation_id
    return None

# === CUSTOM PERSONA MANAGEMENT FUNCTIONS ===

def load_custom_personas():
    """Load custom personas from file"""
    if os.path.exists(CUSTOM_PERSONAS_FILE):
        try:
            with open(CUSTOM_PERSONAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_custom_personas(custom_personas):
    """Save custom personas to file"""
    with open(CUSTOM_PERSONAS_FILE, "w", encoding="utf-8") as f:
        json.dump(custom_personas, f, ensure_ascii=False, indent=2)

def add_custom_persona(name, prompt):
    """Add a new custom persona"""
    custom_personas = load_custom_personas()
    custom_personas[name] = prompt
    save_custom_personas(custom_personas)

def delete_custom_persona(name):
    """Delete a custom persona"""
    custom_personas = load_custom_personas()
    if name in custom_personas:
        del custom_personas[name]
        save_custom_personas(custom_personas)

def get_all_personas():
    """Get combined predefined and custom personas"""
    custom_personas = load_custom_personas()
    all_personas = PREDEFINED_PERSONAS.copy()
    all_personas.update(custom_personas)
    return all_personas, custom_personas

st.set_page_config(page_title="Ollama Chat", page_icon="💬")
st.title("Tibs Chat Interface")

# Show configuration status
config_issues = validate_configuration()
if config_issues:
    with st.expander("⚠️ Configuration Issues", expanded=any(issue["type"] == "error" for issue in config_issues)):
        for issue in config_issues:
            if issue["type"] == "error":
                st.error(f"❌ {issue['message']}")
                st.info(f"💡 {issue['suggestion']}")
            else:
                st.warning(f"⚠️ {issue['message']}")
                st.info(f"💡 {issue['suggestion']}")

# === CONVERSATION MANAGEMENT UI ===

# Initialize conversation management in session state
if "current_conversation_id" not in st.session_state:
    # Try to migrate old history first
    migrated_id = migrate_old_history()
    if migrated_id:
        st.session_state["current_conversation_id"] = migrated_id
    else:
        # Create a new conversation
        st.session_state["current_conversation_id"] = create_new_conversation()

# Conversation management sidebar
st.sidebar.header("💬 Conversations")

# Get list of conversations
conversations = list_conversations()

# Create new conversation button
if st.sidebar.button("➕ New Conversation"):
    new_id = create_new_conversation()
    st.session_state["current_conversation_id"] = new_id
    st.rerun()

# Conversation selector
if conversations:
    # Search functionality
    search_term = st.sidebar.text_input("🔍 Search conversations", placeholder="Search by name or content...")
    
    if search_term:
        # Filter conversations based on search term
        filtered_conversations = []
        for conv in conversations:
            if (search_term.lower() in conv["name"].lower() or 
                search_term.lower() in conv["system_prompt"].lower()):
                filtered_conversations.append(conv)
        conversations = filtered_conversations
    
    conversation_options = []
    conversation_ids = []
    for conv in conversations:
        name = conv["name"]
        if len(name) > 25:
            name = name[:22] + "..."
        msg_count = conv["message_count"]
        display_name = f"{name} ({msg_count} msgs)"
        conversation_options.append(display_name)
        conversation_ids.append(conv["id"])
    
    if conversation_ids:  # Only show selector if there are conversations after filtering
        # Find current selection index
        try:
            current_index = conversation_ids.index(st.session_state["current_conversation_id"])
        except ValueError:
            current_index = 0
            if conversation_ids:
                st.session_state["current_conversation_id"] = conversation_ids[0]
        
        selected_conv_index = st.sidebar.selectbox(
            "Select Conversation", 
            range(len(conversation_options)),
            format_func=lambda x: conversation_options[x],
            index=current_index,
            key="conversation_selector"
        )
        
        if conversation_ids[selected_conv_index] != st.session_state["current_conversation_id"]:
            st.session_state["current_conversation_id"] = conversation_ids[selected_conv_index]
            st.rerun()
    else:
        st.sidebar.info("No conversations match your search.")

# Import conversation functionality
st.sidebar.subheader("📤 Import Conversation")
uploaded_file = st.sidebar.file_uploader("Upload conversation JSON", type=['json'])
if uploaded_file is not None:
    try:
        import_data = json.load(uploaded_file)
        
        # Handle different import formats
        if "conversation" in import_data:
            # New format with conversation wrapper
            conv_data = import_data["conversation"]
        elif "messages" in import_data:
            # Direct conversation format or old history format
            conv_data = import_data
        else:
            st.sidebar.error("Invalid conversation format")
            conv_data = None
        
        if conv_data and st.sidebar.button("Import Conversation"):
            # Create new conversation with imported data
            new_id = str(uuid.uuid4())
            imported_conversation = {
                "id": new_id,
                "name": conv_data.get("name", "Imported Conversation"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": conv_data.get("messages", []),
                "system_prompt": conv_data.get("system_prompt", "")
            }
            save_conversation(imported_conversation, force_save=True)
            st.session_state["current_conversation_id"] = new_id
            st.sidebar.success("Conversation imported successfully!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error importing conversation: {e}")

# Load current conversation
current_conversation = load_conversation(st.session_state["current_conversation_id"])

# Conversation settings
with st.sidebar.expander("⚙️ Conversation Settings"):    # Rename conversation
    new_name = st.text_input("Conversation Name", value=current_conversation["name"], key="conv_name")
    if st.button("Rename") and new_name != current_conversation["name"]:
        current_conversation["name"] = new_name
        save_conversation(current_conversation, force_save=True)
        st.rerun()
    
    # Delete conversation
    if len(conversations) > 1:  # Don't allow deleting the last conversation
        if st.button("🗑️ Delete This Conversation", type="secondary"):
            delete_conversation(st.session_state["current_conversation_id"])
            # Switch to first available conversation
            remaining_conversations = list_conversations()
            if remaining_conversations:
                st.session_state["current_conversation_id"] = remaining_conversations[0]["id"]
            else:
                st.session_state["current_conversation_id"] = create_new_conversation()
            st.rerun()
    
    # Export conversation
    if st.button("📥 Export This Conversation"):
        export_data = {
            "conversation": current_conversation,
            "export_timestamp": datetime.now().isoformat()
        }
        st.download_button(
            label="Download conversation as JSON",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"conversation_{current_conversation['name']}.json",
            mime="application/json",
            key="export_conv"
        )

# Display conversation info
st.caption(f"💬 **{current_conversation['name']}** • {len(current_conversation['messages'])} messages • Updated: {current_conversation.get('updated_at', 'Unknown')[:10]}")

# Initialize session state from current conversation
if "messages" not in st.session_state or st.session_state.get("loaded_conversation_id") != st.session_state["current_conversation_id"]:
    st.session_state["messages"] = current_conversation["messages"]
    st.session_state["system_prompt"] = current_conversation["system_prompt"]
    st.session_state["loaded_conversation_id"] = st.session_state["current_conversation_id"]

# Model selection UI
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = AVAILABLE_MODELS[0]["id"]

model_names = [m["name"] for m in AVAILABLE_MODELS]
model_ids = [m["id"] for m in AVAILABLE_MODELS]
selected_name = st.selectbox("Select Model", model_names, index=model_ids.index(st.session_state["selected_model"]))
st.session_state["selected_model"] = AVAILABLE_MODELS[model_names.index(selected_name)]["id"]
selected_type = AVAILABLE_MODELS[model_names.index(selected_name)]["type"]

# UI for custom Hugging Face model ID
st.sidebar.header("Advanced Model Options")
hf_custom_id = st.sidebar.text_input("Hugging Face Model ID (e.g. gpt2, meta-llama/Llama-2-7b-chat-hf)")
if hf_custom_id:
    custom_hf_model = {"name": f"HuggingFace Hub ({hf_custom_id})", "id": hf_custom_id, "type": "hf_hub"}
    if custom_hf_model not in AVAILABLE_MODELS:
        AVAILABLE_MODELS.append(custom_hf_model)

# System Prompt/Persona Configuration
st.sidebar.header("🎭 Assistant Persona")

# Initialize system prompt in session state
if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = ""
if "custom_prompt_draft" not in st.session_state:
    st.session_state["custom_prompt_draft"] = ""
if "custom_prompt_applied" not in st.session_state:
    st.session_state["custom_prompt_applied"] = False

# Get all personas (predefined + custom)
all_personas, custom_personas = get_all_personas()

# Persona selection
persona_names = list(all_personas.keys())

# Check if we just saved a new persona and should select it
if "newly_saved_persona" in st.session_state:
    if st.session_state["newly_saved_persona"] in persona_names:
        default_index = persona_names.index(st.session_state["newly_saved_persona"])
        del st.session_state["newly_saved_persona"]  # Clear the flag
    else:
        default_index = 0
else:
    default_index = 0

selected_persona = st.sidebar.selectbox("Choose Persona", persona_names, index=default_index)

# Clear draft if a different persona is selected
if "previous_selected_persona" not in st.session_state:
    st.session_state["previous_selected_persona"] = selected_persona
elif st.session_state["previous_selected_persona"] != selected_persona:
    st.session_state["custom_prompt_draft"] = ""
    st.session_state["previous_selected_persona"] = selected_persona

# Show if this is a custom persona
if selected_persona in custom_personas:
    st.sidebar.caption("🔧 Custom Persona")

# Custom system prompt
custom_prompt = st.sidebar.text_area(
    "Custom System Prompt", 
    value=st.session_state.get("custom_prompt_draft", st.session_state["system_prompt"]),
    height=100,
    help="Define how the assistant should behave. This will override the selected persona. Press Ctrl+Enter to apply changes quickly.",
    key="custom_prompt_input"
)

# Store draft in session state but don't apply it yet
st.session_state["custom_prompt_draft"] = custom_prompt

# Add Apply button for system prompt
if st.sidebar.button("Apply System Prompt", help="Apply the custom system prompt (Shortcut: Ctrl+Enter in the text area)"):
    st.session_state["system_prompt"] = custom_prompt
    st.session_state["custom_prompt_applied"] = True

# Save current prompt as new persona
st.sidebar.subheader("💾 Save Persona")

# Add helpful hint about keyboard shortcuts
st.sidebar.caption("💡 Tip: Use Ctrl+Enter in the text area to quickly apply changes")

# Use a different approach for clearing the input - use a counter to force widget recreation
if "persona_input_key" not in st.session_state:
    st.session_state["persona_input_key"] = 0

# Use dynamic key to allow clearing
input_key = f"persona_name_input_{st.session_state['persona_input_key']}"

new_persona_name = st.sidebar.text_input(
    "Persona Name", 
    placeholder="Enter name for new persona...",
    help="Enter a name and press Enter to focus, then use the Save Current button",
    key=input_key
)

# Check if user pressed Enter in the persona name field (simulating quick save intent)
if new_persona_name.strip() and new_persona_name != st.session_state.get("last_persona_name", ""):
    st.sidebar.info("💡 Name entered! Click 'Save Current' or press the button below to save.")
    st.session_state["last_persona_name"] = new_persona_name

col1, col2 = st.sidebar.columns(2)
with col1:
    # Enhanced save button with better feedback
    save_button_text = "Save Current"
    if new_persona_name.strip() and st.session_state["system_prompt"].strip():
        save_button_text = f"Save '{new_persona_name[:15]}{'...' if len(new_persona_name) > 15 else ''}'"
    
    if st.button(save_button_text, help="Save current system prompt as new persona (Shortcut: Fill name and click here)", type="primary"):
        if new_persona_name.strip() and st.session_state["system_prompt"].strip():
            if new_persona_name in PREDEFINED_PERSONAS:
                st.sidebar.error("Cannot overwrite predefined personas!")
            else:
                add_custom_persona(new_persona_name.strip(), st.session_state["system_prompt"])
                st.sidebar.success(f"Saved '{new_persona_name}'!")
                # Set the newly saved persona to be selected after rerun
                st.session_state["newly_saved_persona"] = new_persona_name.strip()
                # Clear the name field after successful save by incrementing the key
                st.session_state["persona_input_key"] += 1
                st.session_state["last_persona_name"] = ""
                st.rerun()
        elif not new_persona_name.strip():
            st.sidebar.error("Please enter a persona name!")
        else:
            st.sidebar.error("No system prompt to save!")

# Quick save button for faster workflow
if new_persona_name.strip() and st.session_state["system_prompt"].strip() and new_persona_name not in PREDEFINED_PERSONAS:
    if st.sidebar.button("⚡ Quick Save", help="Quick save with the entered name", type="secondary"):
        add_custom_persona(new_persona_name.strip(), st.session_state["system_prompt"])
        st.sidebar.success(f"✅ Saved '{new_persona_name}'!")
        # Set the newly saved persona to be selected after rerun
        st.session_state["newly_saved_persona"] = new_persona_name.strip()
        # Clear the name field after successful save by incrementing the key
        st.session_state["persona_input_key"] += 1
        st.session_state["last_persona_name"] = ""
        st.rerun()

with col2:
    if st.button("Delete Persona", help="Delete the selected custom persona"):
        if selected_persona in custom_personas:
            delete_custom_persona(selected_persona)
            st.sidebar.success(f"Deleted '{selected_persona}'!")
            st.rerun()
        else:
            st.sidebar.error("Cannot delete predefined personas!")

# Quick save buttons for common scenarios
if st.session_state["system_prompt"].strip() and new_persona_name.strip():
    st.sidebar.info(f"💡 Ready to save '{new_persona_name}' with current prompt")

# Persona templates for quick creation
with st.sidebar.expander("🚀 Quick Persona Templates"):
    st.write("**Create from templates:**")
    
    templates = {
        "Domain Expert": "You are an expert in [DOMAIN]. Provide detailed, accurate information and practical advice in this field.",
        "Debug Helper": "You are a debugging assistant. Help identify issues, suggest solutions, and explain problems step by step.",
        "Documentation Writer": "You are a technical documentation writer. Create clear, comprehensive documentation with examples.",
        "Project Manager": "You are a project management assistant. Help with planning, organization, and workflow optimization.",
        "Research Assistant": "You are a research assistant. Help gather information, analyze data, and summarize findings."
    }
    
    for template_name, template_prompt in templates.items():
        if st.button(f"Use {template_name}", key=f"template_{template_name}"):
            st.session_state["system_prompt"] = template_prompt
            current_conversation["system_prompt"] = template_prompt
            save_conversation(current_conversation)
            st.rerun()

# Custom Persona Management
if custom_personas:
    with st.sidebar.expander("🔧 Manage Custom Personas"):
        st.write("**Your Custom Personas:**")
        for name, prompt in custom_personas.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"**{name}**")
                preview = prompt[:60] + "..." if len(prompt) > 60 else prompt
                st.caption(preview)
            with col2:
                if st.button("🗑️", key=f"del_{name}", help=f"Delete {name}"):
                    delete_custom_persona(name)
                    st.rerun()
        
        # Export/Import Custom Personas
        if st.button("📥 Export All Custom Personas"):
            export_data = {
                "custom_personas": custom_personas,
                "export_timestamp": datetime.now().isoformat()
            }
            st.download_button(
                label="Download custom personas as JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name="custom_personas.json",
                mime="application/json",
                key="export_personas"
            )
        
        # Import personas
        uploaded_personas = st.file_uploader("Import Personas JSON", type=['json'], key="import_personas")
        if uploaded_personas is not None:
            try:
                import_data = json.load(uploaded_personas)
                if "custom_personas" in import_data:
                    imported_personas = import_data["custom_personas"]
                    if st.button("Import Personas"):
                        current_custom = load_custom_personas()
                        current_custom.update(imported_personas)
                        save_custom_personas(current_custom)
                        st.success(f"Imported {len(imported_personas)} personas!")
                        st.rerun()
                else:
                    st.error("Invalid personas file format")
            except Exception as e:
                st.error(f"Error importing personas: {e}")

# Update system prompt based on selection
old_system_prompt = st.session_state["system_prompt"]

# Only update system prompt if it was explicitly applied or if no custom prompt is being drafted
if st.session_state.get("custom_prompt_applied", False):
    # Custom prompt was applied
    st.session_state["custom_prompt_applied"] = False  # Reset flag
elif not st.session_state.get("custom_prompt_draft", "").strip():
    # No custom prompt drafted, use selected persona
    st.session_state["system_prompt"] = all_personas[selected_persona]

# Save system prompt changes to current conversation
if st.session_state["system_prompt"] != old_system_prompt:
    current_conversation["system_prompt"] = st.session_state["system_prompt"]
    save_conversation(current_conversation)

# Show current active prompt
if st.session_state["system_prompt"]:
    with st.sidebar.expander("Current System Prompt"):
        st.write(st.session_state["system_prompt"])

# Reset persona button
if st.sidebar.button("Reset Persona"):
    st.session_state["system_prompt"] = ""
    st.session_state["custom_prompt_draft"] = ""
    current_conversation["system_prompt"] = ""
    save_conversation(current_conversation, force_save=True)
    st.rerun()

# Display system prompt indicator in main area
if st.session_state["system_prompt"]:
    # Show persona name if it matches a known persona
    persona_name = None
    all_personas, custom_personas = get_all_personas()
    for name, prompt in all_personas.items():
        if prompt == st.session_state["system_prompt"]:
            persona_name = name
            break
    
    if persona_name:
        if persona_name in custom_personas:
            st.success(f"🎭 **Active Persona:** {persona_name} (Custom)")
        else:
            st.info(f"🎭 **Active Persona:** {persona_name}")
        
        # Show preview of the prompt
        with st.expander("View System Prompt"):
            st.write(st.session_state["system_prompt"])
    else:
        # Custom prompt that doesn't match any saved persona
        prompt_preview = st.session_state["system_prompt"][:150] + "..." if len(st.session_state["system_prompt"]) > 150 else st.session_state["system_prompt"]
        st.warning(f"🎭 **Custom System Prompt Active:** {prompt_preview}")
        
        # Show full prompt in expander
        with st.expander("View Full System Prompt"):
            st.write(st.session_state["system_prompt"])
else:
    st.info("🎭 **No System Prompt Active** - Using default behavior")

# Display conversation history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**{selected_name}:** {msg['content']}")

# User input - using chat_input for better Enter key handling
user_input = st.chat_input("Type your message here...")

if user_input:
    # Add user message to history
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    if selected_type == "ollama":
        # Prepare prompt as conversation history with system prompt
        prompt = ""
        if st.session_state["system_prompt"]:
            prompt += f"System: {st.session_state['system_prompt']}\n\n"
        
        for msg in st.session_state["messages"]:
            if msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            else:
                prompt += f"Assistant: {msg['content']}\n"
        
        payload = {
            "model": st.session_state["selected_model"],
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            ollama_reply = data.get("response", "[No response]")
        except Exception as e:
            ollama_reply = f"[Error: {e}]"
        st.session_state["messages"].append({"role": "assistant", "content": ollama_reply})
    elif selected_type == "bert":
        bert_reply = bert_infer(user_input)
        st.session_state["messages"].append({"role": "assistant", "content": bert_reply})
    elif selected_type == "hf_hub":
        hf_reply = hf_infer(user_input, st.session_state["selected_model"], st.session_state["system_prompt"])
        st.session_state["messages"].append({"role": "assistant", "content": hf_reply})
    elif selected_type == "openai":
        st.session_state["messages"].append({"role": "assistant", "content": "[OpenAI integration not configured. Add your API key and code to enable.]"})
    elif selected_type == "anthropic":
        st.session_state["messages"].append({"role": "assistant", "content": "[Anthropic integration not configured. Add your API key and code to enable.]"})
    
    # Save to current conversation
    current_conversation["messages"] = st.session_state["messages"]
    current_conversation["system_prompt"] = st.session_state["system_prompt"]
    save_conversation(current_conversation)
    st.rerun()

if st.button("Clear Conversation"):
    st.session_state["messages"] = []
    current_conversation["messages"] = []
    conversation_deleted = clear_conversation_if_empty(current_conversation)
    
    # If conversation was deleted because it's empty, create a new one
    if conversation_deleted:
        st.session_state["current_conversation_id"] = create_new_conversation()
    
    st.rerun()

# === KEYBOARD SHORTCUTS SUPPORT ===

# Add JavaScript for keyboard shortcuts
keyboard_js = """
<script>
document.addEventListener('keydown', function(e) {
    // Ctrl+Enter in custom system prompt text area
    if (e.ctrlKey && e.key === 'Enter') {
        // Find if we're in the custom prompt text area
        if (e.target.tagName === 'TEXTAREA' && e.target.getAttribute('aria-label') && 
            e.target.getAttribute('aria-label').includes('Custom System Prompt')) {
            
            // Look for the Apply System Prompt button and click it
            const applyBtn = document.querySelector('button[title*="Apply the custom system prompt"]');
            if (applyBtn) {
                e.preventDefault();
                applyBtn.click();
                return;
            }
            
            // Fallback to other save buttons
            const quickSaveBtn = document.querySelector('button[title*="Quick save"]');
            const saveCurrentBtn = document.querySelector('button[title*="Save current system prompt"]');
            
            if (quickSaveBtn) {
                e.preventDefault();
                quickSaveBtn.click();
            } else if (saveCurrentBtn) {
                e.preventDefault();
                // Focus on persona name input if empty
                const nameInput = document.querySelector('input[aria-label*="Persona Name"]');
                if (nameInput && !nameInput.value.trim()) {
                    nameInput.focus();
                    nameInput.placeholder = 'Enter name and try Ctrl+Enter again...';
                }
            }
        }
    }
    
    // Enter in persona name input to trigger save
    if (e.key === 'Enter' && e.target.getAttribute('aria-label') && 
        e.target.getAttribute('aria-label').includes('Persona Name')) {
        const quickSaveBtn = document.querySelector('button[title*="Quick save"]');
        const saveCurrentBtn = document.querySelector('button[title*="Save current system prompt"]');
        
        if (quickSaveBtn) {
            e.preventDefault();
            quickSaveBtn.click();
        } else if (saveCurrentBtn) {
            e.preventDefault();
            saveCurrentBtn.click();
        }
    }
});
</script>
"""

st.components.v1.html(keyboard_js, height=0)