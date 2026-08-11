import streamlit as st
from modules.database import get_supabase_client
from modules.metadata import get_semester_curriculum_structure, resolve_paper_code

def render_profile_management_center(profile: dict):
    """
    Renders a unified Academic Profile Control Center.
    Allows users to update their university parameters and customize saved subject tracking arrays.
    """
    st.header("⚙️ Academic Profile Control Center")
    st.caption("Manage university parameters, update active semesters, and customize course lists.")

    supabase = get_supabase_client()

    # --- SECTION 1: UNIVERSITY DETAILS CONFIGURATION ---
    st.subheader("🎓 University & Academic Details")
    
    with st.form(key="university_details_update_form"):
        col1, col2 = st.columns(2)
        with col1:
            current_stream = st.selectbox(
                "Active Stream / Branch", 
                ["AIML", "CSE", "IT"], 
                index=["AIML", "CSE", "IT"].index(profile.get("stream", "AIML"))
            )
        with col2:
            current_semester = st.selectbox(
                "Current Semester", 
                [str(i) for i in range(1, 9)], 
                index=int(profile.get("semester", "1")) - 1
            )
            
        save_details_btn = st.form_submit_button("🔄 Update Academic Milestone Parameters", use_container_width=True)
        
    if save_details_btn:
        try:
            # Clear historical context tokens upon milestone transformation shifts
            for key in list(st.session_state.keys()):
                if "cache_token_" in key:
                    del st.session_state[key]
                    
            supabase.table("profiles").update({
                "stream": current_stream,
                "semester": current_semester,
                "selected_subjects": []  
            }).eq("id", profile["id"]).execute()
            
            st.success("Milestones updated successfully! Subject metrics refreshed.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to synchronize variables: {str(e)}")

    st.divider()

    # --- SECTION 2: THE INTERACTIVE CUSTOM SELECTION CHECKLIST ---
    st.subheader("🎯 Active Curriculum Subject Mapping")
    st.caption("Toggle your registered course subjects below. Saved choices directly update the Chatbot Console and Mock Test Engine.")

    all_subjects_pool = get_semester_curriculum_structure(profile.get("stream"), profile.get("semester"))

    if not all_subjects_pool:
        st.warning("No curriculum mappings established for this specific branch or semester yet.")
        return

    currently_saved_choices = profile.get("selected_subjects", [])

    st.markdown("#### Check your active courses for this semester:")
    
    chosen_subjects_list = []
    
    for sub in all_subjects_pool:
        is_checked_default = (sub["name"] in currently_saved_choices) if currently_saved_choices else True
        
        label_text = f"**{sub['name']}** `[{sub['code']}]`"
        checked = st.checkbox(label_text, value=is_checked_default, key=f"check_{sub['code']}")
        if checked:
            chosen_subjects_list.append(sub["name"])

    st.markdown("")
    save_subjects_btn = st.button("💾 Save Selected Academic Subject List", use_container_width=True, type="primary")

    if save_subjects_btn:
        try:
            # CRITICAL CACHE CLEAR RULE:
            # Force purge existing memory mapping slots to overwrite old 24-hour server context frames
            for sub in all_subjects_pool:
                clean_token = "".join(c.upper() for c in sub['code'] if c.isalnum())
                cache_key = f"cache_token_{profile.get('stream')}_{clean_token}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]

            supabase.table("profiles").update({
                "selected_subjects": chosen_subjects_list
            }).eq("id", profile["id"]).execute()
            
            st.success("Academic workspace updated cleanly! Memory structures flushed and updated.")
            st.rerun()
        except Exception as e:
            st.error(f"Subject configuration alignment fault: {str(e)}")