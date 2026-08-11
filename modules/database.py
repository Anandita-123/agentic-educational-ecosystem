import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_supabase_client() -> Client:
    """Initializes and caches the Supabase client connection."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def fetch_user_profile(user_id: str):
    """Fetches user profile metrics safely from the custom profiles table."""
    try:
        supabase = get_supabase_client()
        query = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return query.data
    except Exception as e:
        st.error(f"Error fetching profile context: {str(e)}")
        return None