import os
import json
import streamlit as st
from google import genai
from google.genai import types

LOCAL_DATA_FILE = "dashboard_data.json"

def load_local_metrics() -> dict:
    if not os.path.exists(LOCAL_DATA_FILE):
        default_structure = {
            "strengths": ["System Initialized - Take a test to populate metrics"],
            "weaknesses": ["No historical data evaluated yet"],
            "ratings": {
                "Conceptual Clarity": 3.0,
                "Time Management": 3.0,
                "Syllabus Alignment": 3.0,
                "Exam Readiness": 3.0
            },
            "test_history": []
        }
        with open(LOCAL_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_structure, f, indent=4)
        return default_structure
        
    with open(LOCAL_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_local_metrics(data: dict):
    with open(LOCAL_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def log_test_for_analytics(profile: dict, subject: str, test_type: str, performance_summary: str):
    """Pipes test summaries to the modern Google GenAI Client for telemetry parsing."""
    try:
        client = genai.Client()
        
        analytics_prompt = f"""
        You are an academic analytical engine for MAKAUT University.
        Review this student's latest test attempt performance summary:
        ---
        Subject: {subject}
        Format: {test_type}
        Performance Notes: {performance_summary}
        ---
        
        Based on this, update their profile analytics. You must return your response STRICTLY as a raw JSON object matching this schema exactly without any markdown wrappers or ```json blocks:
        {{
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "ratings": {{
                "Conceptual Clarity": 4.5,
                "Time Management": 3.8,
                "Syllabus Alignment": 4.2,
                "Exam Readiness": 4.0
            }}
        }}
        Provide real numerical ratings between 1.0 and 5.0.
        """
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=analytics_prompt,
            config=config
        )
        
        ai_metrics = json.loads(response.text.strip())
        
        current_data = load_local_metrics()
        current_data["strengths"] = ai_metrics.get("strengths", current_data["strengths"])
        current_data["weaknesses"] = ai_metrics.get("weaknesses", current_data["weaknesses"])
        current_data["ratings"] = ai_metrics.get("ratings", current_data["ratings"])
        current_data["test_history"].append({
            "subject": subject,
            "type": test_type,
            "summary": performance_summary
        })
        
        save_local_metrics(current_data)
    except Exception as e:
        st.error(f"Background Analytics Parsing Fault: {str(e)}")

def render_dashboard_interface():
    st.header("📊 Student Analytics & Performance Dashboard")
    st.caption("Locally stored telemetry metrics optimizing exam preparation strategies.")
    
    metrics = load_local_metrics()
    
    st.subheader("🎯 Academic Capability Ratings")
    col1, col2, col3, col4 = st.columns(4)
    
    ratings = metrics.get("ratings", {})
    with col1:
        st.metric(label="🧠 Conceptual Clarity", value=f"{ratings.get('Conceptual Clarity', 3.0)} / 5.0")
    with col2:
        st.metric(label="⏱️ Time Management", value=f"{ratings.get('Time Management', 3.0)} / 5.0")
    with col3:
        st.metric(label="📚 Syllabus Alignment", value=f"{ratings.get('Syllabus Alignment', 3.0)} / 5.0")
    with col4:
        st.metric(label="🎓 Exam Readiness", value=f"{ratings.get('Exam Readiness', 3.0)} / 5.0")
        
    st.divider()
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.success("### 💪 Core Identified Strengths")
        for strength in metrics.get("strengths", []):
            st.markdown(f"* {strength}")
            
    with col_right:
        st.error("### ⚠️ Focus Areas & Weaknesses")
        for weakness in metrics.get("weaknesses", []):
            st.markdown(f"* {weakness}")
            
    st.divider()
    
    st.subheader("📈 Competency Matrix Chart")
    st.bar_chart(ratings)