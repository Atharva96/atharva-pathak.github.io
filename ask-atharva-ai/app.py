import streamlit as st
import os
import re
from collections import Counter

# -----------------------------------
# Page config
# -----------------------------------
st.set_page_config(page_title="Ask Atharva AI", layout="wide")

# -----------------------------------
# UI header
# -----------------------------------
st.title("🤖 Ask Atharva AI – Version 2.3")
st.write("Intent-aware local portfolio assistant with cleaner recruiter-style answers.")

# -----------------------------------
# Paths
# -----------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_FOLDER = os.path.join(BASE_DIR, "..", "knowledge_base")

# -----------------------------------
# Stopwords
# -----------------------------------
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "am", "i", "me", "my", "you",
    "your", "he", "she", "it", "they", "them", "their", "this", "that", "these",
    "those", "in", "on", "at", "to", "for", "of", "and", "or", "with", "by",
    "from", "as", "about", "tell", "show", "what", "which", "who", "does", "do",
    "did", "has", "have", "had", "please", "atharva"
}

TECH_KEYWORDS = {
    "power bi", "dax", "power query", "tableau", "microstrategy", "looker",
    "ssrs", "azure", "azure data factory", "adf", "azure databricks",
    "databricks", "synapse", "azure synapse", "data lake", "sql", "python",
    "mysql", "oracle", "ssms", "ssis", "etl", "elt", "generative ai", "nlp",
    "machine learning", "predictive modeling", "speech-to-text", "recommendation systems",
    "ga4", "google analytics", "adobe analytics", "salesforce", "webengage"
}

SOFT_SKILL_WORDS = {
    "stakeholder", "communication", "problem solving", "decision-making",
    "project ownership", "attention to detail", "collaboration", "leadership"
}

INTENT_MAP = {
    "experience": {
        "keywords": [
            "experience", "career", "work", "role", "job", "employment",
            "current role", "work history"
        ],
        "preferred_files": ["experience.md"],
        "summary": "Atharva’s experience spans Business Intelligence, data engineering, analytics, and AI-led roles."
    },
    "skills": {
        "keywords": [
            "skills", "tools", "technology", "technologies", "stack", "expertise",
            "azure", "databricks", "sql", "python", "power bi", "synapse", "adf",
            "technical skills", "technical"
        ],
        "preferred_files": ["skills.md"],
        "summary": "Atharva’s skills include Business Intelligence, Azure data engineering, analytics, SQL/Python, and AI-related tools."
    },
    "projects": {
        "keywords": [
            "projects", "project", "built", "developed", "created", "solutions",
            "portfolio", "copilot", "automation"
        ],
        "preferred_files": ["project.md", "projects.md"],
        "summary": "Atharva has worked on enterprise BI, AI, automation, analytics, and data engineering projects."
    },
    "education": {
        "keywords": [
            "education", "degree", "college", "university", "study", "studied", "academic"
        ],
        "preferred_files": ["education.md"],
        "summary": "Atharva’s education combines engineering fundamentals with advanced analytics training."
    },
    "about": {
        "keywords": [
            "about", "who is", "profile", "summary", "background", "introduce"
        ],
        "preferred_files": ["about_me.md"],
        "summary": "Atharva is a senior analytics and business intelligence professional with strong technical and business impact."
    }
}


# -----------------------------------
# Helpers
# -----------------------------------
def normalize_text(text):
    return text.lower().strip()


def tokenize(text):
    text = normalize_text(text)
    words = re.findall(r"\b[a-zA-Z0-9+\-\.]+\b", text)
    return [word for word in words if word not in STOPWORDS]


def contains_any_phrase(text, phrase_set):
    text_lower = normalize_text(text)
    for phrase in phrase_set:
        if phrase in text_lower:
            return True
    return False


def is_soft_skill_query(question):
    q = normalize_text(question)
    return any(word in q for word in ["soft skill", "soft skills", "leadership", "communication", "stakeholder"])


def is_technical_skill_query(question):
    q = normalize_text(question)

    if is_soft_skill_query(q):
        return False

    # By default, generic "skills" questions should prefer technical skills
    if "skill" in q or "skills" in q:
        return True

    explicit_tech_words = [
        "technical", "technology", "technologies", "tools", "stack", "azure",
        "databricks", "sql", "python", "power bi", "synapse", "adf",
        "etl", "elt", "data engineering", "ai", "nlp", "machine learning"
    ]
    return any(word in q for word in explicit_tech_words)


