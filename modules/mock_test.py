import os, re, tempfile, json, warnings, streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from google import genai
from google.genai import types
from pylatex import Document, Package, Itemize
from pylatex.utils import NoEscape, escape_latex
from modules.ai_engine import load_target_syllabus_file, get_or_create_context_cache, load_target_pyq_file
from modules.metadata import get_subjects_for_student, get_cached_marking_scheme, resolve_paper_code
from modules.dashboard import log_test_for_analytics

def to_roman(num: int) -> str:
    """Converts standard integers to lowercase Roman numerals for Group A subquestions."""
    val = [10, 9, 5, 4, 1]
    syb = ["x", "ix", "v", "iv", "i"]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def enforce_uniform_instructions(paper_json: dict) -> dict:
    """Deterministically applies strict university guidelines, completely overriding LLM text."""
    if not isinstance(paper_json, dict):
        return paper_json
        
    exam_val = str(paper_json.get("exam_type", "")).strip().upper()
    
    for i, group in enumerate(paper_json.get("groups", [])):
        grp_val = str(group.get("group_name", "")).strip().upper()
        
        # CA4 and MCQ tests do not have distinct groups; clear the group name.
        if "CA4" in exam_val or "MCQ" in exam_val:
            group["group_name"] = ""
            if "CA4" in exam_val:
                group["group_instruction"] = "Answer all the questions. [1 X 25 = 25 Marks]"
            else:
                group["group_instruction"] = "Answer all questions. [1 X 10 = 10 Marks]"
            continue

        # Safely determine the group letter for Semester / CA3
        group_letter = ""
        if "GROUP A" in grp_val or "SECTION A" in grp_val:
            group_letter = "A"
        elif "GROUP B" in grp_val or "SECTION B" in grp_val:
            group_letter = "B"
        elif "GROUP C" in grp_val or "SECTION C" in grp_val:
            group_letter = "C"
        else:
            fallback_letters = ["A", "B", "C", "D"]
            group_letter = fallback_letters[i] if i < len(fallback_letters) else "A"
            
        group["group_name"] = f"GROUP {group_letter}"
        
        if "SEMESTER" in exam_val:
            if group_letter == "A":
                group["group_instruction"] = "Answer any 10 questions. [1 X 10 = 10 Marks]"
            elif group_letter == "B":
                group["group_instruction"] = "Answer any 3 questions. [5 X 3 = 15 Marks]"
            elif group_letter == "C":
                group["group_instruction"] = "Answer any 3 questions. [15 X 3 = 45 Marks]"
                
        elif "CA3" in exam_val:
            if group_letter == "A":
                group["group_instruction"] = "Answer any 5 questions. [1 X 5 = 5 Marks]"
            elif group_letter == "B":
                group["group_instruction"] = "Answer any 4 questions. [4 X 5 = 20 Marks]"
                
    return paper_json

def process_text_with_math(text: str) -> str:
    """Safely parses mathematical blocks and converts text newlines to valid LaTeX breaks."""
    if not text:
        return ""
    
    cleaned_text = str(text).replace('\\n', '\n')
    parts = re.split(r'(\$\$.*?\$\$|\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\))', cleaned_text, flags=re.DOTALL)
    processed = ""
    
    for i, part in enumerate(parts):
        if i % 2 == 1:
            part = part.replace(r'\begin{align*}', r'\begin{aligned}').replace(r'\end{align*}', r'\end{aligned}')
            part = part.replace(r'\begin{align}', r'\begin{aligned}').replace(r'\end{align}', r'\end{aligned}')
            part = re.sub(r'\\\\([a-zA-Z])', r'\\\1', part)
            processed += part
        else:
            escaped = escape_latex(part)
            escaped = escaped.replace('\n', r' \newline ')
            processed += escaped
            
    return processed

