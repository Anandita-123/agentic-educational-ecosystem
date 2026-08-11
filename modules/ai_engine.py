import os
import streamlit as st
from google import genai
from google.genai import types
from modules.database import get_supabase_client
from modules.metadata import get_subjects_for_student, resolve_paper_code

def clean_code_string(code: str) -> str:
    """Standardizes strings by removing spaces, hyphens, and converting to uppercase."""
    return "".join(c.upper() for c in code if c.isalnum())

def load_global_university_schedules() -> str:
    """
    Scans the university folder to ingest calendars, 
    holidays, and exam notice files into the global context bundle.
    """
    # FIXED: Re-aligned folder pathway to look into university cleanly
    directory_path = "knowledge_base/university"
    if not os.path.exists(directory_path):
        return "[NOT_FOUND] Global timeline folder not currently active."
        
    combined_schedules = []
    try:
        for filename in os.listdir(directory_path):
            if filename.endswith(".txt"):
                full_path = os.path.join(directory_path, filename)
                with open(full_path, "r", encoding="utf-8") as f:
                    combined_schedules.append(f"--- FILE: {filename} ---\n{f.read()}")
        return "\n\n".join(combined_schedules) if combined_schedules else "[NOT_FOUND] No schedule files found."
    except Exception as e:
        return f"Error reading schedule timeline directory: {str(e)}"

def load_target_syllabus_file(stream: str, semester: str, subject_name: str) -> str:
    """
    Locates and reads the standard curriculum .txt file for a selected course.
    Scans the nested /Syllabus subfolder inside the stream directory.
    """
    if subject_name == "General Topics":
        return "[NOT_FOUND]"
    target_code = resolve_paper_code(stream, semester, subject_name)
    if target_code == "UNKNOWN":
        return "[NOT_FOUND]"
    
    clean_target = clean_code_string(target_code)
    directory_path = f"knowledge_base/{stream}/Syllabus"
    
    if not os.path.exists(directory_path):
        directory_path = f"knowledge_base/{stream}"
        if not os.path.exists(directory_path):
            return "[NOT_FOUND]"
            
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt") and "_pyq" not in filename.lower() and "_notes" not in filename.lower():
            if clean_target in clean_code_string(filename.replace(".txt", "")):
                try:
                    with open(os.path.join(directory_path, filename), "r", encoding="utf-8") as f:
                        return f.read()
                except Exception:
                    pass
    return "[NOT_FOUND]"

def load_target_pyq_file(stream: str, semester: str, subject_name: str) -> str:
    """
    Locates and reads the matching previous year question papers text file.
    Supports stream-wide batch text processing fallbacks.
    """
    if subject_name == "General Topics":
        return "[NOT_FOUND]"
    target_code = resolve_paper_code(stream, semester, subject_name)
    clean_target = clean_code_string(target_code)
    
    directory_path = f"knowledge_base/{stream}"
    if not os.path.exists(directory_path):
        return "[NOT_FOUND]"
        
    search_paths = [directory_path, os.path.join(directory_path, "PYQs"), os.path.join(directory_path, "pyq"), os.path.join(directory_path, "pyqs"), os.path.join(directory_path, "PYQ"), os.path.join(directory_path, "Syllabus")]
    fallback_files = []
    
    for path in search_paths:
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.endswith(".txt"):
                    fn_lower = filename.lower()
                    
                    if "pyq" in fn_lower and stream.lower() in fn_lower:
                        fallback_files.append(os.path.join(path, filename))
                        
                    clean_filename = clean_code_string(filename.replace(".txt", ""))
                    if clean_target in clean_filename or clean_filename in clean_target:
                        try:
                            with open(os.path.join(path, filename), "r", encoding="utf-8") as f:
                                return f.read()
                        except Exception:
                            pass
                            
    if fallback_files:
        combined_fallback = []
        for file_path in fallback_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    combined_fallback.append(f"--- BATCH PYQ FILE SOURCE: {os.path.basename(file_path)} ---\n{f.read()}")
            except Exception:
                pass
        if combined_fallback:
            return "\n\n".join(combined_fallback)
            
    return "[NOT_FOUND]"

