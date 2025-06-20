import streamlit as st
import requests
import os
import json
# HuggingFace imports for BERT
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Ollama API endpoint (correct endpoint)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
HISTORY_FILE = "chat_history.json"

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

# Path to your local BERT model
BERT_MODEL_PATH = "C:/Users/Tibs/Documents/GitHub/Python/HFBERt/Intel/huggingface_Intel_bert-base-uncased-mrpc_v1"

# Load BERT model and tokenizer only once
@st.cache_resource
def load_bert():
    tokenizer = BertTokenizer.from_pretrained(BERT_MODEL_PATH)
    model = BertForSequenceClassification.from_pretrained(BERT_MODEL_PATH)
    return tokenizer, model

@st.cache_resource
def load_hf_model(model_id):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    return tokenizer, model

def bert_infer(user_input):
    tokenizer, model = load_bert()
    # For MRPC, we need two sentences. We'll use the user input as both for demo.
    inputs = tokenizer(user_input, user_input, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        pred = torch.argmax(logits, dim=1).item()
    # MRPC is a paraphrase task: 1=paraphrase, 0=not paraphrase
    return f"BERT MRPC prediction: {'Paraphrase' if pred==1 else 'Not paraphrase'}"

def hf_infer(user_input, model_id):
    tokenizer, model = load_hf_model(model_id)
    inputs = tokenizer(user_input, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=100)
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return reply[len(user_input):].strip() if reply.startswith(user_input) else reply

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

st.set_page_config(page_title="Ollama Chat", page_icon="💬")
st.title("Tibs Chat Interface")

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

# Load persistent history on first run
if "messages" not in st.session_state:
    st.session_state["messages"] = load_history()

# Display conversation history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**{selected_name}:** {msg['content']}")

# User input
user_input = st.text_input("Type your message:", key="input")

if st.button("Send") and user_input:
    # Add user message to history
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    if selected_type == "ollama":
        # Prepare prompt as conversation history
        prompt = ""
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
        hf_reply = hf_infer(user_input, st.session_state["selected_model"])
        st.session_state["messages"].append({"role": "assistant", "content": hf_reply})
    elif selected_type == "openai":
        st.session_state["messages"].append({"role": "assistant", "content": "[OpenAI integration not configured. Add your API key and code to enable.]"})
    elif selected_type == "anthropic":
        st.session_state["messages"].append({"role": "assistant", "content": "[Anthropic integration not configured. Add your API key and code to enable.]"})
    save_history(st.session_state["messages"])
    st.rerun()

if st.button("Clear Conversation"):
    st.session_state["messages"] = []
    save_history([])
    st.rerun()

if st.button("Export History"):
    st.download_button(
        label="Download chat history as JSON",
        data=json.dumps(st.session_state["messages"], ensure_ascii=False, indent=2),
        file_name="chat_history.json",
        mime="application/json"
    )