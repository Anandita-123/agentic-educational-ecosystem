import os, re, json
import streamlit as st
from datetime import datetime
try:
    from rapidfuzz import fuzz
except ImportError:
    st.error("Missing dependency. Please run: pip install rapidfuzz")

from modules.ai_engine import load_target_syllabus_file, load_target_pyq_file
from modules.metadata import get_subjects_for_student, resolve_paper_code
from modules.mock_test import generate_pdf_bytes
from google import genai
from google.genai import types

def load_all_historical_pyqs(stream: str, semester: str, subject_name: str) -> str:
    """Grabs ALL years for a specific subject using OS-safe Absolute Paths."""
    target_code = resolve_paper_code(stream, semester, subject_name)
    if target_code == "UNKNOWN":
        return "[NOT_FOUND]"
        
    clean_target = "".join(c.upper() for c in target_code if c.isalnum())
    
    # THE FIX: Anchor to the project root to create a bulletproof absolute path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    directory_path = os.path.join(base_dir, "knowledge_base", stream, "PYQs")
    
    if not os.path.exists(directory_path):
        directory_path = os.path.join(base_dir, "knowledge_base", stream)
        if not os.path.exists(directory_path):
            return "[NOT_FOUND]"
            
    combined_pyqs = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            clean_filename = "".join(c.upper() for c in filename.replace(".txt", "") if c.isalnum())
            if clean_target in clean_filename:
                try:
                    # Safely join the absolute path with the filename
                    file_path = os.path.join(directory_path, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        year_match = re.search(r'20\d{2}', filename)
                        year_label = year_match.group() if year_match else "UNKNOWN_YEAR"
                        combined_pyqs.append(f"--- EXAM YEAR: {year_label} ---\n{f.read()}")
                except Exception as e:
                    # Log the error safely instead of crashing Streamlit
                    print(f"Warning: System bypassed {filename} due to OS lock/error - {e}")
                    pass
                    
    return "\n\n".join(combined_pyqs) if combined_pyqs else "[NOT_FOUND]"

def extract_topics_from_syllabus(syllabus_txt: str) -> list:
    """Surgically extracts topics directly from the structured syllabus YAML/Text format."""
    if "[NOT_FOUND]" in syllabus_txt or not syllabus_txt.strip():
        return []
    
    topics = re.findall(r'^topic:\s*(.+)$', syllabus_txt, flags=re.MULTILINE | re.IGNORECASE)
    if topics:
        return list(dict.fromkeys([t.strip() for t in topics if len(t.strip()) > 2]))
    
    lines = syllabus_txt.split('\n')
    fallback_topics = []
    blacklist = [
        "unit", "module", "subject_name", "subject name", "subject_code", "paper_code", 
        "paper code", "upid", "time allotted", "full marks", "metadata", "group-a", 
        "group-b", "group-c", "chunk_id", "content:", "keywords:", "program:"
    ]
    
    for line in lines:
        clean_line = re.sub(r'^[0-9\.\-\*]+\s*', '', line.strip())
        lower_line = clean_line.lower()
        if 5 < len(clean_line) < 60 and not any(bad_word in lower_line for bad_word in blacklist):
            fallback_topics.append(clean_line)
            
    return list(dict.fromkeys(fallback_topics))

def parse_pyq_history(pyq_txt: str, topics: list) -> dict:
    """Scans historical PYQs by splitting the custom Year boundaries."""
    topic_history = {topic: [] for topic in topics}
    if "[NOT_FOUND]" in pyq_txt or not pyq_txt.strip():
        return topic_history

    blocks = {}
    segments = re.split(r'---\s*EXAM YEAR:\s*(\d{4})\s*---', pyq_txt)
    
    for i in range(1, len(segments), 2):
        year = segments[i]
        text_block = segments[i+1]
        blocks[year] = text_block
        
    for year, text_block in blocks.items():
        clean_block = text_block.replace("END OF PAPER", "\n---\n") 
        for topic in topics:
            if fuzz.partial_ratio(topic.lower(), clean_block.lower()) > 85:
                if year not in topic_history[topic]:
                    topic_history[topic].append(year)
                    
    return topic_history

def calculate_etpa_scores(topic_history: dict) -> list:
    """Core Examiner Trend Prediction Algorithm (ETPA)."""
    predictions = []
    current_year = datetime.now().year
    
    for topic, years_appeared in topic_history.items():
        if not years_appeared:
            continue
            
        years_int = sorted([int(y) for y in years_appeared])
        max_year = max(years_int)
        
        freq_score = len(years_int) * 15
        gap_bonus = 20 if max_year < current_year - 1 else 0
        
        last_year_penalty = 0
        overuse_penalty = 0
        
        if max_year == current_year - 1:
            last_year_penalty = 15
            if len(years_int) >= 3 and (current_year - 2) in years_int and (current_year - 3) in years_int:
                overuse_penalty = 10
                last_year_penalty = 5 
                
        marks_bonus = 10 
        raw_score = 40 + freq_score + gap_bonus + marks_bonus - last_year_penalty - overuse_penalty
        final_score = max(15, min(98, raw_score))
        
        # UPGRADE: Eye-soothing modern HEX colors instead of harsh defaults
        if final_score >= 85:
            confidence, color = "Very High", "#10b981" # Soft Emerald Green
        elif final_score >= 70:
            confidence, color = "High", "#3b82f6"      # Ocean Blue
        elif final_score >= 50:
            confidence, color = "Moderate", "#f59e0b"  # Warm Amber
        else:
            confidence, color = "Low", "#ef4444"       # Muted Coral Red
            
        explanation = f"**Appeared in:** {', '.join(map(str, years_int))}\n\n"
        if gap_bonus > 0:
            explanation += "🔹 **Long absence:** Topic is overdue for an appearance, suggesting a possible reappearance.\n"
        if last_year_penalty > 0:
            explanation += "🔻 **Recent appearance:** Appeared last year, reducing probability slightly to avoid repetition.\n"
        if overuse_penalty > 0:
            explanation += "🔻 **Overuse detected:** Frequently repeated in consecutive years; examiner may rotate it out.\n"
        if len(years_int) >= 2:
            explanation += "⭐ **Core Topic:** Strong historical relevance and syllabus alignment.\n"
            
        predictions.append({
            "topic": topic, "score": final_score, "confidence": confidence,
            "color": color, "explanation": explanation
        })
        
    return sorted(predictions, key=lambda x: x["score"], reverse=True)

def generate_predicted_paper_json(profile: dict, subject: str, top_topics: list) -> dict:
    """Requests JSON generation from AI without interacting with Streamlit Session State."""
    paper_code = resolve_paper_code(profile['stream'], profile['semester'], subject)
    
    total_score = sum([t["score"] for t in top_topics[:5]])
    topic_distribution = [f"- {t['topic']}: ~{round((t['score'] / total_score) * 25)} Marks" for t in top_topics[:5]]
    topic_distribution_str = "\n".join(topic_distribution)
    
    prompt = f"""
    You are an elite external paper setter for MAKAUT University. 
    Based on the Examiner Trend Prediction Algorithm(ETPA), you must generate a 25-mark examination paper for {subject} ({paper_code}).
    
    CRITICAL TOPIC MARK DISTRIBUTION (You MUST allocate questions to match these marks approximately):
    {topic_distribution_str}
    CRITICAL QUANTITY RULE: You MUST generate EXACTLY 10 questions in total. Do not generate 5 questions. Generate exactly 10.

    MATHEMATICAL, SCIENTIFIC AND LATEX FORMATTING MANDATE:
    1. CRITICAL MATH RULE: EVERY mathematical equation, variable, and symbol MUST be wrapped in dollar signs ($...$). If an option is a math equation, wrap the ENTIRE option in dollar signs.
    2. CRITICAL JSON ESCAPE RULE: You MUST double-escape all LaTeX backslashes so the JSON is valid. Write \\\\frac instead of \\frac, \\\\int instead of \\int.
    3. CRITICAL - MATRICES: You MUST use the LaTeX \\begin{{bmatrix}} ... \\end{{bmatrix}} environment STRICTLY inside double dollar signs ($$ ... $$). 
    4. NEVER use LaTeX commands like \\text{{}}, \\boxed{{}}, \\underline{{}}, or \\hspace{{}}. Use plain text underscores for blanks.
    5. AVOID RAW UNICODE: Do not use raw Unicode math emojis (like λ, α, β, π). You MUST use their LaTeX code equivalents (e.g., \\\\lambda, \\\\alpha, \\\\beta, \\\\pi).
    6. NEVER use the \\begin{{align}} or \\begin{{align*}} environments. Use \\begin{{aligned}} instead.
    
    Return the response STRICTLY as a raw JSON object matching this schema exactly, with NO markdown formatting:
    {{
        "university": "MAKAUT UNIVERSITY",
        "subject": "{subject} ({paper_code})",
        "exam_type": "Predicted Assessment",
        "max_marks": "25",
        "time_allowed": "60 Minutes",
        "general_instructions": ["Focus heavily on the predicted core concepts."],
        "groups": [
            {{
                "group_instruction": "Answer all questions.",
                "questions": [
                    {{
                        "q_id": 1,
                        "question_text": "Question here...",
                        "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"] 
                    }}
                ]
            }}
        ],
        "answer_key_summary": "Standard evaluation criteria."
    }}
    """
    client = genai.Client()
    response_text = None
    
    # Implementing the multi-model fallback pipeline for redundancy
    model_pipeline = ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
    
    for target_model in model_pipeline:
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            # Ensure the response object and text actually exist
            if response and response.text and response.text.strip():
                response_text = response.text
                break  # Success! Break out of the loop early
        except Exception:
            continue  # If a model fails or timeouts, silently try the next one in the pipeline
            
    # THE SHIELD: Catch the edge case where all models failed or returned None
    if not response_text:
        raise ValueError("Cloud generation limits exhausted or empty response returned. Please try again in a few moments.")
    
    # Now it is completely safe to process and clean the string
    clean_json_str = response_text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_json_str)
    
