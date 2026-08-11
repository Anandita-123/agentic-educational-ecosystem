import streamlit as st
from modules.database import get_supabase_client, fetch_user_profile
from modules.auth import render_auth_page
from modules.ai_engine import render_chat_interface
from modules.mock_test import render_mock_test_interface
from modules.dashboard import render_dashboard_interface 
from modules.profile_setup import render_profile_management_center
from modules.prediction_agent import render_prediction_agent

st.set_page_config(page_title="Agentic AI", page_icon="🎓", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    # CRITICAL PROFILE SYNC FIX: 
    # Force a fresh, live database query on every page refresh/interaction to bypass stale session caches
    user_profile = fetch_user_profile(st.session_state.user.id)
    
    if user_profile:
        st.sidebar.title("🎓 Student's Portal")
        st.sidebar.markdown(f"**Welcome back, {user_profile['name']}!**")
        st.sidebar.info(f"📍 {user_profile['stream']} | Sem {user_profile['semester']}")
        
        # Profile Section Management Expandable Container Block
        with st.sidebar.expander("⚙️ Customize Stream, Sem & Subjects", expanded=False):
            if st.button("Click to Open Academic Control Center", use_container_width=True, type="secondary"):
                st.session_state.active_profile_edit_view = True
                st.rerun()

        st.sidebar.divider()
        
        # Core operational study workspaces list array
        app_mode = st.sidebar.radio(
            "📁 Select Workspace Module", 
            [
                "Academic AI Chatbot", 
                "Mock Test Sandbox", 
                "Question Prediction Agent",
                "Performance Dashboard"
            ]
        )
        st.sidebar.divider()
        
        if st.sidebar.button("🚪 Log Out", use_container_width=True):
            supabase = get_supabase_client()
            supabase.auth.sign_out()
            st.session_state.user = None
            st.session_state.messages = []
            if "current_test" in st.session_state:
                del st.session_state.current_test
            if "active_paper_json" in st.session_state:
                del st.session_state.active_paper_json
            if "active_profile_edit_view" in st.session_state:
                del st.session_state.active_profile_edit_view
            st.rerun()
            
        # --- ROUTING ENGINE ---
        if st.session_state.get("active_profile_edit_view", False):
            render_profile_management_center(user_profile)
            
            st.markdown("---")
            if st.button("⬅️ Back to Active Study Workspaces", use_container_width=True):
                st.session_state.active_profile_edit_view = False
                st.rerun()
        else:
            if app_mode == "Academic AI Chatbot":
                render_chat_interface(user_profile)  # Passes the newly synchronized user profile dict
            elif app_mode == "Mock Test Sandbox":
                render_mock_test_interface(user_profile)
            elif app_mode == "Performance Dashboard":
                render_dashboard_interface()
            elif app_mode == "Question Prediction Agent":
                render_prediction_agent(user_profile)

    else:
        st.error("Failed to load user profile metrics layout.")
else:
    st.title("🎓 Agentic-AI System")
    render_auth_page()