def load_target_notes_file(stream: str, semester: str, subject_name: str) -> str:
    """Locates and reads the detailed student/lecture notes text file."""
    if subject_name == "General Topics":
        return "[NOT_FOUND]"
    target_code = resolve_paper_code(stream, semester, subject_name)
    clean_target = clean_code_string(target_code)
    
    directory_path = f"knowledge_base/{stream}"
    if not os.path.exists(directory_path):
        return "[NOT_FOUND]"
        
    search_paths = [directory_path, os.path.join(directory_path, "Notes"), os.path.join(directory_path, "Syllabus")]
    fallback_files = []
    
    for path in search_paths:
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.endswith(".txt"):
                    fn_lower = filename.lower()
                    
                    if "notes" in fn_lower and stream.lower() in fn_lower:
                        fallback_files.append(os.path.join(path, filename))
                        
                    clean_filename = clean_code_string(filename.replace(".txt", ""))
                    if clean_target in clean_filename or clean_filename in clean_target:
                        try:
                            with open(os.path.join(path, filename), "r", encoding="utf-8") as f:
                                return f.read()
                        except Exception:
                            pass
                            
    if fallback_files:
        combined_fallback = []
        for file_path in fallback_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    combined_fallback.append(f"--- BATCH NOTES SOURCE: {os.path.basename(file_path)} ---\n{f.read()}")
            except Exception:
                pass
        if combined_fallback:
            return "\n\n".join(combined_fallback)
            
    return "[NOT_FOUND]"

def get_or_create_context_cache(stream: str, semester: str, subject_name: str) -> str:
    """Combines all regional branch documents alongside global timelines into a server cache window."""
    client = genai.Client()
    target_code = resolve_paper_code(stream, semester, subject_name) if subject_name != "General Topics" else "GENERAL"
    cache_key = f"cache_token_{stream}_{clean_code_string(target_code)}"
    
    if cache_key in st.session_state:
        return st.session_state[cache_key]
        
    syllabus = load_target_syllabus_file(stream, semester, subject_name)
    pyqs = load_target_pyq_file(stream, semester, subject_name)
    notes = load_target_notes_file(stream, semester, subject_name)
    schedules = load_global_university_schedules()
    
    combined_payload = f"""
    === GLOBAL UNIVERSITY SCHEDULES & TIMELINES ===
    {schedules}
    
    === SUBJECT Blueprints ===
    {syllabus}
    
    === PAST EXAMINATION PAPERS (PYQS) ===
    {pyqs}
    
    === CLASSROOM LECTURE NOTES ===
    {notes}
    """
    
    try:
        with st.spinner(f"Warming up cloud hybrid memory blocks..."):
            cloud_cache = client.caches.create(
                model="gemini-2.5-flash",
                config=types.CreateCachedContentConfig(
                    displayName=f"hybrid_cache_{clean_code_string(target_code).lower()}",
                    contents=[combined_payload],
                    ttl="86400s"
                )
            )
            st.session_state[cache_key] = cloud_cache.name
            return cloud_cache.name
    except Exception:
        return None

