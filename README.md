This is the sophisticated, professional introduction you should place at the very top of your README.md file to explain the project to recruiters, developers, or professors.

# Adaptive Educational Ecosystem Using Agentic AI

Overview
The Agentic Educational Ecosystem is an intelligent, domain-specific platform engineered to streamline academic preparation for undergraduate engineering students. Built to counter the data fragmentation and contextual hallucinations common in generalized AI models, this system establishes a localized, highly structured workspace that seamlessly integrates with official university curricula.

Powered by a folder-based Retrieval-Augmented Generation (RAG) architecture, the application dynamically injects verified institutional materials—such as branch syllabi, academic calendars, and historical previous years' question papers (PYQs)—directly into the large language model’s context window. This ensures that every conversational interaction and generated practice material remains strictly bounded by official institutional guidelines.

Core Architecture & Modules
The ecosystem operates through a secure Streamlit web interface and is decoupled into four primary, agentic workflows:

Academic AI Chatbot: A real-time, RAG-grounded conversational agent that provides hallucination-free curriculum assistance based on the student's authenticated branch and semester.

Mock Test Sandbox: A programmatic document compilation engine that utilizes PyLaTeX to translate generative text payloads into mathematically stable, printable assessment PDFs matching official Continuous Assessment (CA) blueprints.

Question Prediction Agent (ETPA): An analytical module that leverages sequence-matching algorithms to evaluate chronological historical exam data, calculate topic recurrence frequencies, and forecast high-probability examination concepts.

Offline Learning Analytics: A localized telemetry loop that intercepts interactive session logs to compute multi-variable capability ratings (e.g., conceptual clarity, time management) without incurring continuous cloud database compute overheads.

Tech Stack

Frontend & Routing: Python, Streamlit

Identity & Database: Supabase (PostgreSQL)

AI Inference Engine: Google Gemini API

Document Generation: PyLaTeX

Trend Analytics: RapidFuzz

Here are the comprehensive **Installation & Setup** instructions to seamlessly append to your 'README.md' file. This guide ensures that any evaluator, recruiter, or developer can clone and run your environment perfectly on their local machine.


**Installation & Setup**

**Prerequisites**

Before initializing the application, ensure your local environment has the following installed:
Python 3.10+
Git
A LaTeX Distribution: Required for PyLaTeX to compile the mock test PDFs.
i.      Windows: Install [MiKTeX](https://miktex.org/download)
ii.     macOS: Install [MacTeX](https://www.tug.org/mactex/)
iii.    Linux: Run 'sudo apt-get install texlive-full'

**1. Clone the Repository**
Open your terminal and clone the project to your local machine:
git clone https://github.com/YourUsername/agentic-educational-ecosystem.git
cd agentic-educational-ecosystem

**2. Initialize the Virtual Environment**
To prevent dependency clashing, it is highly recommended to run this project inside an isolated virtual environment.

Create the environment:
python -m venv .venv

Activate the environment:
Windows:        .venv\Scripts\activate
macOS/Linux:    source .venv/bin/activate

**3. Install Dependencies**
With your virtual environment active, install the required Python packages from the requirements manifest:
pip install -r requirements.txt

**4. Configure Environment Variables**
The application relies on external cloud providers for authentication and LLM inference. You must configure your API keys securely.

i.  Create a new file in the root directory named exactly '.env' (do not commit this file to GitHub).
ii. Add the following credentials to the file:

Supabase Cloud Database Credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-secure-anon-public-key

Google Gemini API Credentials
GEMINI_API_KEY=your-google-gemini-api-key

**5. Verify the Knowledge Base Architecture**
For the folder-based RAG pipeline to function without throwing '[NOT_FOUND]' errors, ensure your 'knowledge_base' folder follows this strict hierarchical taxonomy:
knowledge_base/
├── CSE(AI & ML)/
│   ├── Notes/
│   ├── PYQs/
│   └── Syllabus/
├── CSE/
├── IT/
└── university/

**6. Launch the Application**
Once the environment is configured and dependencies are installed, boot up the Streamlit server:
streamlit run app.py

The application will automatically compile the interface and launch the student portal in your default web browser at 'http://localhost:8501'.


Implementation Note: If you are testing the Mock Test Sandbox module, please ensure your local LaTeX distribution is fully added to your system's PATH variables, otherwise, the programmatic PDF compilation thread will fail.