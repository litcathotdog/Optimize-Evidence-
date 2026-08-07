import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Journal Club",
    page_icon="📚",
    layout="wide",
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
# Load data
# ---------------------------------------------------------

def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


journal_club = load_json(
    "data/journal_club.json",
    {},
)

evidence_db = load_json(
    "data/evidence_database.json",
    [],
)

knowledge_graph = load_json(
    "data/knowledge_graph.json",
    {},
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def safe_dict(value):
    return value if isinstance(value, dict) else {}


def safe_list(value):
    return value if isinstance(value, list) else []


def display_name(specialty):
    names = {
        "regenerative_medicine": "Atlas",
        "sports_performance": "Vector",
        "biomechanics": "Newton",
        "womens_athlete_health": "Athena",
    }

    return names.get(
        specialty,
        specialty.replace("_", " ").title(),
    )


def specialist_icon(name):
    icons = {
        "Atlas": "🌱",
        "Vector": "⚡",
        "Newton": "⚙️",
        "Athena": "♡",
        "Euler": "Σ",
        "Artemis": "📚",
    }

    return icons.get(name, "✦")


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        WEEKLY RESEARCH MEETING
    </div>

    <h1 class="hero-title">
        Journal <span>Club</span>
    </h1>

    <p class="hero-subtitle">
        The papers, clinical problems, controversies, and evidence gaps
        your research team thinks are worth discussing.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Executive summary
# ---------------------------------------------------------

summary = safe_dict(
    journal_club.get(
        "executive_summary"
    )
)

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(
    "Papers Reviewed",
    summary.get(
        "papers_reviewed",
        len(evidence_db),
    ),
)

m2.metric(
    "High Priority",
    summary.get(
        "high_priority_papers",
        0,
    ),
)

m3.metric(
    "Practice-Informing",
    summary.get(
        "practice_informing_papers",
        0,
    ),
)

m4.metric(
    "Controversies",
    summary.get(
        "conflicting_evidence_topics",
        0,
    ),
)

m5.metric(
    "Evidence Gaps",
    summary.get(
        "evidence_gaps_highlighted",
        0,
    ),
)


# ---------------------------------------------------------
# Paper of the Week
# ---------------------------------------------------------

st.markdown("## 🏆 Paper of the Week")

paper_of_week = safe_dict(
    journal_club.get(
        "paper_of_the_week"
    )
)

if paper_of_week:

    with st.container(border=True):

        st.caption(
            " · ".join(
                value
                for value in [
                    paper_of_week.get(
                        "clinical_area",
                        "",
                    ),
                    paper_of_week.get(
                        "study_design",
                        "",
                    ),
                    paper_of_week.get(
                        "journal",
                        "",
                    ),
                ]
                if value
            )
        )

        st.markdown(
            f"## {paper_of_week.get('title', 'Untitled paper')}"
        )

        score_cols = st.columns(4)

        score_cols[0].metric(
            "Evidence",
            paper_of_week.get(
                "evidence_score",
                0,
            ),
        )

        score_cols[1].metric(
            "Statistics",
            paper_of_week.get(
                "statistics_score",
                0,
            ),
        )

        score_cols[2].metric(
            "Relevance",
            paper_of_week.get(
                "practitioner_relevance",
                0,
            ),
        )

        score_cols[3].metric(
            "Priority",
            paper_of_week.get(
                "journal_club_priority",
                0,
            ),
        )

        takeaway = paper_of_week.get(
            "practitioner_takeaway",
            "",
        )

        if takeaway:
            st.markdown(
                "### Why it matters"
            )

            st.write(
                takeaway
            )

        why_selected = safe_list(
            paper_of_week.get(
                "why_selected"
            )
        )

        if why_selected:

            st.markdown(
                "### Why Artemis selected it"
            )

            for reason in why_selected:
                st.write(
                    f"• {reason}"
                )

        cautions = safe_list(
            paper_of_week.get(
                "major_cautions"
            )
        )

        if cautions:

            with st.expander(
                "What to be cautious about"
            ):
                for caution in cautions:
                    st.write(
                        f"• {caution}"
                    )

        pubmed_url = paper_of_week.get(
            "pubmed_url",
            "",
        )

        if pubmed_url:
            st.link_button(
                "Open in PubMed ↗",
                pubmed_url,
            )

else:

    st.info(
        "Paper of the Week will appear after your pipeline generates the Journal Club."
    )


# ---------------------------------------------------------
# Weekly story
# ---------------------------------------------------------

st.markdown(
    "## This Week's Research Story"
)

top_papers = safe_list(
    journal_club.get(
        "top_papers"
    )
)

practice_papers = safe_list(
    journal_club.get(
        "practice_informing_papers"
    )
)

conflicts = safe_list(
    journal_club.get(
        "conflicting_evidence"
    )
)

gaps = safe_list(
    journal_club.get(
        "evidence_gaps"
    )
)

story_parts = []

if top_papers:
    story_parts.append(
        f"{len(top_papers)} papers rose to the top of this week's evidence review."
    )

if practice_papers:
    story_parts.append(
        f"{len(practice_papers)} were classified as potentially practice-informing."
    )

if conflicts:
    story_parts.append(
        f"The team identified {len(conflicts)} areas where published findings point in different directions."
    )

if gaps:
    story_parts.append(
        f"{len(gaps)} important evidence gaps remain unresolved."
    )

if story_parts:

    st.markdown(
        f"""
        <div class="journal-story-card">
            {" ".join(story_parts)}
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.info(
        "The weekly research story will populate after the pipeline has enough evidence to summarize."
    )


# ---------------------------------------------------------
# AI Team Discussion
# ---------------------------------------------------------

st.markdown(
    "## AI Team Discussion"
)

specialty_highlights = safe_dict(
    journal_club.get(
        "specialty_highlights"
    )
)

discussion_cards = []

for specialty, papers in specialty_highlights.items():

    papers = safe_list(papers)

    if not papers:
        continue

    top = safe_dict(
        papers[0]
    )

    name = display_name(
        specialty
    )

    takeaway = top.get(
        "specialist_takeaway",
        "",
    )

    if takeaway:

        discussion_cards.append(
            (
                name,
                takeaway,
            )
        )


# Add Euler
statistics_flags = []

for record in evidence_db:

    stats = safe_dict(
        record.get(
            "statistics"
        )
    )

    flags = safe_list(
        stats.get(
            "reporting_flags"
        )
    )

    statistics_flags.extend(
        flags
    )


if statistics_flags:

    discussion_cards.append(
        (
            "Euler",
            (
                f"I flagged statistical-reporting concerns across "
                f"{len(statistics_flags)} instances. "
                f"One recurring concern is: {statistics_flags[0]}"
            ),
        )
    )


# Add Artemis
if paper_of_week:

    discussion_cards.append(
        (
            "Artemis",
            (
                "I prioritized this week's papers based on evidence quality, "
                "statistical rigor, practitioner relevance, and potential "
                "clinical importance."
            ),
        )
    )


if discussion_cards:

    for i in range(
        0,
        len(discussion_cards),
        3,
    ):

        cols = st.columns(3)

        for col, item in zip(
            cols,
            discussion_cards[
                i : i + 3
            ],
        ):

            name, message = item

            with col:

                st.markdown(
                    f"""
                    <div class="journal-agent-card">

                        <div class="journal-agent-header">

                            <div class="journal-agent-avatar">
                                {specialist_icon(name)}
                            </div>

                            <div>
                                <div class="journal-agent-name">
                                    {name}
                                </div>

                                <div class="journal-agent-label">
                                    RESEARCH TEAM
                                </div>
                            </div>

                        </div>

                        <div class="journal-agent-message">
                            “{message}”
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

else:

    st.info(
        "Specialist discussion will appear once specialty reviews are available."
    )


# ---------------------------------------------------------
# Emerging clinical problems
# ---------------------------------------------------------

st.markdown(
    "## Problems Gaining Research Attention"
)

problem_counts = {}

for record in evidence_db:

    translation = safe_dict(
        record.get(
            "clinical_translation"
        )
    )

    problem = translation.get(
        "clinical_area"
    )

    if not problem:
        continue

    problem_counts[
        problem
    ] = (
        problem_counts.get(
            problem,
            0,
        )
        + 1
    )


ranked_problems = sorted(
    problem_counts.items(),
    key=lambda item: item[1],
    reverse=True,
)


if ranked_problems:

    cols = st.columns(
        min(
            5,
            len(ranked_problems),
        )
    )

    for col, (
        problem,
        count,
    ) in zip(
        cols,
        ranked_problems[:5],
    ):

        with col:

            st.markdown(
                f"""
                <div class="journal-topic-card">

                    <div class="journal-topic-arrow">
                        ↑
                    </div>

                    <div class="journal-topic-title">
                        {problem}
                    </div>

                    <div class="journal-topic-count">
                        {count} indexed studies
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

else:

    st.info(
        "Clinical problem trends will populate after your database contains translated studies."
    )


# ---------------------------------------------------------
# Clinical pearls
# ---------------------------------------------------------

st.markdown(
    "## Clinical Pearls"
)

clinical_pearls = []

for paper in practice_papers:

    if not isinstance(
        paper,
        dict,
    ):
        continue

    takeaway = paper.get(
        "practitioner_takeaway",
        "",
    )

    if (
        takeaway
        and takeaway
        not in clinical_pearls
    ):
        clinical_pearls.append(
            takeaway
        )


if clinical_pearls:

    for pearl in clinical_pearls[:5]:

        st.success(
            pearl,
            icon="✓",
        )

else:

    st.info(
        "Clinical pearls will appear when papers reach practice-informing status."
    )


# ---------------------------------------------------------
# Current controversies
# ---------------------------------------------------------

st.markdown(
    "## Current Debates"
)

if conflicts:

    for conflict in conflicts[:8]:

        if not isinstance(
            conflict,
            dict,
        ):
            continue

        concept = conflict.get(
            "concept",
            "Unknown topic",
        )

        with st.expander(
            concept
        ):

            c1, c2, c3 = st.columns(
                3
            )

            c1.metric(
                "Favorable",
                conflict.get(
                    "favorable",
                    0,
                ),
            )

            c2.metric(
                "Neutral",
                conflict.get(
                    "neutral",
                    0,
                ),
            )

            c3.metric(
                "Unfavorable",
                conflict.get(
                    "unfavorable",
                    0,
                ),
            )

            st.write(
                conflict.get(
                    "discussion_point",
                    "",
                )
            )

else:

    st.info(
        "No multi-study evidence conflicts are currently flagged."
    )


# ---------------------------------------------------------
# Evidence gaps
# ---------------------------------------------------------

st.markdown(
    "## What We Still Don't Know"
)

if gaps:

    for gap in gaps[:8]:

        if not isinstance(
            gap,
            dict,
        ):
            continue

        concept = gap.get(
            "concept",
            "Unknown problem",
        )

        reasons = safe_list(
            gap.get(
                "reasons"
            )
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {concept}"
            )

            st.caption(
                f"{gap.get('paper_count', 0)} indexed studies"
            )

            for reason in reasons:
                st.write(
                    f"• {reason}"
                )

else:

    st.info(
        "No major evidence gaps are currently flagged."
    )


# ---------------------------------------------------------
# Papers worth reading
# ---------------------------------------------------------

st.markdown(
    "## Papers Worth Reading"
)

for index, paper in enumerate(
    top_papers[:10],
    start=1,
):

    if not isinstance(
        paper,
        dict,
    ):
        continue

    with st.expander(
        f"{index}. {paper.get('title', 'Untitled paper')}"
    ):

        st.caption(
            " · ".join(
                value
                for value in [
                    paper.get(
                        "clinical_area",
                        "",
                    ),
                    paper.get(
                        "study_design",
                        "",
                    ),
                    paper.get(
                        "journal",
                        "",
                    ),
                ]
                if value
            )
        )

        c1, c2, c3, c4 = st.columns(
            4
        )

        c1.metric(
            "Evidence",
            paper.get(
                "evidence_score",
                0,
            ),
        )

        c2.metric(
            "Statistics",
            paper.get(
                "statistics_score",
                0,
            ),
        )

        c3.metric(
            "Relevance",
            paper.get(
                "practitioner_relevance",
                0,
            ),
        )

        c4.metric(
            "Priority",
            paper.get(
                "journal_club_priority",
                0,
            ),
        )

        takeaway = paper.get(
            "practitioner_takeaway",
            "",
        )

        if takeaway:

            st.markdown(
                "**Why it matters**"
            )

            st.write(
                takeaway
            )

        pubmed_url = paper.get(
            "pubmed_url",
            "",
        )

        if pubmed_url:

            st.link_button(
                "Open PubMed ↗",
                pubmed_url,
            )


# ---------------------------------------------------------
# Discussion questions
# ---------------------------------------------------------

st.markdown(
    "## Questions for the Room"
)

questions = safe_list(
    journal_club.get(
        "discussion_questions"
    )
)

if questions:

    for number, question in enumerate(
        questions,
        start=1,
    ):

        st.markdown(
            f"""
            <div class="journal-question">
                <span>{number:02d}</span>
                {question}
            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.info(
        "Discussion questions will appear after the Journal Club Editor runs."
    )
