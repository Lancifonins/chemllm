import streamlit as st

@st.dialog("Search by CAS Number")
def cas_search_dialog():
    st.write("Enter the CAS number of the chemical you want to search:")
    
    # The input box inside the pop-up
    cas_number = st.text_input("CAS Number (e.g. 58-08-2)")
    
    # The submit button inside the pop-up
    if st.button("Check Chemical", type="primary"):
        if cas_number:
            # Save the prompt to session state and trigger a rerun to close the pop-up
            st.session_state.cas_action_prompt = f"Provide information and properties for the chemical with CAS number {cas_number} and if it is in stock in the inventory"
            st.rerun()


def render_sidebar():
    """Renders the sidebar and returns a prompt string if a button is clicked."""
    action_prompt = None
    
    if "cas_action_prompt" in st.session_state and st.session_state.cas_action_prompt:
        action_prompt = st.session_state.cas_action_prompt
        # Clear it immediately so it doesn't loop forever
        st.session_state.cas_action_prompt = None

    with st.sidebar:
        st.header("⚡ Quick Actions")
        st.divider()
        
        if st.button("📚 Latest Papers", use_container_width=True):
            action_prompt = "Find the latest papers from the people in the watchlist and format the links."
            
        if st.button("🔍 Search for Chemical", use_container_width=True):
            cas_search_dialog()

        if st.button("⚠️ Check GHS Hazards", use_container_width=True):
            action_prompt = "What are the GHS safety hazards for the most recent compound we discussed?"
            
        
            
    return action_prompt