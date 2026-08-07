import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="AI Specialists",
    page_icon="🤖",
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


evidence_db = load_json(
    "data/evidence_database.json",
    [],
)

journal_club = load_json(
    "data/journal_club.json",
    {},
)


# ---------------------------------------------------------
# Specialist config
# ---------------------------------------------------------

SPECIALISTS = {
    "Atlas": {
        "role": "Regenerative Medicine",
        "specialty_key": "regenerative_medicine",
        "icon": "🌱",
        "description": (
            "Reviews PRP, BMAC, mesenchymal-cell therapies, "
            "exosomes, shockwave, and regenerative interventions."
        ),
    },

    "Vector": {
        "role": "Sports Performance",
        "specialty_key": "sports_performance",
        "icon": "⚡",
        "description": (
            "Reviews sprinting, strength, power, training adaptation, "
            "fatigue, recovery, and performance outcomes."
        ),
    },

    "Newton": {
        "role": "Biomechanics",
        "specialty_key": "biomechanics",
        "icon": "⚙️",
        "description": (
            "Reviews kinetics, kinematics, force production, movement "
            "mechanics, stiffness, and measurement systems."
        ),
    },

    "Athena": {
        "role": "Women's Athlete Health",
        "specialty_key": "womens_athlete_health",
        "icon": "♡",
        "description": (
            "Reviews RED-S, menstrual health, bone health, hormones, "
            "female injury risk, and sex-specific evidence."
        ),
    },

    "Euler": {
        "role": "Statistical Review",
        "specialty_key": None,
        "icon": "Σ",
        "description": (
            "Reviews statistical reporting, precision, effect estimates, "
            "confidence intervals, and methodological rigor."
        ),
    },

    "Artemis": {
        "role": "Journal Club",
        "specialty_key": None,
        "icon": "📚",
        "description": (
            "Ranks the most important new papers, surfaces controversies, "
            "and builds discussion questions."
        ),
    },
}


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        YOUR RESEARCH TEAM
    </div>

    <h1 class="hero-title">
        Meet your <span>AI specialists</span>
    </h1>

    <p class="hero-subtitle">
        Each specialist reviews the evidence through a different lens.
        Together, they help turn research into clinical intelligence.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Specialist overview cards
# ---------------------------------------------------------

def count_specialty_papers(specialty_key):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:
        specialties = record.get(
            "specialties",
            {},
        )

        if not isinstance(
            specialties,
            dict,
        ):
            continue

        review = specialties.get(
            specialty_key,
            {},
        )

        if (
            isinstance(
                review,
                dict,
            )
            and review.get(
                "relevant",
                False,
            )
        ):
            count += 1

    return count


def count_high_confidence(specialty_key):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:
        specialties = record.get(
            "specialties",
            {},
        )

        if not isinstance(
            specialties,
            dict,
        ):
            continue

        review = specialties.get(
            specialty_key,
            {},
        )

        if not isinstance(
            review,
            dict,
        ):
            continue

        if review.get(
            "specialist_confidence"
        ) in {
            "High",
            "Moderate",
        }:
            count += 1

    return count


rows = [
    ("Atlas", "Vector", "Newton"),
    ("Athena", "Euler", "Artemis"),
]


