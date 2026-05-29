import streamlit as st

def render_chat_history():
    """Iterates through session state and renders the chat UI."""
    for msg in st.session_state.messages:
        # Streamlit uses "user" and "assistant". Google uses "user", "model", and "tool".
        ui_role = "user" if msg.role == "user" else "assistant"
        
        # Hide raw JSON tool responses to keep the UI clean
        if msg.role == "tool":
            continue 

        with st.chat_message(ui_role):
            for part in msg.parts:
                if part.text:
                    st.markdown(part.text)
                elif part.function_call:
                    st.caption(f"🛠️ *Agent autonomously used: `{part.function_call.name}`*")