def render_prediction_agent(profile: dict):
    """Main UI for the Question Prediction Agent with Upgraded Native Styling."""
    
    # UPGRADE: Hero Banner using markdown
    st.markdown(
        """
        <div style='background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%); padding: 25px; border-radius: 12px; border: 1px solid #cbd5e1; margin-bottom: 25px;'>
            <h2 style='color: #0f172a; margin: 0;'>🎯 AI Question Prediction Engine</h2>
            <p style='color: #475569; font-size: 16px; margin: 5px 0 0 0;'>Powered by the Examiner Trend Prediction Algorithm (ETPA)</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    profile_saved_subjects = profile.get("selected_subjects", [])
    if not profile_saved_subjects:
        st.warning("No courses currently mapped. Please select your subjects in the Profile Management Center.")
        return
        
    # UPGRADE: Contained step layout
    with st.container(border=True):
        st.markdown("#### ⚙️ Step 1: Initialize Analysis")
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        
        with col1:
            subject = st.selectbox(
                "Select a subject to forecast upcoming examination trends:", 
                profile_saved_subjects, 
                key="prediction_subject_select",
                on_change=lambda: st.session_state.pop("predicted_pdf_bytes", None)
            )
            
        with col2:
            run_btn = st.button("🔍 Run ETPA Engine", use_container_width=True, type="primary")

    if run_btn:
        with st.spinner(f"Extracting historical matrices and analyzing patterns for {subject}..."):
            syllabus_txt = load_target_syllabus_file(profile['stream'], profile['semester'], subject)
            pyq_txt = load_all_historical_pyqs(profile['stream'], profile['semester'], subject)
            
            if "[NOT_FOUND]" in pyq_txt:
                st.error(f"Insufficient historical PYQ data available to run the ETPA model for {subject}.")
                return
                
            topics = extract_topics_from_syllabus(syllabus_txt)
            if not topics:
                topics = ["Linear Regression", "Logistic Regression", "Decision Trees", "K-Means", "CNN", "Backpropagation", "Gradient Descent", "Support Vector Machines"]
                
            history = parse_pyq_history(pyq_txt, topics)
            predictions = calculate_etpa_scores(history)
            
            st.session_state.current_predictions = predictions
            st.session_state.predicted_subject = subject
            st.session_state.pop("predicted_pdf_bytes", None) 
            st.rerun()
            
    if "current_predictions" in st.session_state and st.session_state.current_predictions:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🏆 Top High-Probability Topics")
        st.caption("Mathematically ranked based on recency, frequency, and rotational absence patterns.")
        
        top_predictions = st.session_state.current_predictions[:5]
        
        # UPGRADE: Interactive Card-like layout for each topic
        for idx, pred in enumerate(top_predictions):
            with st.container(border=True):
                col_text, col_score = st.columns([4, 1], vertical_alignment="center")
                
                with col_text:
                    st.markdown(f"**{idx + 1}. {pred['topic']}**")
                    st.progress(pred['score'] / 100)
                    
                with col_score:
                    # Centered, styled score using the eye-soothing hex colors
                    st.markdown(f"<h2 style='color: {pred['color']}; margin: 0; text-align: center;'>{pred['score']}%</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 13px; margin: 0;'>{pred['confidence']}</p>", unsafe_allow_html=True)
                    
                with st.expander("🔍 View ETPA Reasoning Analytics"):
                    st.markdown(pred['explanation'])
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # UPGRADE: Dedicated Action Container
        with st.container(border=True):
            st.markdown("#### 📝 Step 2: Synthesis & Compilation")
            st.info("Translate these predictive weights into a formally formatted, printable 25-mark Mock Test.")
            
            col_gen, col_down = st.columns(2, vertical_alignment="center")
            
            with col_gen:
                if st.button("✨ Compile Predicted Exam", use_container_width=True, type="secondary"):
                    with st.spinner("Instructing AI to map topics and compiling LaTeX document..."):
                        try:
                            paper_json = generate_predicted_paper_json(profile, st.session_state.predicted_subject, top_predictions)
                            pdf_bytes = generate_pdf_bytes(paper_json)
                            st.session_state.predicted_pdf_bytes = pdf_bytes
                            st.toast("Document compiled successfully!", icon="✅")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Compilation Failed: {e}")
                            
            with col_down:
                if "predicted_pdf_bytes" in st.session_state:
                    safe_filename = st.session_state.predicted_subject.replace(" ", "_")
                    st.download_button(
                        label="📥 Download PDF Document",
                        data=st.session_state.predicted_pdf_bytes,
                        file_name=f"{safe_filename}_Predicted_Exam.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary" # Makes the download button pop out
                    )
                else:
                    st.markdown("<p style='text-align:center; color:#94a3b8; font-size: 14px;'>Compile document to enable download</p>", unsafe_allow_html=True)