"""
Central configuration data registry for MAKAUT curriculum tracking.
Acts as a high-speed dictionary cache mapping student selections directly to 
their specific university Paper Codes for precise localized RAG lookups.
"""

STREAM_CURRICULUM = {
    "AIML": {
        "1": [
            {"name": "Mathematics-I", "code": "BSM101"},
            {"name": "Physics-I", "code": "BSPH101"},
            {"name": "Basic Electrical Engineering", "code": "ESEE101"}
        ],
        "2": [
            {"name": "Mathematics-IIA", "code": "BSM201"},
            {"name": "Chemistry", "code": "BSCH201"},
            {"name": "English", "code": "HMHU201"},
            {"name": "Programming for Problem Solving", "code": "ESCS201"}
        ],
        "3": [
            {"name": "Data Structure & Algorithm ", "code": "PCCCS301"},
            {"name": "Computer Organization", "code": "PCCCS302"},
            {"name": "Economics for Engineers (Humanities-II)", "code": "HSMC301"},
            {"name": "Analog & Digital Electronics", "code": "ESC301"},
            {"name": "Linear Algebra (BS) ", "code": "BSCAIML301"}
        ],
        "4": [
            {"name": "Discrete Mathematics", "code": "PCCCS401"},
            {"name": "Design and Analysis of Algorithms", "code": "PCCCS404"},
            {"name": "Biology", "code": "BSC401"},
            {"name": "Environmental Sciences", "code": "MC401"},
            {"name": "Artificial Intelligence", "code": "PCCAIML401"},
            {"name": "Environmental Sciences", "code": "MC401"},
            {"name": "OPTIMIZATION TECHNIQUES ", "code": "PCCAIML402"}
        ],
        "5": [
            {"name": "Probability & Statistics", "code": "PCCAIML501"},
            {"name": "Operating Systems", "code": "PCCCS502"},
            {"name": "Object Oriented Programming", "code": "PCCCS503"},
            {"name": "Introduction to Machine Learning", "code": "PCCAIML502"},
            {"name": "Introduction to Industrial Management", "code": "HSMC501"},
            {"name": "Cloud Computing", "code": " PECAIML501A"},
            {"name": "Pattern Recognition", "code": " PECAIML501B"},
            {"name": "Graph Theory", "code": " PECAIML501C"}
        ],
        "6": [
            {"name": "Application of machine learning in industries", "code": "PCCAI601"},
            {"name": "Deep Learning", "code": "PCCAIML602"},
            {"name": "Soft Computing", "code": "PCCAIML603"},
            {"name": "Computer Networks", "code": "PCCCS602"},
            {"name": "Big Data Analytics", "code": "PECAI601A"},
            {"name": "Distributed Systems", "code": "PECAIML601C"},
            {"name": "Data Mining", "code": "PECAIML601B"},
            {"name": "Database Management Systems", "code": "OECAIML601A"},
            {"name": "Human Computer Interaction", "code": "OECAIML601B"},
            {"name": "Neural Networks", "code": "OECAIML601C"},
            {"name": "Cryptography & Network Security", "code": "OECAIML601D"}
        ],
        "7": [
            {"name": "Quantum Computing", "code": "PECAIML701C"},
            {"name": "Multi-agent Intelligent Systems", "code": "PECAIML701D"},
            {"name": "Computer Vision", "code": "PECAIML701B"},
            {"name": "Information Theory and Coding", "code": "OECAIML702B"},
            {"name": "Digital Signal Processing", "code": "PECAIML701D(1)"},
            {"name": "Social Network Analysis", "code": "PECAIML701A"},
            {"name": "E-Commerce & ERP:", "code": "PECAIML702A"},
            {"name": "Internet of Things", "code": "OECAIML701A"},
            {"name": "Bioinformatics", "code": "OECAIML701B"},
            {"name": "Robotics", "code": "OECAIML701C"},
            {"name": "Compiler Design", "code": "OECAIML701D"},
            {"name": "Project Management and Entrepreneurship", "code": "HSMC701"}
        ],
        "8": [
            {"name": "Cyber Law and Ethics", "code": "PECAIML801B"},
            {"name": "Research Methodology", "code": "OECAIML802B"},
            {"name": "Software Engineering", "code": "OECAIML801C"},
            {"name": "Human Resource Development and Organizational Behavior", "code": "OECAIML802A"},
            {"name": "Natural Language Processing", "code": "PECAIML801A"},
            {"name": "Mobile Computing", "code": "PECAIML801C"},
            {"name": "Economic Policies in India", "code": "OECAIML801A"},
            {"name": "Micro-electronics and VLSI Design", "code": "OECAIML801B"},
            {"name": "Soft Skill & Interpersonal Communication", "code": "OECAIML802C"}
        ]
    },
    "CSE": {
        "1": [
            {"name": "Mathematics-I", "code": "BSM101"},
            {"name": "Chemistry", "code": "BSCH101"},
            {"name": "Programming for Problem Solving", "code": "ESCS101"}
        ],
        "2": [
            {"name": "Mathematics-II", "code": "BSM201"},
            {"name": "Physics-I", "code": "BSPH201"},
            {"name": "Basic Electrical Engineering", "code": "ESEE201"}
        ],
        "3": [
            {"name": "Data Structures", "code": "PCCCS301"},
            {"name": "Computer Organization", "code": "PCCCS302"},
            {"name": "Digital Electronics", "code": "ESC301"}
        ],
        "4": [
            {"name": "Design & Analysis of Algorithms", "code": "PCCCS401"},
            {"name": "Operating Systems", "code": "PCCCS402"},
            {"name": "Discrete Mathematics", "code": "PCCCS403"}
        ],
        "5": [
            {"name": "Database Management Systems", "code": "PCCCS501"},
            {"name": "Formal Language & Automata Theory", "code": "PCCCS502"},
            {"name": "Computer Networks", "code": "PCCCS503"}
        ],
        "6": [
            {"name": "Compiler Design", "code": "PCCCS601"},
            {"name": "Software Engineering", "code": "PCCCS602"},
            {"name": "Distributed Systems", "code": "PECCS601A"}
        ],
        "7": [
            {"name": "Information Security", "code": "PCCCS701"},
            {"name": "Quantum Computing", "code": "PECS701A"}
        ],
        "8": [
            {"name": "Project Work", "code": "PROJCS801"},
            {"name": "Comprehensive Viva", "code": "VIVACS802"}
        ]
    },
    "IT": {
        "1": [
            {"name": "Mathematics-I", "code": "BSM101"},
            {"name": "Physics-I", "code": "BSPH101"},
            {"name": "Basic Electrical Engineering", "code": "ESEE101"}
        ],
        "2": [
            {"name": "Mathematics-II", "code": "BSM201"},
            {"name": "Chemistry", "code": "BSCH201"},
            {"name": "Programming for Problem Solving", "code": "ESCS201"}
        ],
        "3": [
            {"name": "Data Structures", "code": "PCCIT301"},
            {"name": "Analog & Digital Electronics", "code": "ESCIT301"},
            {"name": "Mathematics-III", "code": "BSMIT301"}
        ],
        "4": [
            {"name": "Design & Analysis of Algorithms", "code": "PCCIT401"},
            {"name": "Operating Systems", "code": "PCCIT402"},
            {"name": "Object Oriented Programming", "code": "PCCIT403"}
        ],
        "5": [
            {"name": "Database Management Systems", "code": "PCCIT501"},
            {"name": "Software Engineering", "code": "PCCIT502"},
            {"name": "E-Commerce", "code": "PECIT501A"}
        ],
        "6": [
            {"name": "Computer Networks", "code": "PCCIT601"},
            {"name": "Web Technology", "code": "PCCIT602"},
            {"name": "Data Warehousing & Data Mining", "code": "PECIT601B"}
        ],
        "7": [
            {"name": "Cloud Computing", "code": "PCCIT701"},
            {"name": "Internet of Things", "code": "PECIT701A"}
        ],
        "8": [
            {"name": "Project Work", "code": "PROJIT801"},
            {"name": "Grand Viva", "code": "VIVAIT802"}
        ]
    }
}