for row in rows:
    cols = st.columns(3)

    for col, name in zip(
        cols,
        row,
    ):
        config = SPECIALISTS[
            name
        ]

        specialty_key = config[
            "specialty_key"
        ]

        paper_count = (
            count_specialty_papers(
                specialty_key
            )
            if specialty_key
            else 0
        )

        confidence_count = (
            count_high_confidence(
                specialty_key
            )
            if specialty_key
            else 0
        )

        with col:
            st.markdown(
                f"""
                <div class="ai-agent-card">

                    <div class="ai-agent-top">

                        <div class="ai-agent-avatar">
                            {config["icon"]}
                        </div>

                        <div>
                            <div class="ai-agent-name">
                                {name}
                            </div>

                            <div class="ai-agent-role">
                                {config["role"]}
                            </div>
                        </div>

                    </div>

                    <div class="ai-agent-description">
                        {config["description"]}
                    </div>

                    <div class="ai-agent-stats">

                        <div>
                            <div class="ai-agent-number">
                                {paper_count}
                            </div>

                            <div class="ai-agent-small">
                                Relevant papers
                            </div>
                        </div>

                        <div>
                            <div class="ai-agent-number">
                                {confidence_count}
                            </div>

                            <div class="ai-agent-small">
                                Higher confidence
                            </div>
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Open {name}'s workspace →",
                key=f"open_{name}",
                use_container_width=True,
            ):
                st.session_state[
                    "selected_specialist"
                ] = name

                st.rerun()


# ---------------------------------------------------------
# Workspace
# ---------------------------------------------------------

selected_specialist = st.session_state.get(
    "selected_specialist"
)

if selected_specialist:

    st.divider()

    config = SPECIALISTS[
        selected_specialist
    ]

    st.markdown(
        f"""
        <div class="specialist-workspace-header">

            <div class="specialist-workspace-avatar">
                {config["icon"]}
            </div>

            <div>
                <div class="specialist-workspace-name">
                    {selected_specialist}
                </div>

                <div class="specialist-workspace-role">
                    {config["role"]}
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    specialty_key = config[
        "specialty_key"
    ]


    # -----------------------------------------------------
    # Atlas / Vector / Newton / Athena
    # -----------------------------------------------------

    if specialty_key:

        reviewed_records = []

        for record in evidence_db:

            specialties = record.get(
                "specialties",
                {},
            )

            if not isinstance(
                specialties,
                dict,
            ):
                continue

            review = specialties.get(
                specialty_key,
                {},
            )

            if (
                isinstance(
                    review,
                    dict,
                )
                and review.get(
                    "relevant",
                    False,
                )
            ):
                reviewed_records.append(
                    (
                        record,
                        review,
                    )
                )


        reviewed_count = len(
            reviewed_records
        )

        high_confidence = sum(
            1
            for _, review
            in reviewed_records
            if review.get(
                "specialist_confidence"
            )
            == "High"
        )

        moderate_confidence = sum(
            1
            for _, review
            in reviewed_records
            if review.get(
                "specialist_confidence"
            )
            == "Moderate"
        )

        flagged = sum(
            1
            for _, review
            in reviewed_records
            if review.get(
                "domain_flags"
            )
        )


        m1, m2, m3, m4 = st.columns(
            4
        )

        m1.metric(
            "Relevant Papers",
            reviewed_count,
        )

        m2.metric(
            "High Confidence",
            high_confidence,
        )

        m3.metric(
            "Moderate Confidence",
            moderate_confidence,
        )

        m4.metric(
            "Flagged Papers",
            flagged,
        )


        st.markdown(
            "### What I'm seeing"
        )

        if reviewed_records:

            top_record, top_review = (
                reviewed_records[0]
            )

            takeaway = top_review.get(
                "specialist_takeaway",
                "",
            )

            if takeaway:
                st.info(
                    takeaway
                )

        else:
            st.info(
                "No papers are currently routed to this specialty."
            )


        st.markdown(
            "### Recent specialist reviews"
        )

        for record, review in (
            reviewed_records[:10]
        ):

            metadata = record.get(
                "metadata",
                {},
            )

            title = metadata.get(
                "title",
                "Untitled paper",
            )

            with st.expander(
                title
            ):

                confidence = review.get(
                    "specialist_confidence",
                    "Unknown",
                )

                score = review.get(
                    "domain_score",
                    0,
                )

                c1, c2 = st.columns(
                    2
                )

                c1.metric(
                    "Domain Score",
                    score,
                )

                c2.metric(
                    "Confidence",
                    confidence,
                )

                takeaway = review.get(
                    "specialist_takeaway",
                    "",
                )

                if takeaway:
                    st.write(
                        takeaway
                    )

                flags = review.get(
                    "domain_flags",
                    [],
                )

                if flags:

                    st.markdown(
                        "**What I'm cautious about**"
                    )

                    for flag in flags:
                        st.write(
                            f"• {flag}"
                        )

                pubmed_url = metadata.get(
                    "pubmed_url",
                    "",
                )

                if pubmed_url:
                    st.link_button(
                        "Open PubMed",
                        pubmed_url,
                    )


    # -----------------------------------------------------
    # Euler
    # -----------------------------------------------------

    elif selected_specialist == "Euler":

        reviewed = []

        for record in evidence_db:

            statistics = record.get(
                "statistics",
                {},
            )

            if isinstance(
                statistics,
                dict,
            ) and statistics:
                reviewed.append(
                    (
                        record,
                        statistics,
                    )
                )


        high_confidence = sum(
            1
            for _, stats
            in reviewed
            if stats.get(
                "statistical_confidence"
            )
            == "High"
        )

        flagged = sum(
            1
            for _, stats
            in reviewed
            if stats.get(
                "reporting_flags"
            )
        )


        m1, m2, m3 = st.columns(
            3
        )

        m1.metric(
            "Papers Reviewed",
            len(reviewed),
        )

        m2.metric(
            "High Confidence",
            high_confidence,
        )

        m3.metric(
            "With Statistical Flags",
            flagged,
        )


        st.markdown(
            "### Euler's concerns"
        )

        for record, stats in (
            reviewed[:10]
        ):

            flags = stats.get(
                "reporting_flags",
                [],
            )

            if not flags:
                continue

            title = record.get(
                "metadata",
                {},
            ).get(
                "title",
                "Untitled paper",
            )

            with st.expander(
                title
            ):

                st.write(
                    stats.get(
                        "review_summary",
                        "",
                    )
                )

                for flag in flags:
                    st.write(
                        f"• {flag}"
                    )


    # -----------------------------------------------------
    # Artemis
    # -----------------------------------------------------

    elif selected_specialist == "Artemis":

        paper_of_week = (
            journal_club.get(
                "paper_of_the_week",
                {},
            )
        )

        summary = (
            journal_club.get(
                "executive_summary",
                {},
            )
        )


        m1, m2, m3 = st.columns(
            3
        )

        m1.metric(
            "High Priority",
            summary.get(
                "high_priority_papers",
                0,
            ),
        )

        m2.metric(
            "Practice Informing",
            summary.get(
                "practice_informing_papers",
                0,
            ),
        )

        m3.metric(
            "Evidence Gaps",
            summary.get(
                "evidence_gaps_highlighted",
                0,
            ),
        )


        st.markdown(
            "### Artemis' Paper of the Week"
        )

        if paper_of_week:

            st.markdown(
                f"## {paper_of_week.get('title', '')}"
            )

            st.write(
                paper_of_week.get(
                    "practitioner_takeaway",
                    "",
                )
            )

        else:
            st.info(
                "Paper of the Week will appear after the pipeline runs."
            )


        st.markdown(
            "### Discussion prompts"
        )

        for question in (
            journal_club.get(
                "discussion_questions",
                [],
            )
        ):
            st.write(
                f"• {question}"
            )
