import streamlit as st
import os
import sys
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inter_ui.sidebar import render_sidebar
from inter_ui.chat_ui import render_chat_history

# 1. Path routing

from functions.get_response import get_response

# --- PAGE CONFIG ---
st.set_page_config(page_title="ChemLLM Agent", page_icon="🧪", layout="centered")
st.title("🧪 ChemLLM Agent")

# --- INITIALIZE MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- RENDER UI COMPONENTS ---
# 1. Draw the sidebar (and catch any button clicks)
action_prompt = render_sidebar()

# 2. Draw the existing conversation
render_chat_history()

# --- CHAT INPUT & EXECUTION ---
# The active prompt is EITHER the button you clicked OR what you typed
user_input = st.chat_input("Ask ChemLLM to research or extract a structure...")
prompt = action_prompt or user_input

if prompt:
    # 1. Show the user's message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. Add to memory
    st.session_state.messages.append(
        types.Content(role="user", parts=[types.Part(text=prompt)])
    )
    
    # 3. Call backend
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking and executing tools..."):
            try:
                final_response = get_response(st.session_state.messages, verbose=False)
                
                if final_response and final_response.text:
                    st.markdown(final_response.text)
                    
            except Exception as e:
                st.error(f"Backend Execution Error: {e}")