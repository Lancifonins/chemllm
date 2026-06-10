import streamlit as st
import streamlit_authenticator as stauth

import yaml
from yaml.loader import SafeLoader

from inter_ui.acc_signup import *

def require_login():
    with open('auth_config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Check log-in status before drawing the tabs
    authentication_status = st.session_state.get('authentication_status')

    # Show Login/Sign Up if the user is not logged in
    if not authentication_status:
        tab1, tab2 = st.tabs(["🔒 Login", "📝 Sign Up"])

        with tab1:
            authenticator.login(location='main')

        with tab2:
            render_signup(authenticator, config)

        authentication_status = st.session_state.get('authentication_status')

    username = st.session_state.get('username')
    name = st.session_state.get('name')

    # --- GATEKEEPER ---
    if authentication_status is False:
        st.error('Username/password is incorrect')
        st.stop() 
    elif authentication_status is None:
        st.stop() 

    # --- IF SECURELY LOGGED IN ---
    user_data = config['credentials']['usernames'][username]
    user_role = user_data.get('role', 'researcher')

    if "followed_authors" not in st.session_state:
        st.session_state.followed_authors = user_data.get('followed_authors', [])

    return authenticator, name, username, user_role