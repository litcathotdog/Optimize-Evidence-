import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Optimize Evidence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Load CSS
# ---------------------------------------------------------

STYLE_PATH = Path("assets/style.css")

if STYLE_PATH.exists():
    with STYLE_PATH.open("r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Load dashboard data
# ---------------------------------------------------------

def load_json(path):
    path = Path(path)

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


dashboard = load_json("data/dashboard.json")
journal_club = load_json("data/journal_club.json")


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-icon">🧠</div>
            <div>
                <div class="brand-name">OPTIMIZE</div>
                <div class="brand-name">EVIDENCE</div>
                <div class="brand-tagline">Better evidence.<br>Better outcomes.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "Home",
            "Clinical Problems",
            "Evidence Library",
            "AI Specialists",
            "Journal Club",
            "Knowledge Graph",
            "Evidence Gaps",
            "Statistics Review",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """
        <div class="athena-card">
            <div class="athena-title">✦ Ask Athena</div>
            <p>Ask a question or explore evidence-based insights.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

if page == "Home":

    st.markdown(
        """
        <div class="hero-eyebrow">GOOD MORNING ✦</div>
        <h1 class="hero-title">
            What <span>problems</span> are we solving today?
        </h1>
        <p class="hero-subtitle">
            AI specialists continuously review, critique, and synthesize
            evidence so you can make better clinical decisions.
        </p>
        """,
        unsafe_allow_html=True,
    )

    overview = dashboard.get("overview", {})

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "New Papers",
        overview.get("total_papers", 0),
    )

    c2.metric(
        "Practice-Informing",
        overview.get("practice_informing_papers", 0),
    )

    c3.metric(
        "Clinical Problems",
        0,
    )

    c4.metric(
        "Evidence Gaps",
        overview.get("evidence_gaps", 0),
    )

    c5.metric(
        "Avg. Confidence",
        "—",
    )

    st.markdown("## Top Clinical Problems")

    problem_cols = st.columns(5)

    demo_problems = [
        ("Patellar Tendinopathy", "143 studies", "Very strong", "91%"),
        ("Hamstring Strain", "98 studies", "Strong", "84%"),
        ("Stress Fractures", "76 studies", "Strong", "83%"),
        ("RED-S", "64 studies", "Strong", "82%"),
        ("Explosive Performance", "224 studies", "Moderate", "76%"),
    ]

    for col, problem in zip(problem_cols, demo_problems):
        name, papers, strength, confidence = problem

        with col:
            st.markdown(
                f"""
                <div class="problem-card">
                    <div class="problem-name">{name}</div>
                    <div class="problem-count">{papers}</div>
                    <div class="problem-strength">{strength}</div>
                    <div class="problem-confidence">{confidence}</div>
                    <div class="problem-link">View problem →</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("## Your AI Specialists")

    specialist_cols = st.columns(6)

    specialists = [
        ("Atlas", "Regenerative Medicine", "🌱"),
        ("Vector", "Sports Performance", "⚡"),
        ("Newton", "Biomechanics", "⚙️"),
        ("Athena", "Women's Athlete Health", "♡"),
        ("Euler", "Statistical Review", "Σ"),
        ("Artemis", "Journal Club", "📖"),
    ]

    for col, specialist in zip(
        specialist_cols,
        specialists,
    ):
        name, specialty, icon = specialist

        with col:
            st.markdown(
                f"""
                <div class="specialist-card">
                    <div class="specialist-icon">{icon}</div>
                    <div class="specialist-name">{name}</div>
                    <div class="specialist-role">{specialty}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("## Research Intelligence")

    left, middle, right = st.columns(
        [1.2, 1, 1]
    )

    with left:
        st.markdown("### Evidence Overview")
        st.line_chart(
            {
                "New papers": [
                    25,
                    38,
                    31,
                    48,
                    42,
                    55,
                    51,
                    67,
                ]
            }
        )

    with middle:
        st.markdown("### Paper of the Week")

        paper = journal_club.get(
            "paper_of_the_week",
            {},
        )

        if paper:
            st.markdown(
                f"**{paper.get('title', '')}**"
            )

            st.caption(
                paper.get(
                    "study_design",
                    "",
                )
            )

            st.write(
                paper.get(
                    "practitioner_takeaway",
                    "",
                )
            )

        else:
            st.info(
                "Paper of the Week will appear after the pipeline runs."
            )

    with right:
        st.markdown("### Top Evidence Gaps")

        gaps = dashboard.get(
            "evidence_gaps",
            [],
        )

        if gaps:
            for gap in gaps[:5]:
                st.write(
                    f"• {gap.get('concept', '')}"
                )

        else:
            st.write(
                "Evidence gaps will populate after analysis."
            )
