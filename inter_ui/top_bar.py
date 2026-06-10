import streamlit as st

def render_top_bar(name, authenticator):
    """Renders the custom top bar with the title and user profile/logout."""
    # Create two columns: a wide one for the title, a narrow one for the user profile
    col_title, col_profile = st.columns([4, 1])
    
    with col_title:
        st.title("🧪 ChemLLM Agent")
        
    with col_profile:
        # Use HTML/Markdown to align the text and make it look clean
        st.markdown(f"<div style='text-align: right; padding-top: 15px;'>👤 <b>{name}</b></div>", unsafe_allow_html=True)
        # The logout button will automatically align under the name
        authenticator.logout('Logout', 'main')