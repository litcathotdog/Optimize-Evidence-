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

clinical_problems = st.Page(
    "pages/clinical_problems.py",
    title="Clinical Problems",
    icon=":material/clinical_notes:",
    default=True,
)

problem_detail = st.Page(
    "pages/problem_detail.py",
    title="Problem Detail",
    icon=":material/article:",
    visibility="hidden",
)

ai_specialists = st.Page(
    "pages/ai_specialists.py",
    title="AI Specialists",
    icon=":material/groups:",
)

evidence_library = st.Page(
    "pages/evidence_library.py",
    title="Evidence Library",
    icon=":material/library_books:",
)

journal_club = st.Page(
    "pages/journal_club.py",
    title="Journal Club",
    icon=":material/menu_book:",
)

knowledge_graph = st.Page(
    "pages/knowledge_graph.py",
    title="Knowledge Graph",
    icon=":material/hub:",
)

evidence_gaps = st.Page(
    "pages/evidence_gaps.py",
    title="Evidence Gaps",
    icon=":material/warning:",
)

statistics_review = st.Page(
    "pages/statistics_review.py",
    title="Statistics Review",
    icon=":material/analytics:",
)

ask_athena = st.Page(
    "pages/ask_athena.py",
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

            <div class="brand-mark">
                🧠
            </div>

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

page = st.navigation(
    {
        "Evidence Intelligence": [
            clinical_problems,
            ai_specialists,
            evidence_library,
            journal_club,
            knowledge_graph,
            evidence_gaps,
            statistics_review,
        ],

        "Research Assistant": [
            ask_athena,
        ],

        # Hidden but still routable
        "_hidden": [
            problem_detail,
        ],
    },
    position="sidebar",
)


# =========================================================
# RUN SELECTED PAGE
# =========================================================

page.run()
