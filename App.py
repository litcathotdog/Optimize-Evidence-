from pathlib import Path

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
# LOAD GLOBAL CSS
# =========================================================

STYLE_PATH = Path("assets/style.css")

if STYLE_PATH.exists():
    with STYLE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# =========================================================
# DEFINE PAGES
# =========================================================

home = st.Page(
    "pages/1_Home.py",
    title="Home",
    icon=":material/home:",
    default=True,
)

clinical_problems = st.Page(
    "pages/2_Clinical_Problems.py",
    title="Clinical Problems",
    icon=":material/clinical_notes:",
)

problem_detail = st.Page(
    "pages/3_Problem_Detail.py",
    title="Problem Detail",
    icon=":material/article:",
    visibility="hidden",
)

ai_specialists = st.Page(
    "pages/4_AI_Specialists.py",
    title="AI Specialists",
    icon=":material/groups:",
)

evidence_library = st.Page(
    "pages/5_Evidence_Library.py",
    title="Evidence Library",
    icon=":material/library_books:",
)

journal_club = st.Page(
    "pages/6_Journal_Club.py",
    title="Journal Club",
    icon=":material/menu_book:",
)

knowledge_graph = st.Page(
    "pages/7_Knowledge_Graph.py",
    title="Knowledge Graph",
    icon=":material/hub:",
)

evidence_gaps = st.Page(
    "pages/8_Evidence_Gaps.py",
    title="Evidence Gaps",
    icon=":material/warning:",
)

statistics_review = st.Page(
    "pages/9_Statistics_Review.py",
    title="Statistics Review",
    icon=":material/analytics:",
)

ask_athena = st.Page(
    "pages/10_Ask_Athena.py",
    title="Ask Athena",
    icon=":material/auto_awesome:",
)


# =========================================================
# SIDEBAR BRAND
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">🧠</div>

            <div>
                <div class="brand-title">
                    OPTIMIZE
                </div>

                <div class="brand-title">
                    EVIDENCE
                </div>

                <div class="brand-subtitle">
                    Better evidence.<br>
                    Better outcomes.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# NAVIGATION
# =========================================================

navigation = st.navigation(
    {
        "": [
            home,
            clinical_problems,
            ai_specialists,
            evidence_library,
            journal_club,
            knowledge_graph,
            evidence_gaps,
            statistics_review,
        ],

        "AI": [
            ask_athena,
        ],
    }
)


# =========================================================
# RUN CURRENT PAGE
# =========================================================

navigation.run()