def generate_pdf_bytes(paper_data: dict) -> bytes:
    """Generates formal academic question paper bytes using PyLaTeX with robust numbering logic."""
    doc = Document(documentclass='article')
    doc.packages.append(Package('amsmath'))
    doc.packages.append(Package('amssymb'))
    doc.packages.append(Package('geometry', options=['margin=1in']))
    doc.packages.append(Package('inputenc', options=['utf8']))

    doc.append(NoEscape(r'\begin{center}'))
    doc.append(NoEscape(r'\LARGE \textbf{' + escape_latex(paper_data.get('university', 'MAKAUT UNIVERSITY')) + r'}'))
    doc.append(NoEscape(r'\end{center} \par\vspace{0.4cm}'))
    
    doc.append(NoEscape(r'\noindent\textbf{Subject:} ' + escape_latex(paper_data.get('subject', 'N/A')) + r' \hfill \textbf{Exam Type:} ' + escape_latex(paper_data.get('exam_type', 'N/A')) + r' \par\vspace{0.2cm}'))
    doc.append(NoEscape(r'\noindent\textbf{Max Marks:} ' + escape_latex(str(paper_data.get('max_marks', '25'))) + r' \hfill \textbf{Time Allowed:} ' + escape_latex(paper_data.get('time_allowed', '60 Min')) + r' \par\vspace{0.2cm}'))
    doc.append(NoEscape(r'\hrule \par\vspace{0.5cm}'))

    instructions = paper_data.get('general_instructions', [])
    if instructions:
        doc.append(NoEscape(r'\noindent\textbf{GENERAL INSTRUCTIONS:} \par'))
        with doc.create(Itemize()) as itemize:
            for ins in instructions:
                if str(ins).strip():
                    itemize.add_item(NoEscape(process_text_with_math(ins)))
        doc.append(NoEscape(r'\vspace{0.5cm}'))

    has_group_a = any("GROUP A" in str(g.get("group_name", "")).upper() for g in paper_data.get("groups", []))
    global_q_num = 2 if has_group_a else 1

    for grp in paper_data.get('groups', []):
        grp_name = str(grp.get('group_name', '')).strip()
        grp_ins = str(grp.get('group_instruction', '')).strip()
        is_group_a = "GROUP A" in grp_name.upper()

        if grp_name:
            doc.append(NoEscape(r'\begin{center}\textbf{\Large ' + process_text_with_math(grp_name) + r'}\end{center}\vspace{0.1cm}'))
        '''
        if grp_ins:
            if is_group_a:
                doc.append(NoEscape(r'\noindent\textbf{Q1. } \textit{' + process_text_with_math(grp_ins) + r'}\par\vspace{0.3cm}'))
            else:
                doc.append(NoEscape(r'\begin{center}\textit{' + process_text_with_math(grp_ins) + r'}\end{center}\vspace{0.3cm}'))
        '''
        if grp_ins:
            doc.append(NoEscape(r'\begin{center}\textit{' + process_text_with_math(grp_ins) + r'}\end{center}\vspace{0.3cm}'))
            #doc.append(NoEscape(r'\noindent\textbf{Q1. } \par\vspace{0.3cm}'))
        else:
            doc.append(NoEscape(r'\vspace{0.3cm}'))
        
        for idx, q in enumerate(grp.get('questions', [])):
            if is_group_a:
                q_display_label = f"({to_roman(idx + 1)})"
            else:
                q_display_label = f"Q{global_q_num}."
                global_q_num += 1
            
            q_raw = q.get('question_text')
            q_text = process_text_with_math(q_raw) if q_raw else ""
            
            doc.append(NoEscape(r'\vspace{0.2cm}'))
            if q_text:
                doc.append(NoEscape(fr"\noindent\textbf{{{q_display_label}}} " + q_text + r" \par"))
            else:
                doc.append(NoEscape(fr"\noindent\textbf{{{q_display_label}}} \par"))
            
            t_data = q.get('table')
            if isinstance(t_data, dict) and t_data.get('headers') and t_data.get('rows'):
                headers = t_data.get('headers', [])
                rows = t_data.get('rows', [])
                if headers and rows:
                    doc.append(NoEscape(r'\vspace{0.25cm}'))
                    align_cells = "|" + "|".join(["c"] * len(headers)) + "|"
                    doc.append(NoEscape(r'\begin{center}'))
                    doc.append(NoEscape(r'\begin{tabular}{' + align_cells + r'}'))
                    doc.append(NoEscape(r'\hline'))
                    
                    header_line = [process_text_with_math(str(h)) for h in headers]
                    doc.append(NoEscape(" & ".join(header_line) + r' \\ \hline'))
                    
                    for row in rows:
                        safe_row = [str(cell) for cell in row]
                        if len(safe_row) < len(headers):
                            safe_row.extend([""] * (len(headers) - len(safe_row)))
                        elif len(safe_row) > len(headers):
                            safe_row = safe_row[:len(headers)]
                            
                        row_line = [process_text_with_math(c) for c in safe_row]
                        doc.append(NoEscape(" & ".join(row_line) + r' \\ \hline'))
                        
                    doc.append(NoEscape(r'\end{tabular}'))
                    doc.append(NoEscape(r'\end{center}'))
                    doc.append(NoEscape(r'\vspace{0.25cm}'))
            
            subqs = q.get('subquestions', [])
            if isinstance(subqs, list) and len(subqs) > 0:
                doc.append(NoEscape(r'\vspace{0.1cm}'))
                for sq in subqs:
                    doc.append(NoEscape(r'\noindent \hspace{0.5cm}' + process_text_with_math(str(sq)) + r" \par"))
                    doc.append(NoEscape(r'\vspace{0.1cm}'))
            
            options = q.get('options', [])
            if isinstance(options, list) and len(options) > 0 and any(str(opt).strip() for opt in options):
                doc.append(NoEscape(r'\vspace{0.1cm}'))
                with doc.create(Itemize()) as opt_list:
                    for opt in options:
                        if str(opt).strip():
                            clean_opt = re.sub(r'^[A-Za-z][\.\)]\s*', '', str(opt).strip())
                            opt_list.add_item(NoEscape(process_text_with_math(clean_opt)))
            
            doc.append(NoEscape(r'\vspace{0.3cm}'))

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, 'paper')
        try:
            doc.generate_pdf(filepath, clean_tex=True, compiler='pdflatex')
            with open(filepath + '.pdf', 'rb') as f:
                pdf_bytes = f.read()
            return pdf_bytes
        except Exception as e:
            raise Exception(f"LaTeX Compilation Failed: {e}")

