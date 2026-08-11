import streamlit as st


# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Optimize Evidence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# PAGE DEFINITIONS
# =========================================================

home = st.Page(
    "pages/home.py",
    title="Home",
    icon=":material/home:",
    default=True,
)

clinical_problems = st.Page(
    "pages/1_Clinical_Problems.py",
    title="Clinical Problems",
)

problem_detail = st.Page(
    "pages/2_Problem_Detail.py",
    title="Problem Detail",
    icon=":material/article:",
)

ai_specialists = st.Page(
    "pages/3_AI_Specialists.py",
    title="AI Specialists",
    icon=":material/groups:",
)

evidence_library = st.Page(
    "pages/4_Evidence_Library.py",
    title="Evidence Library",
    icon=":material/library_books:",
)

journal_club = st.Page(
    "pages/5_Journal_Club.py",
    title="Journal Club",
    icon=":material/menu_book:",
)

knowledge_graph = st.Page(
    "pages/6_Knowledge_Graph.py",
    title="Knowledge Graph",
    icon=":material/hub:",
)

evidence_gaps = st.Page(
    "pages/7_Evidence_Gaps.py",
    title="Evidence Gaps",
    icon=":material/search_off:",
)

statistics_review = st.Page(
    "pages/8_Statistics_Review.py",
    title="Statistics Review",
    icon=":material/analytics:",
)

ask_athena = st.Page(
    "pages/9_Ask_Athena.py",
    title="Ask Athena",
    icon=":material/auto_awesome:",
)


# =========================================================
# NAVIGATION
# =========================================================

navigation = st.navigation(
    {
        "Optimize Evidence": [
            home,
            clinical_problems,
            problem_detail,
            ai_specialists,
            evidence_library,
            journal_club,
            knowledge_graph,
            evidence_gaps,
            statistics_review,
            ask_athena,
        ]
    }
)


# =========================================================
# RUN SELECTED PAGE
# =========================================================

navigation.run()