def render_chat_interface(profile: dict):
    """Renders the conversational layer utilizing a cascading framework for deep grounding and open exploration."""
    st.header(f"💬 {profile['stream']} AI Academic Agent")
    
    profile_saved_subjects = profile.get("selected_subjects", [])
    available_subjects = list(profile_saved_subjects) if profile_saved_subjects else get_subjects_for_student(profile['stream'], profile['semester'])
        
    if "General Topics" not in available_subjects:
        available_subjects.append("General Topics")
        
    selected_focus = st.selectbox("🎯 Target a Specific Course Module for this Chat Session:", available_subjects)

    client = genai.Client()
    cache_token = get_or_create_context_cache(profile['stream'], profile['semester'], selected_focus)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.sidebar.markdown(msg["content"]) if msg["role"] == "user" else st.markdown(msg["content"])

    if user_prompt := st.chat_input("Ask me about timelines, holiday schedules, notes, or any global topic..."):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):
            with st.spinner("Analyzing knowledge bases and timeline networks..."):
                
                paper_code = resolve_paper_code(profile['stream'], profile['semester'], selected_focus)
                
                syllabus_txt = load_target_syllabus_file(profile['stream'], profile['semester'], selected_focus)
                pyq_txt = load_target_pyq_file(profile['stream'], profile['semester'], selected_focus)
                notes_txt = load_target_notes_file(profile['stream'], profile['semester'], selected_focus)
                schedule_txt = load_global_university_schedules()

                semester_full_catalog = get_subjects_for_student(profile['stream'], profile['semester'])
                catalog_with_codes = [f"- {sub} (Code: {resolve_paper_code(profile['stream'], profile['semester'], sub)})" for sub in semester_full_catalog]
                catalog_str = "\n".join(catalog_with_codes)
                
                user_selected_str = "\n".join([f"- {s} (Code: {resolve_paper_code(profile['stream'], profile['semester'], s)})" for s in profile_saved_subjects]) if profile_saved_subjects else "None selected yet."

                system_context = f"""
                You are a highly advanced, ultra-precise AI Academic Agent for MAKAUT University.
                The student is currently registered under Stream: {profile['stream']} | Semester: {profile['semester']}.
                The current session UI view frame is targeted strictly at: {selected_focus} (Paper Code: {paper_code}).
                
                MASTER SYSTEM DIRECTORY REGISTRY (Always Available from metadata):
                [Full Master Semester Curriculum Blueprint]:
                {catalog_str}
                
                [Student's Custom Checked/Saved Course Selections]:
                {user_selected_str}

                CRITICAL FILE DATA AVAILABILITY DETECTORS:
                If a context payload below contains "[NOT_FOUND]" or is missing actual data entries, that asset does not exist.
                - Detailed Syllabus Notes Text Status: {"MISSING" if "[NOT_FOUND]" in syllabus_txt or not syllabus_txt.strip() else "AVAILABLE"}
                - Detailed PYQ Past Paper Text Status: {"MISSING" if "[NOT_FOUND]" in pyq_txt or not pyq_txt.strip() else "AVAILABLE"}
                - Detailed Classroom Notes Text Status: {"MISSING" if "[NOT_FOUND]" in notes_txt or not notes_txt.strip() else "AVAILABLE"}

                MANDATORY FORMATTING & READABILITY INSTRUCTIONS:
                When displaying any retrieved question paper, syllabus, or timeline notes context, you MUST present the text in a highly clean, structured, and visually human-readable Markdown format:
                1. Use bold Markdown titles (e.g., `### 📝 Group A - Short Answer Type`) instead of plain text tags.
                2. Put question tables or timeline event dates into neat Markdown tables with proper headers where appropriate.
                3. Add full section dividers (`---`) between major blocks to prevent wall-of-text layouts.
                4. Maintain distinct ordered list parameters for itemized questions.

                MANDATORY RULES FOR UN-UPLOADED FILES:
                If the "Detailed PYQ Past Paper Text Status" is flagged as MISSING, and the user asks for "past papers", "2025 question paper", "exam questions", or any exam year variation for this subject, you are strictly FORBIDDEN from creating a mock exam layout, inventing group questions, or guessing topics.
                You must stop and respond exactly with:
                "I do not have the official past year question papers for {selected_focus} ({paper_code}) in my knowledge base. Let me know if you would like me to help you review the core syllabus topics instead."

                MANDATORY PREVIOUS YEAR QUESTION PAPERS LAYOUT RULE:
                If the files are AVAILABLE and the user requests past papers, provide ONLY the actual question text lines present in the context below. Do not generate or attach answers unless the user explicitly requests answers within their prompt.

                CASCADING GENERAL KNOWLEDGE FALLBACK Paradigm:
                If the user asks a completely out-of-scope non-academic question (e.g., "Who is Messi?"), bypass the university file constraints entirely and answer beautifully using your pre-trained dataset weights.
                """
                
                formatted_contents = []
                for m in st.session_state.messages:
                    role_label = "user" if m["role"] == "user" else "model"
                    formatted_contents.append({"role": role_label, "parts": [{"text": m["content"]}]})

                response_text = None
                model_pipeline = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
                
                for target_model in model_pipeline:
                    try:
                        config = types.GenerateContentConfig(
                            system_instruction=system_context,
                            temperature=0.1
                        )
                        
                        config.system_instruction = system_context + f"""
                        \n\n[GLOBAL UNIVERSITY TIMELINES & SCHEDULES NOTICES]:
                        {schedule_txt}
                        
                        [SUBJECT SYLLABUS SOURCE]:
                        {syllabus_txt}
                        
                        [VERIFIED SUBJECT PAST PAPERS Pool]:
                        {pyq_txt}
                        
                        [STUDENT CLASSROOM NOTES CONTEXT]:
                        {notes_txt}
                        """

                        if target_model == "gemini-2.5-flash" and cache_token:
                            config.cached_content = cache_token

                        response = client.models.generate_content(
                            model=target_model,
                            contents=formatted_contents,
                            config=config
                        )
                        
                        if response.text and response.text.strip():
                            response_text = response.text
                            st.toast(f"🎯 Handled via active server node: {target_model}", icon="✅")
                            break
                            
                    except Exception:
                        continue

                if not response_text:
                    response_text = "🚨 Academic Agent offline due to cloud request saturation. Please try again in 10 seconds!"

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})