def render_timer(minutes: int, is_submitted: bool):
    """Embeds an upgraded, sleek dark-themed JavaScript countdown timer."""
    import time
    seconds = minutes * 60
    is_submitted_js = "true" if is_submitted else "false"
    
    raw_html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <!-- CRITICAL FIX: Cache Buster forces Streamlit to reload the JS on every new test -->
        <!-- Render Hash: {time.time()} -->
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; display: flex; justify-content: center; }}
            .timer-box {{ background: linear-gradient(145deg, #0f172a, #1e293b); border-radius: 12px; padding: 15px 30px; text-align: center; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); width: 100%; max-width: 400px; height: 90px; }}
            .label {{ color: #94a3b8; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; display: block; }}
            .clock {{ font-size: 38px; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
        </style>
    </head>
    <body>
        <div class="timer-box">
            <span class="label">⏱️ Remaining Exam Window</span>
            <div id="countdown_clock" class="clock" style="color: #f8fafc;">00:00:00</div>
        </div>
        <script>
            var total_sec = {seconds};
            var formSubmitted = false;
            var appSubmittedState = {is_submitted_js};

            function updateClock() {{
                if (appSubmittedState) {{
                    document.getElementById('countdown_clock').innerHTML = "COMPLETED";
                    document.getElementById('countdown_clock').style.color = "#10b981"; 
                    return;
                }}
                
                if (total_sec <= 0) {{
                    document.getElementById('countdown_clock').innerHTML = "TIME EXPIRED";
                    document.getElementById('countdown_clock').style.color = "#ef4444"; 
                    if (!formSubmitted) {{
                        formSubmitted = true;
                        
                        /* Foolproof DOM targeting for auto-submit */
                        var targetDoc = window.parent.document || window.document;
                        var buttons = targetDoc.getElementsByTagName('button');
                        for (var i = 0; i < buttons.length; i++) {{
                            if (buttons[i].textContent.includes("Submit Test for AI Grading")) {{
                                buttons[i].click();
                                break;
                            }}
                        }}
                    }}
                    return;
                }}
                total_sec--;
                var hrs = Math.floor(total_sec / 3600);
                var mins = Math.floor((total_sec % 3600) / 60);
                var secs = total_sec % 60;
                document.getElementById('countdown_clock').innerHTML = 
                    (hrs < 10 ? "0"+hrs : hrs) + ":" + (mins < 10 ? "0"+mins : mins) + ":" + (secs < 10 ? "0"+secs : secs);
            }}
            if (!appSubmittedState) setInterval(updateClock, 1000);
            updateClock();
        </script>
    </body>
    </html>
    """
    warnings.filterwarnings("ignore", message=".*st.components.v1.html.*")
    components.html(raw_html_content, height=120)


def load_offline_fallback_paper(subject: str, exam_variant: str, test_type: str, max_marks: int, duration_min: int) -> dict:
    return {
        "university": "MAKAUT UNIVERSITY (OFFLINE DESIGN BOX)",
        "subject": subject,
        "exam_type": exam_variant if test_type == "FULL" else "Objective MCQ Test",
        "max_marks": str(max_marks),
        "time_allowed": f"{duration_min} Minutes",
        "general_instructions": ["Bypass Active: Cloud server limits reached."],
        "groups": [{
            "group_name": " GROUP A ",
            "group_instruction": "Answer standard sample items.",
            "questions": [{"q_id": 1, "question_text": "Sample baseline text evaluation context", "table": {}, "subquestions": [], "options": []}]
        }],
        "answer_key_summary": "N/A"
    }

def render_mock_test_interface(profile: dict):
    """Renders the modernized modular question generation interface."""
    st.markdown(
        """
        <div style='background: linear-gradient(90deg, #f8fafc 0%, #e2e8f0 100%); padding: 25px; border-radius: 12px; border: 1px solid #cbd5e1; margin-bottom: 25px;'>
            <h2 style='color: #0f172a; margin: 0;'>📝 Mock Test Sandbox</h2>
            <p style='color: #475569; font-size: 16px; margin: 5px 0 0 0;'>Generate AI-powered, syllabus-aligned mock exams with automated grading.</p>
        </div>
        """, unsafe_allow_html=True
    )
    
    profile_saved_subjects = profile.get("selected_subjects", [])
    if profile_saved_subjects:
        available_subjects = list(profile_saved_subjects)
    else:
        available_subjects = ["No Course Selected"]
        st.warning("⚠️ No courses currently mapped. Go to **Profile Management** to select your subjects.")

    if "historical_question_pool" not in st.session_state:
        st.session_state.historical_question_pool = []

    with st.container(border=True):
        st.markdown("#### ⚙️ Step 1: Configure Examination Parameters")
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Select Target Subject", available_subjects, disabled=not profile_saved_subjects)
            chapters = st.text_input("Specify Target Unit / Topic", placeholder="e.g., CMOS Circuits Fundamentals, All", disabled=not profile_saved_subjects)
        
        with col2:
            test_type = st.selectbox("Select Assessment Type", ["MCQ", "FULL"], disabled=not profile_saved_subjects)
            exam_variant = "Standard Assessment"
            if test_type == "FULL":
                exam_variant = st.selectbox("Exam Mapping Type", ["CA3", "CA4", "Semester Exam"], disabled=not profile_saved_subjects)
                
        generate_btn = st.button("🚀 Initialize Exam Engine", use_container_width=True, type="primary")

    if "active_paper_json" not in st.session_state:
        st.session_state.active_paper_json = None
    if "test_evaluation" not in st.session_state:
        st.session_state.test_evaluation = None
    if "active_max_marks" not in st.session_state:
        st.session_state.active_max_marks = 25
    if "timer_minutes" not in st.session_state:
        st.session_state.timer_minutes = 60

    if not profile_saved_subjects:
        return 

    if generate_btn:
        if not chapters:
            st.warning("Please specify the chapter scopes to map your preparation accurately.")
        else:
            with st.spinner("Compiling structural schema vectors and checking endpoint quotas..."):
                if test_type == "MCQ":
                    st.session_state.active_max_marks = 10
                    st.session_state.timer_minutes = 15
                elif exam_variant == "Semester Exam":
                    st.session_state.active_max_marks = 70
                    st.session_state.timer_minutes = 180
                elif exam_variant == "CA3":
                    st.session_state.active_max_marks = 25
                    st.session_state.timer_minutes = 60
                else:
                    st.session_state.active_max_marks = 25
                    st.session_state.timer_minutes = 40

                marking_scheme_txt = get_cached_marking_scheme(exam_variant)
                paper_code_token = resolve_paper_code(profile['stream'], profile['semester'], subject)
                forbidden_questions_str = "\n".join([f"- {q}" for q in st.session_state.historical_question_pool]) if st.session_state.historical_question_pool else "None"

                syllabus_txt = load_target_syllabus_file(profile['stream'], profile['semester'], subject)
                pyq_history_txt = load_target_pyq_file(profile['stream'], profile['semester'], subject)

                latex_rules = r"""
                MATHEMATICAL, SCIENTIFIC AND LATEX FORMATTING MANDATE:
                1. CRITICAL MATH RULE: EVERY mathematical equation, variable, and symbol MUST be wrapped in dollar signs ($...$). If an option is a math equation, wrap the ENTIRE option in dollar signs.
                2. CRITICAL JSON ESCAPE RULE: You MUST double-escape all LaTeX backslashes so the JSON is valid. Write \\frac instead of \frac, \\int instead of \int, \\infty instead of \infty.
                3. NEVER use LaTeX commands like \text{}, \boxed{}, \underline{}, or \hspace{}. Use plain text underscores for blanks.
                4. AVOID RAW UNICODE: Do not use raw Unicode math symbols (like λ, α, β, π). You MUST use their LaTeX equivalents (e.g., \\lambda, \\alpha, \\beta, \\pi).
                5. NEVER use the \begin{align} or \begin{align*} environments. Use \begin{aligned} instead.
                """
                                                                             
                system_behavior = f"""
                You are an elite external paper setter for MAKAUT University specializing in paper code: {paper_code_token}.
                Generate a flawless high-quality academic evaluation paper matching this template blueprint structure exactly:
                {marking_scheme_txt if test_type == "FULL" else "Output exactly 10 challenging multiple-choice questions worth 1 mark each."}
                
                CRITICAL REPETITION CONTROL AUDIT:
                You are strictly forbidden from generating any of the following questions:
                {forbidden_questions_str}

                {latex_rules}
                
                STRUCTURAL JSON MANDATE (STRICT RESOLUTION FOR DATA TABLES & SUBQUESTIONS):
                1. CRITICAL - NO MARKDOWN TABLES: NEVER create tables using markdown (| and -) inside "question_text" or "subquestions". If a question contains a structured dataset matrix or a grid distribution table, you MUST format it STRICTLY into the "table" JSON object array provided in the template below.
                2. If a question contains multi-part subquestions (such as an 'a' part and a 'b' part), you MUST cleanly split them and isolate them inside the "subquestions" JSON array.
                3. CRITICAL - STRICT GROUP NAMING: You MUST strictly name your groups as exactly "GROUP A", "GROUP B", or "GROUP C". Do not add any extra descriptive text, question types, or marks into the group_name field.
                
                CRITICAL STRUCTURAL OUTPUT RULE:
                You must return your complete response strictly as a raw JSON object matching the following structure exactly. Do not wrap it in markdown code blocks.
                {{
                    "university": "MAKAUT UNIVERSITY",
                    "subject": "{subject} ({paper_code_token})",
                    "exam_type": "{exam_variant if test_type == 'FULL' else 'Objective MCQ Test'}",
                    "max_marks": "{st.session_state.active_max_marks}",
                    "time_allowed": "{st.session_state.timer_minutes} Minutes",
                    "general_instructions": [
                        "Answer questions meticulously based on topic constraints.",
                        "Adhere to formal marking groups specifications."
                    ],
                    "groups": [
                        {{
                            "group_name": " GROUP A ",
                            "group_instruction": "Answer comprehensive problems.",
                            "questions": [
                                {{
                                    "q_id": 15,
                                    "question_text": "Isolate the main overview prompt text here.",
                                    "table": {{
                                        "headers": ["X", "1", "2"],
                                        "rows": [
                                            ["P(X=x)", "0.4", "0.6"]
                                        ]
                                    }},
                                    "subquestions": [
                                        "a) Calculate the first metric requirement...",
                                        "b) Evaluate structural parameters context..."
                                    ],
                                    "options": [] 
                                }}
                            ]
                        }}
                    ],
                    "answer_key_summary": "Provide concise question-to-answer text keys here for subsequent grading."
                }}
                """

                model_pipeline = ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
                response_text = None
                client = genai.Client()

                for target_model in model_pipeline:
                    try:
                        config = types.GenerateContentConfig(
                            system_instruction=system_behavior + f"\n\n[OFFICIAL SYLLABUS REFERENCE CHUNKS DETAILED CONTEXT]:\n{syllabus_txt}\n\n[VERIFIED UNIVERSITY PAST PYQ QUESTION MATRIX POOL]:\n{pyq_history_txt}",
                            response_mime_type="application/json",
                            temperature=0.3
                        )
                        response = client.models.generate_content(
                            model=target_model,
                            contents=f"Generate questions mapping exactly to the requested unit/topic scope: '{chapters}'",
                            config=config
                        )
                        if response.text and response.text.strip():
                            response_text = response.text
                            st.toast(f"🎯 Paper generated via cloud server node: {target_model}", icon="✅")
                            break
                    except Exception:
                        continue

                if response_text:
                    try:
                        parsed_json_paper = json.loads(response_text)
                        
                        parsed_json_paper = enforce_uniform_instructions(parsed_json_paper)
                        
                        for group in parsed_json_paper.get("groups", []):
                            for question in group.get("questions", []):
                                q_text = question.get("question_text")
                                if q_text and q_text not in st.session_state.historical_question_pool:
                                    st.session_state.historical_question_pool.append(q_text)
                        
                        st.session_state.active_paper_json = parsed_json_paper
                        st.session_state.test_evaluation = None  
                        st.rerun()
                    except Exception as json_err:
                        st.error(f"JSON Structure Alignment Fault: {str(json_err)}")
                else:
                    st.warning("⚠️ Deploying Offline Prototyping Mode layout sandbox.")
                    fallback_paper = load_offline_fallback_paper(subject, exam_variant, test_type, st.session_state.active_max_marks, st.session_state.timer_minutes)
                    st.session_state.active_paper_json = enforce_uniform_instructions(fallback_paper)
                    st.session_state.test_evaluation = None
                    st.rerun()

    if st.session_state.active_paper_json:
        paper = st.session_state.active_paper_json
        is_submitted_flag = st.session_state.test_evaluation is not None
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🎓 Step 2: Active Examination Session")
        
        with st.container(border=True):
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Maximum Marks", paper.get('max_marks', '0'))
            col_m2.metric("Duration", paper.get('time_allowed', '0 Min'))
            col_m3.metric("Exam Type", paper.get('exam_type', 'N/A'))
            col_m4.metric("Subject Code", resolve_paper_code(profile['stream'], profile['semester'], subject))
            
            with st.expander("📝 View Exam Instructions & Download PDF"):
                for ins in paper.get("general_instructions", []):
                    st.markdown(f"* {ins}")
                try:
                    pdf_data_bytes = generate_pdf_bytes(paper)
                    st.download_button(
                        label="📥 Download Formal Exam as PDF",
                        data=pdf_data_bytes,
                        file_name=f"MAKAUT_{resolve_paper_code(profile['stream'], profile['semester'], subject)}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as pdf_err:
                    st.caption(f"PDF compilation pipeline sleeping... ({str(pdf_err)})")

        render_timer(st.session_state.timer_minutes, is_submitted_flag)
        st.markdown("<br>", unsafe_allow_html=True)

        if "student_responses" not in st.session_state:
            st.session_state.student_responses = {}

        has_group_a = any("GROUP A" in str(g.get("group_name", "")).upper() for g in paper.get("groups", []))
        global_q_num = 2 if has_group_a else 1

        with st.form(key="structured_exam_submission_form"):
            for grp in paper.get("groups", []):
                grp_name = str(grp.get('group_name', '')).strip()
                grp_ins = str(grp.get('group_instruction', '')).strip()
                is_group_a = "GROUP A" in grp_name.upper()

                if grp_name:
                    st.markdown(f"<h3 style='text-align:center; color: #1e293b;'>{grp_name}</h3>", unsafe_allow_html=True)
                
                if grp_ins:
                    if is_group_a:
                        st.markdown(f"**Q1.** *{grp_ins}*")
                    else:
                        st.markdown(f"<p style='text-align:center; font-style:italic; color: #64748b; margin-bottom: 20px;'>{grp_ins}</p>", unsafe_allow_html=True)
                
                for idx, q in enumerate(grp.get("questions", [])):
                    with st.container(border=True):
                        if is_group_a:
                            q_display_label = f"({to_roman(idx + 1)})"
                            internal_q_key = f"1_{to_roman(idx + 1)}"
                        else:
                            q_display_label = f"Q{global_q_num}."
                            internal_q_key = str(global_q_num)
                            global_q_num += 1
                        
                        ui_raw_text = q.get('question_text')
                        if ui_raw_text:
                            st.markdown(f"**{q_display_label}** {ui_raw_text}")
                        else:
                            st.markdown(f"**{q_display_label}**")

                        t_data = q.get('table')
                        if isinstance(t_data, dict) and t_data.get('headers') and t_data.get('rows'):
                            headers = t_data.get('headers', [])
                            rows = t_data.get('rows', [])
                            if headers and rows:
                                md_table = "\n| " + " | ".join([str(h).replace('|', '') for h in headers]) + " |\n"
                                md_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                                for row in rows:
                                    safe_row = [str(cell).replace('|', '') for cell in row]
                                    if len(safe_row) < len(headers):
                                        safe_row.extend([""] * (len(headers) - len(safe_row)))
                                    elif len(safe_row) > len(headers):
                                        safe_row = safe_row[:len(headers)]
                                    md_table += "| " + " | ".join(safe_row) + " |\n"
                                st.markdown(md_table)
                                st.markdown("<br>", unsafe_allow_html=True)

                        safe_group_name = grp_name.replace(" ", "_")
                        subqs = q.get("subquestions", [])
                        options_list = q.get("options", [])
                        
                        if isinstance(subqs, list) and len(subqs) > 0:
                            for sub_idx, sq in enumerate(subqs):
                                st.markdown(f"**{sq}**")
                                response_key = f"ans_{safe_group_name}_q{internal_q_key}_sub_{sub_idx}"
                                st.session_state.student_responses[response_key] = st.text_area(
                                    "Your Answer:",
                                    key=f"text_element_{safe_group_name}_q{internal_q_key}_sub_{sub_idx}",
                                    placeholder=f"Detail your solutions for part {sq[:4]} here...",
                                    disabled=is_submitted_flag
                                )
                        
                        elif isinstance(options_list, list) and len(options_list) >= 2 and any(str(opt).strip() for opt in options_list):
                            ui_options = []
                            for opt in options_list:
                                if str(opt).strip():
                                    clean_opt = re.sub(r'^[A-Za-z][\.\)]\s*', '', str(opt).strip())
                                    if ('\\' in clean_opt or '^' in clean_opt or '_' in clean_opt) and '$' not in clean_opt:
                                        clean_opt = f"${clean_opt}$"
                                    ui_options.append(clean_opt)
                                
                            response_key = f"ans_{safe_group_name}_q{internal_q_key}"
                            st.session_state.student_responses[response_key] = st.radio(
                                "Select your answer:",
                                ui_options,
                                key=f"radio_element_{safe_group_name}_q{internal_q_key}",
                                index=None,
                                disabled=is_submitted_flag 
                            )
                        
                        else:
                            response_key = f"ans_{safe_group_name}_q{internal_q_key}"
                            st.session_state.student_responses[response_key] = st.text_area(
                                "Your Answer:",
                                key=f"text_element_{safe_group_name}_q{internal_q_key}",
                                placeholder="Detail your response context here...",
                                disabled=is_submitted_flag
                            )
                                                    
            submit_btn = st.form_submit_button("📊 Submit Test for AI Grading", use_container_width=True, disabled=is_submitted_flag)
            
        if submit_btn:
            compiled_answers_summary = ""
            for key, val in st.session_state.student_responses.items():
                if key.startswith("ans_"):
                    q_name = key.replace("ans_", "").replace("_", " ")
                    compiled_answers_summary += f"Question {q_name} answer payload: {val}\n"
            
            with st.spinner("Analyzing responses..."):
                try:
                    grading_prompt = f"""
                    You are an official academic evaluator for MAKAUT University.
                    Evaluate the student's interactive responses based on the question paper rules and correct key overview.
                    
                    [ORIGINAL EXAM PAPER CONFIGURATION STRUCTURE]
                    {json.dumps(paper, indent=2)}
                    
                    [STUDENT'S SUBMITTED FORM EXAM ENTRIES]
                    {compiled_answers_summary}
                    
                    Output Requirements:
                    1. Start with "MARKS SCORED: [Calculated Score] / {st.session_state.active_max_marks}".
                    2. Provide an itemized review detailing correct vs incorrect entries.
                    3. Give actionable advice on how to improve. Wrap math variables in single dollar signs ($B(m,n)$).
                    """
                    
                    client = genai.Client()
                    grading_text = None
                    grading_pipeline = ["gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
                    
                    for grading_model in grading_pipeline:
                        try:
                            g_response = client.models.generate_content(
                                model=grading_model,
                                contents=grading_prompt
                            )
                            if g_response.text and g_response.text.strip():
                                grading_text = g_response.text
                                break
                        except Exception:
                            continue
                            
                    if grading_text:
                        st.session_state.test_evaluation = grading_text
                        try:
                            log_test_for_analytics(profile, subject, test_type, grading_text)
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error("🚨 Cloud evaluation limits active.")
                        st.session_state.test_evaluation = f"### Marks Scored: Self-Grade Required\nLocal tracking fallback verification token checklist ledger:\n`{paper.get('answer_key_summary', 'N/A')}`"
                        st.rerun()
                    
                except Exception as eval_err:
                    st.error(f"Grading Anomaly Context: {str(eval_err)}")

        if st.session_state.test_evaluation:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("### 🏆 Final Valuation Scorecard")
                st.markdown(st.session_state.test_evaluation)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_b:
                if st.button("🗑️ Clear Exam Sandbox", use_container_width=True, type="secondary"):
                    st.session_state.active_paper_json = None
                    st.session_state.test_evaluation = None
                    if "student_responses" in st.session_state:
                        del st.session_state.student_responses
                    st.rerun()