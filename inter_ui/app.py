import streamlit as st
import os
import sys
from google.genai import types
from functions.get_response import get_response

# Path routing so Streamlit can find your backend files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- PAGE CONFIG ---
st.set_page_config(page_title="ChemLLM Agent", page_icon="🧪", layout="centered")
st.title("🧪 ChemLLM Agent")
st.markdown("Your interactive research assistant. The backend tools are fully online.")

# --- INITIALIZE MEMORY ---
# Store the messages list exactly how get_response expects it: 
# as a list of google.genai.types.Content objects.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- RENDER CHAT HISTORY ---
for msg in st.session_state.messages:
    # Streamlit uses "user" and "assistant". Google uses "user", "model", and "tool".
    ui_role = "user" if msg.role == "user" else "assistant"
    
    # We hide the raw JSON "tool" responses from the screen to keep it clean
    if msg.role == "tool":
        continue 

    with st.chat_message(ui_role):
        for part in msg.parts:
            # If the agent is speaking text, print it
            if part.text:
                st.markdown(part.text)
            # If the agent decided to use a tool, show a cool badge!
            elif part.function_call:
                st.caption(f"🛠️ *Agent autonomously used: `{part.function_call.name}`*")

# --- CHAT INPUT & EXECUTION ---
if prompt := st.chat_input("Ask ChemLLM to research or extract a structure..."):
    
    # 1. Show the user's message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. Add the user's prompt to the memory list in Google's format
    st.session_state.messages.append(
        types.Content(role="user", parts=[types.Part(text=prompt)])
    )
    
    # 3. Call your backend!
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking and executing tools..."):
            try:
                # Because st.session_state.messages is a list, your get_response function 
                # will modify it directly, appending all the tool calls and final answers.
                final_response = get_response(st.session_state.messages, verbose=False)
                
                # Print the final text to the screen
                if final_response and final_response.text:
                    st.markdown(final_response.text)
                    
            except Exception as e:
                st.error(f"Backend Execution Error: {e}")