def load_knowledge_files(folder):
    knowledge = {}

    if not os.path.exists(folder):
        return knowledge

    for file_name in os.listdir(folder):
        if file_name.endswith(".md"):
            file_path = os.path.join(folder, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                knowledge[file_name] = f.read()

    return knowledge


def split_into_sections(text, file_name):
    lines = text.split("\n")
    sections = []

    current_title = file_name.replace(".md", "").replace("_", " ").title()
    current_content = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#"):
            if current_content:
                section_text = "\n".join(current_content).strip()
                if section_text:
                    sections.append({
                        "file": file_name,
                        "title": current_title,
                        "content": section_text
                    })
                current_content = []

            current_title = stripped.replace("#", "").strip()
        else:
            current_content.append(line)

    if current_content:
        section_text = "\n".join(current_content).strip()
        if section_text:
            sections.append({
                "file": file_name,
                "title": current_title,
                "content": section_text
            })

    return sections


# -----------------------------------
# Detect intent
# -----------------------------------
def detect_intent(question):
    q = normalize_text(question)

    for intent_name, config in INTENT_MAP.items():
        for keyword in config["keywords"]:
            if keyword in q:
                return intent_name, config

    return "general", {
        "preferred_files": [],
        "summary": "Here is the most relevant information I found from the knowledge base."
    }


# -----------------------------------
# Score section
# -----------------------------------
def score_section(question, section, intent_name):
    question_tokens = tokenize(question)
    title_tokens = tokenize(section["title"])
    content_tokens = tokenize(section["content"])

    title_counter = Counter(title_tokens)
    content_counter = Counter(content_tokens)

    score = 0

    # Base token overlap
    for token in question_tokens:
        score += title_counter[token] * 4
        score += content_counter[token] * 1

    title_lower = normalize_text(section["title"])
    content_lower = normalize_text(section["content"])

    # Stronger section preference for skills
    if intent_name == "skills":
        technical_query = is_technical_skill_query(question)

        if technical_query:
            # Boost technical section titles
            technical_section_titles = [
                "business intelligence", "data engineering", "databases",
                "programming", "analytics", "artificial intelligence",
                "machine learning", "analytics & visualization tools"
            ]
            for tech_title in technical_section_titles:
                if tech_title in title_lower:
                    score += 20

            # Boost if technical tools appear in section content
            for tech_word in TECH_KEYWORDS:
                if tech_word in content_lower or tech_word in title_lower:
                    score += 3

            # Penalize soft skill sections
            if "professional strengths" in title_lower or "soft skills" in title_lower or "leadership" in title_lower:
                score -= 25

            for soft_word in SOFT_SKILL_WORDS:
                if soft_word in content_lower:
                    score -= 2

        else:
            # If user explicitly asks soft skills
            if "professional strengths" in title_lower or "soft skills" in title_lower or "leadership" in title_lower:
                score += 20

    return score


# -----------------------------------
# Search sections
# -----------------------------------
def search_sections(question, all_sections, preferred_files, intent_name, top_n=5):
    candidate_sections = all_sections

    if preferred_files:
        preferred_sections = [
            section for section in all_sections
            if section["file"] in preferred_files
        ]
        if preferred_sections:
            candidate_sections = preferred_sections

    scored = []
    for section in candidate_sections:
        score = score_section(question, section, intent_name)
        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Fallback to all files if nothing found in preferred files
    if not scored and preferred_files:
        for section in all_sections:
            score = score_section(question, section, intent_name)
            if score > 0:
                scored.append((score, section))
        scored.sort(key=lambda x: x[0], reverse=True)

    return scored[:top_n]


# -----------------------------------
# Extract relevant lines from top sections
# -----------------------------------
def extract_relevant_lines(question, matches, max_lines=6):
    question_lower = normalize_text(question)
    technical_query = is_technical_skill_query(question)
    soft_query = is_soft_skill_query(question)

    scored_lines = []

    for section_score, section in matches:
        lines = [line.strip() for line in section["content"].split("\n") if line.strip()]

        for line in lines:
            line_lower = normalize_text(line)
            line_score = 0

            # Prefer bullet-style lines
            if line.startswith("-"):
                line_score += 2

            # Base overlap with question tokens
            for token in tokenize(question):
                if token in line_lower:
                    line_score += 2

            # Technical boosting
            if technical_query:
                for tech_word in TECH_KEYWORDS:
                    if tech_word in line_lower:
                        line_score += 5

                for soft_word in SOFT_SKILL_WORDS:
                    if soft_word in line_lower:
                        line_score -= 3

            # Soft skill boosting
            if soft_query:
                for soft_word in SOFT_SKILL_WORDS:
                    if soft_word in line_lower:
                        line_score += 5

            # If no explicit question words, still allow strong technical lines
            if technical_query and contains_any_phrase(line_lower, TECH_KEYWORDS):
                line_score += 3

            # Avoid heading clutter unless useful
            if line.startswith("##") or line.startswith("#"):
                line_score -= 1

            if line_score > 0:
                scored_lines.append((line_score, line))

    scored_lines.sort(key=lambda x: x[0], reverse=True)

    final_lines = []
    seen = set()

    for score, line in scored_lines:
        cleaned_line = line.lstrip("-").strip()
        if cleaned_line not in seen:
            seen.add(cleaned_line)
            final_lines.append(cleaned_line)

        if len(final_lines) >= max_lines:
            break

    return final_lines


# -----------------------------------
# Build final answer
# -----------------------------------
def build_answer(question, intent_name, intent_config, matches):
    if not matches:
        return {
            "summary": "I could not find a strong match in the current knowledge base.",
            "evidence": []
        }

    q = normalize_text(question)
    yes_no_question = q.startswith(("does", "has", "is", "can"))

    evidence_lines = extract_relevant_lines(question, matches, max_lines=6)

    if intent_name == "skills":
        if yes_no_question:
            summary = "Yes — I found relevant technical skill evidence in Atharva’s knowledge base."
        elif is_soft_skill_query(question):
            summary = "Atharva’s soft skills include stakeholder management, communication, problem solving, and collaboration."
        else:
            summary = "Atharva’s technical skills include Business Intelligence, Azure data engineering, SQL/Python analytics, and AI-related tools."

    elif intent_name == "experience":
        if yes_no_question:
            summary = "Yes — I found relevant experience-based evidence in Atharva’s knowledge base."
        else:
            summary = intent_config["summary"]

    elif intent_name == "projects":
        if yes_no_question:
            summary = "Yes — I found relevant project-related evidence in Atharva’s knowledge base."
        else:
            summary = intent_config["summary"]

    elif intent_name == "education":
        summary = intent_config["summary"]

    elif intent_name == "about":
        summary = intent_config["summary"]

    else:
        if yes_no_question:
            summary = "Yes — I found relevant supporting information in Atharva’s knowledge base."
        else:
            summary = intent_config["summary"]

    return {
        "summary": summary,
        "evidence": evidence_lines
    }


# -----------------------------------
# Load all data
# -----------------------------------
knowledge_files = load_knowledge_files(KNOWLEDGE_FOLDER)

all_sections = []
for file_name, content in knowledge_files.items():
    all_sections.extend(split_into_sections(content, file_name))

# -----------------------------------
# Sidebar
# -----------------------------------
st.sidebar.header("Knowledge Base")
selected_file = st.sidebar.selectbox(
    "Select a file to view",
    ["None"] + list(knowledge_files.keys())
)

if selected_file != "None":
    st.subheader(f"Viewing: {selected_file}")
    st.markdown(knowledge_files[selected_file])

# -----------------------------------
# Sample prompt buttons
# -----------------------------------
st.markdown("---")
st.subheader("Try these sample questions")

col1, col2 = st.columns(2)

with col1:
    if st.button("Tell me about Atharva"):
        st.session_state["sample_question"] = "Tell me about Atharva"

    if st.button("What are Atharva's skills?"):
        st.session_state["sample_question"] = "What are Atharva's skills?"

    if st.button("What are Atharva's technical skills?"):
        st.session_state["sample_question"] = "What are Atharva's technical skills?"

with col2:
    if st.button("What projects has Atharva worked on?"):
        st.session_state["sample_question"] = "What projects has Atharva worked on?"

    if st.button("Does Atharva know Azure and Databricks?"):
        st.session_state["sample_question"] = "Does Atharva know Azure and Databricks?"

    if st.button("Show Atharva's experience"):
        st.session_state["sample_question"] = "Show Atharva's experience"

default_question = st.session_state.get("sample_question", "")
question = st.text_input("Ask your question here", value=default_question)

# -----------------------------------
# Answer block
# -----------------------------------
if question:
    intent_name, intent_config = detect_intent(question)

    matches = search_sections(
        question=question,
        all_sections=all_sections,
        preferred_files=intent_config["preferred_files"],
        intent_name=intent_name,
        top_n=5
    )

    answer = build_answer(question, intent_name, intent_config, matches)

    st.markdown("## Answer")
    st.success(answer["summary"])

    if answer["evidence"]:
        st.markdown("### Key Supporting Points")
        for line in answer["evidence"]:
            st.markdown(f"- {line}")

    if matches:
        st.markdown("### Source Sections Used")
        for score, section in matches[:3]:
            with st.expander(f"{section['title']} | Source: {section['file']} | Score: {score}"):
                st.markdown(section["content"])