EXAM_MARKING_SCHEMES = {
    "CA3": (
        "MAKAUT CA3 Assessment Structure:\n"
        "- Total Marks: 25 Marks\n"
        "- Time Allowed: 60 Minutes\n"
        "- Structural Sections:\n"
        "  * Group A: Answer any 5 out of 7 Very Short Answer Questions no MCQ at all(1 Mark each = 5 Marks Total)\n"
        "  * Group B: Answer any 4 out of 7 Long Questions (5 Marks each = 20 Marks Total)"
    ),
    "CA4": (
        "MAKAUT CA4 Assessment Structure:\n"
        "- Total Marks: 25 Marks\n"
        "- Time Allowed: 40 Minutes\n"
        "- Assessment Intent: Practical assignment track / report compilation evaluation\n"
        "- Structural Sections:\n"
        "  * Section I: 25 Mandatory MCQs (1 Mark each = 25 Marks Total)"
    ),
    "Semester Exam": (
        "MAKAUT End-Semester Written Examination Blueprint:\n"
        "- Total Marks: 70 Marks\n"
        "- Time Allowed: 3 Hours\n"
        "- Structural Sections:\n"
        "  * Group A: Answer any 10 out of 12 Objective Questions (Short Answer Questions/ Blank) covering all units (1 Mark each = 10 Marks Total)\n"
        "  * Group B: Answer any 3 out of 5 Descriptive Questions (5 Marks each = 15 Marks Total)\n"
        "  * Group C: Answer any 3 out of 5 Comprehensive Long Answer Questions (15 Marks each = 45 Marks Total)"
    )
}

def get_semester_curriculum_structure(stream: str, semester: str) -> list:
    """
    Retrieves the complete flat list of subjects for a target semester.
    Maintains compatibility with profile dynamic checkboxes.
    """
    return STREAM_CURRICULUM.get(stream, {}).get(str(semester), [])

def get_subjects_for_student(stream: str, semester: str) -> list:
    """Returns raw string subject names representing a semester's blueprint catalog."""
    subject_maps = STREAM_CURRICULUM.get(stream, {}).get(str(semester), [])
    if not subject_maps:
        return ["General Topics"]
    return [sub["name"] for sub in subject_maps]

def resolve_paper_code(stream: str, semester: str, subject_name: str) -> str:
    """Finds the precise paper code matched to a selected subject dropdown name."""
    subject_maps = STREAM_CURRICULUM.get(stream, {}).get(str(semester), [])
    for sub in subject_maps:
        if sub["name"] == subject_name:
            return sub["code"]
    return "UNKNOWN"

def get_cached_marking_scheme(exam_variant: str) -> str:
    """Instantly resolves pre-loaded structural strings from system memory layout cache."""
    return EXAM_MARKING_SCHEMES.get(
        exam_variant, 
        "Standard Assessment Rule: Compile a balanced test evaluated out of 25 total marks."
    )