import streamlit as st
import yaml

def render_signup(authenticator, config):
    """Renders the sign-up form and saves new users to the database."""
    try:
        email, new_username, new_name = authenticator.register_user()
        
        if email:
            st.success('User registered successfully! You can now switch to the Login tab.')
            
            # Assign default attributes to the new user
            config['credentials']['usernames'][new_username]['role'] = 'researcher'
            
            # Save the new user info permanently into the YAML file
            with open('auth_config.yaml', 'w') as file:
                yaml.dump(config, file, default_flow_style=False)
                
    except Exception as e:
        st.error(f"Registration Error: {e}")