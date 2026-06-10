import streamlit as st
import os
import sys
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inter_ui.auth import *
from inter_ui.sidebar import *
from inter_ui.chat_ui import *
from inter_ui.top_bar import *

from functions.get_response import get_response

#Login check before proceeding to the page.
authenticator, name, username, user_role = require_login()
if user_role == "super_admin":
    st.caption("⚡ System Level: All Administrator Access Enabled")
elif user_role == "admin":
    st.caption("⚡ System Level: Administrator Access Enabled")
else:
    st.caption("🔬 System Level: Read-Only Researcher Access")

# --- PAGE CONFIG ---
st.set_page_config(page_title="ChemLLM Agent", page_icon="🧪", layout="centered")

render_top_bar(name, authenticator)

# --- INITIALIZE MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- RENDER UI COMPONENTS ---
# Draw the sidebar (and catch any button clicks)
action_prompt = render_sidebar()

# Draw the existing conversation
render_chat_history()

# --- CHAT INPUT & EXECUTION ---
# The active prompt is either the button you clicked or what you typed
user_input = st.chat_input("Ask ChemLLM to research or extract a structure...")
prompt = action_prompt or user_input

# Show the user's message immediately and add it to memory
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
        
    st.session_state.messages.append(
        types.Content(role="user", parts=[types.Part(text=prompt)])
    )
    
    # Call the agent at backend
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking and executing tools..."):
            try:
                final_response = get_response(st.session_state.messages, verbose=False)
                
                if final_response and final_response.text:
                    st.markdown(final_response.text)
                    
            except Exception as e:
                st.error(f"Backend Execution Error: {e}")