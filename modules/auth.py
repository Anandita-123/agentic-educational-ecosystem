import streamlit as st
import supabase
from modules.database import get_supabase_client



def render_auth_page():
    supabase = get_supabase_client()

    # Using clean tabs instead of sidebar radio buttons for a modern look
    tab1, tab2 = st.tabs(["🔒 Existing Student Login", "📝 New Registration"])

    with tab1:
        st.subheader("Student Login")
        with st.form("login_form"):
            email = st.text_input("Email Address", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            submit_btn = st.form_submit_button("Login")

        if submit_btn:
            try:
                auth_response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })

                user = auth_response.user

                if not user.email_confirmed_at:
                    st.error("Email not verified. Please verify your email first.")
                    supabase.auth.sign_out()
                    st.stop()

                st.session_state.user = user
                st.success("Access Granted!")
                st.rerun()
            except Exception as e:
                st.error("Login failed. Check credentials or verify your email.")

    with tab2:
        st.subheader("Create a Student Account")
        with st.form("signup_form", clear_on_submit=True):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_pass")

            university = st.selectbox("University", ["MAKAUT"])
            semester = st.selectbox("Semester", [str(i) for i in range(1, 9)])
            stream = st.selectbox("Stream", ["CSE", "IT", "AIML"])

            submit_btn = st.form_submit_button("Register Account")

            if submit_btn:
                if not name or not email or not password:
                    st.error("Please fill out all mandatory fields.")
                else:
                    try:
                        auth_response = supabase.auth.sign_up({
                            "email": email,
                            "password": password,
                            "options": {
                                "data": {
                                    "name": name
                                }
                            }
                        })
                        if auth_response.user:
                            user_id = auth_response.user.id
                            profile_data = {
                                "id": user_id,
                                "name": name,
                                "university": university,
                                "semester": semester,
                                "stream": stream,
                            }
                            existing = (
                                supabase.table("profiles")
                                .select("id")
                                .eq("id", user_id)
                                .execute()
                            )

                            if not existing.data:
                                supabase.table("profiles").insert(profile_data).execute()
                            st.success(
                                "Registration successful! "
                                "Please check your email and verify your account before logging in."
                            )
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")