import json
from pathlib import Path

import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Specialists",
    page_icon="🤖",
    layout="wide",
)


# =========================================================
# LOAD CSS
# =========================================================

STYLE_PATH = Path("assets/style.css")

if STYLE_PATH.exists():
    with STYLE_PATH.open("r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# =========================================================
# LOAD DATA
# =========================================================

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


# =========================================================
# SPECIALIST CONFIG
# =========================================================

SPECIALISTS = {
    "Atlas": {
        "role": "Regenerative Medicine",
        "specialty_key": "regenerative_medicine",
        "icon": "🌱",
        "description": (
            "Reviews PRP, BMAC, mesenchymal-cell therapies, "
            "exosomes, shockwave, and regenerative interventions."
        ),
        "css_class": "atlas",
    },

    "Vector": {
        "role": "Sports Performance",
        "specialty_key": "sports_performance",
        "icon": "⚡",
        "description": (
            "Reviews sprinting, strength, power, training adaptation, "
            "fatigue, recovery, and performance outcomes."
        ),
        "css_class": "vector",
    },

    "Newton": {
        "role": "Biomechanics",
        "specialty_key": "biomechanics",
        "icon": "⚙️",
        "description": (
            "Reviews kinetics, kinematics, force production, movement "
            "mechanics, stiffness, and measurement systems."
        ),
        "css_class": "newton",
    },

    "Athena": {
        "role": "Women's Athlete Health",
        "specialty_key": "womens_athlete_health",
        "icon": "♡",
        "description": (
            "Reviews RED-S, menstrual health, bone health, hormones, "
            "female injury risk, and sex-specific evidence."
        ),
        "css_class": "athena",
    },

    "Euler": {
        "role": "Statistical Review",
        "specialty_key": None,
        "icon": "Σ",
        "description": (
            "Reviews statistical reporting, precision, effect estimates, "
            "confidence intervals, and methodological rigor."
        ),
        "css_class": "euler",
    },

    "Artemis": {
        "role": "Journal Club",
        "specialty_key": None,
        "icon": "📚",
        "description": (
            "Ranks the most important new papers, surfaces controversies, "
            "and builds discussion questions."
        ),
        "css_class": "artemis",
    },
}


# =========================================================
# HELPERS
# =========================================================

def get_specialty_review(record, specialty_key):
    specialties = record.get(
        "specialties",
        {},
    )

    if not isinstance(
        specialties,
        dict,
    ):
        return {}

    review = specialties.get(
        specialty_key,
        {},
    )

    if not isinstance(
        review,
        dict,
    ):
        return {}

    return review


def count_specialty_papers(specialty_key):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:
        review = get_specialty_review(
            record,
            specialty_key,
        )

        if review.get(
            "relevant",
            False,
        ):
            count += 1

    return count


def count_moderate_plus_confidence(
    specialty_key,
):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:
        review = get_specialty_review(
            record,
            specialty_key,
        )

        if review.get(
            "specialist_confidence"
        ) in {
            "High",
            "Moderate",
        }:
            count += 1

    return count


def count_euler_papers():
    count = 0

    for record in evidence_db:
        statistics = record.get(
            "statistics",
            {},
        )

        if (
            isinstance(
                statistics,
                dict,
            )
            and statistics
        ):
            count += 1

    return count


def count_euler_high_confidence():
    count = 0

    for record in evidence_db:
        statistics = record.get(
            "statistics",
            {},
        )

        if not isinstance(
            statistics,
            dict,
        ):
            continue

        if statistics.get(
            "statistical_confidence"
        ) == "High":
            count += 1

    return count


def get_artemis_metrics():
    summary = journal_club.get(
        "executive_summary",
        {},
    )

    if not isinstance(
        summary,
        dict,
    ):
        summary = {}

    relevant = summary.get(
        "high_priority_papers",
        0,
    )

    higher_confidence = summary.get(
        "practice_informing_papers",
        0,
    )

    return (
        relevant,
        higher_confidence,
    )


def get_specialist_metrics(name):
    config = SPECIALISTS[name]
    specialty_key = config[
        "specialty_key"
    ]

    if specialty_key:
        return (
            count_specialty_papers(
                specialty_key
            ),
            count_moderate_plus_confidence(
                specialty_key
            ),
        )

    if name == "Euler":
        return (
            count_euler_papers(),
            count_euler_high_confidence(),
        )

    if name == "Artemis":
        return get_artemis_metrics()

    return 0, 0


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="team-eyebrow">
        YOUR RESEARCH TEAM
    </div>

    <div class="team-title">
        Meet your <span style="color:#16b7a4;">AI specialists</span>
    </div>

    <div class="team-subtitle">
        Each specialist reviews the evidence through a different lens.
        Together, they help turn research into clinical intelligence.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SPECIALIST OVERVIEW CARDS
# =========================================================

rows = [
    ("Atlas", "Vector", "Newton"),
    ("Athena", "Euler", "Artemis"),
]

for row in rows:

    cols = st.columns(
        3,
        gap="large",
    )

    for col, name in zip(
        cols,
        row,
    ):

        config = SPECIALISTS[
            name
        ]

        paper_count, confidence_count = (
            get_specialist_metrics(
                name
            )
        )

        with col:

            card_html = f"""
            <div class="ai-agent-card {config['css_class']}">

                <div class="ai-agent-top">

                    <div class="ai-agent-avatar">
                        {config["icon"]}
                    </div>

                    <div class="ai-agent-heading">

                        <div class="ai-agent-name">
                            {name}
                            <span class="status-dot"></span>
                        </div>

                        <div class="ai-agent-role">
                            {config["role"]}
                        </div>

                    </div>

                </div>

                <div class="ai-agent-description">
                    {config["description"]}
                </div>

                <div class="ai-agent-divider"></div>

                <div class="ai-agent-stats">

                    <div class="ai-agent-stat">

                        <div class="ai-agent-number">
                            {paper_count}
                        </div>

                        <div class="ai-agent-small">
                            Relevant papers
                        </div>

                    </div>

                    <div class="ai-agent-stat">

                        <div class="ai-agent-number">
                            {confidence_count}
                        </div>

                        <div class="ai-agent-small">
                            Moderate+ confidence
                        </div>

                    </div>

                </div>

            </div>
            """

            st.markdown(
                card_html,
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


# =========================================================
# SELECTED SPECIALIST WORKSPACE
# =========================================================

selected_specialist = (
    st.session_state.get(
        "selected_specialist"
    )
)

if selected_specialist:

    if selected_specialist not in SPECIALISTS:
        selected_specialist = None


if selected_specialist:

    st.markdown(
        "<div class='vertical-gap'></div>",
        unsafe_allow_html=True,
    )

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

    st.caption(
        config[
            "description"
        ]
    )

    if st.button(
        "Close workspace",
        key="close_specialist_workspace",
    ):
        st.session_state.pop(
            "selected_specialist",
            None,
        )

        st.rerun()

    specialty_key = config[
        "specialty_key"
    ]


    # =====================================================
    # ATLAS / VECTOR / NEWTON / ATHENA
    # =====================================================

    if specialty_key:

        reviewed_records = []

        for record in evidence_db:

            review = get_specialty_review(
                record,
                specialty_key,
            )

            if review.get(
                "relevant",
                False,
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
            ) == "High"
        )

        moderate_confidence = sum(
            1
            for _, review
            in reviewed_records
            if review.get(
                "specialist_confidence"
            ) == "Moderate"
        )

        flagged = sum(
            1
            for _, review
            in reviewed_records
            if review.get(
                "domain_flags"
            )
        )

        st.markdown(
            "<div class='vertical-gap-small'></div>",
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = (
            st.columns(4)
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

            sorted_reviews = sorted(
                reviewed_records,
                key=lambda item: item[
                    1
                ].get(
                    "domain_score",
                    0,
                ),
                reverse=True,
            )

            top_record, top_review = (
                sorted_reviews[0]
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
                    "This specialist has reviewed relevant papers, "
                    "but no synthesized takeaway is currently available."
                )

        else:
            st.info(
                "No papers are currently routed to this specialty."
            )

        st.markdown(
            "### Recent specialist reviews"
        )

        if not reviewed_records:

            st.caption(
                "No reviews to display yet."
            )

        else:

            sorted_reviews = sorted(
                reviewed_records,
                key=lambda item: item[
                    1
                ].get(
                    "domain_score",
                    0,
                ),
                reverse=True,
            )

            for record, review in (
                sorted_reviews[:10]
            ):

                metadata = record.get(
                    "metadata",
                    {},
                )

                if not isinstance(
                    metadata,
                    dict,
                ):
                    metadata = {}

                title = metadata.get(
                    "title",
                    "Untitled paper",
                )

                with st.expander(
                    title
                ):

                    confidence = (
                        review.get(
                            "specialist_confidence",
                            "Unknown",
                        )
                    )

                    score = (
                        review.get(
                            "domain_score",
                            0,
                        )
                    )

                    c1, c2 = (
                        st.columns(2)
                    )

                    c1.metric(
                        "Domain Score",
                        score,
                    )

                    c2.metric(
                        "Confidence",
                        confidence,
                    )

                    takeaway = (
                        review.get(
                            "specialist_takeaway",
                            "",
                        )
                    )

                    if takeaway:

                        st.markdown(
                            "**Specialist takeaway**"
                        )

                        st.write(
                            takeaway
                        )

                    flags = (
                        review.get(
                            "domain_flags",
                            [],
                        )
                    )

                    if isinstance(
                        flags,
                        list,
                    ) and flags:

                        st.markdown(
                            "**What I'm cautious about**"
                        )

                        for flag in flags:
                            st.write(
                                f"• {flag}"
                            )

                    metadata_left, metadata_right = (
                        st.columns(2)
                    )

                    year = metadata.get(
                        "publication_year",
                        metadata.get(
                            "year",
                            "",
                        ),
                    )

                    journal = metadata.get(
                        "journal",
                        "",
                    )

                    if year:
                        metadata_left.caption(
                            f"Year: {year}"
                        )

                    if journal:
                        metadata_right.caption(
                            f"Journal: {journal}"
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


    # =====================================================
    # EULER
    # =====================================================

    elif (
        selected_specialist
        == "Euler"
    ):

        reviewed = []

        for record in evidence_db:

            statistics = record.get(
                "statistics",
                {},
            )

            if (
                isinstance(
                    statistics,
                    dict,
                )
                and statistics
            ):
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
            ) == "High"
        )

        flagged = sum(
            1
            for _, stats
            in reviewed
            if stats.get(
                "reporting_flags"
            )
        )

        st.markdown(
            "<div class='vertical-gap-small'></div>",
            unsafe_allow_html=True,
        )

        m1, m2, m3 = (
            st.columns(3)
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

        if not reviewed:

            st.info(
                "Euler has not reviewed any papers yet."
            )

        else:

            shown = 0

            for record, stats in (
                reviewed
            ):

                flags = stats.get(
                    "reporting_flags",
                    [],
                )

                if not flags:
                    continue

                title = (
                    record.get(
                        "metadata",
                        {},
                    ).get(
                        "title",
                        "Untitled paper",
                    )
                )

                with st.expander(
                    title
                ):

                    review_summary = (
                        stats.get(
                            "review_summary",
                            "",
                        )
                    )

                    if review_summary:
                        st.write(
                            review_summary
                        )

                    statistical_confidence = (
                        stats.get(
                            "statistical_confidence",
                            "Unknown",
                        )
                    )

                    scores = stats.get(
                        "scores",
                        {},
                    )

                    if not isinstance(
                        scores,
                        dict,
                    ):
                        scores = {}

                    c1, c2 = (
                        st.columns(2)
                    )

                    c1.metric(
                        "Confidence",
                        statistical_confidence,
                    )

                    c2.metric(
                        "Statistics Score",
                        scores.get(
                            "overall_statistics",
                            0,
                        ),
                    )

                    st.markdown(
                        "**Reporting flags**"
                    )

                    for flag in flags:
                        st.write(
                            f"• {flag}"
                        )

                shown += 1

                if shown >= 10:
                    break

            if shown == 0:
                st.success(
                    "Euler has not identified reporting flags "
                    "in the currently reviewed papers."
                )


    # =====================================================
    # ARTEMIS
    # =====================================================

    elif (
        selected_specialist
        == "Artemis"
    ):

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

        if not isinstance(
            summary,
            dict,
        ):
            summary = {}

        st.markdown(
            "<div class='vertical-gap-small'></div>",
            unsafe_allow_html=True,
        )

        m1, m2, m3 = (
            st.columns(3)
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

        if (
            isinstance(
                paper_of_week,
                dict,
            )
            and paper_of_week
        ):

            st.markdown(
                f"## {paper_of_week.get('title', 'Paper of the Week')}"
            )

            study_design = (
                paper_of_week.get(
                    "study_design",
                    "",
                )
            )

            if study_design:
                st.caption(
                    study_design
                )

            takeaway = (
                paper_of_week.get(
                    "practitioner_takeaway",
                    "",
                )
            )

            if takeaway:
                st.write(
                    takeaway
                )

            paper_url = (
                paper_of_week.get(
                    "pubmed_url",
                    "",
                )
            )

            if paper_url:
                st.link_button(
                    "Open Paper",
                    paper_url,
                )

        else:

            st.info(
                "Paper of the Week will appear after the pipeline runs."
            )

        st.markdown(
            "### Discussion prompts"
        )

        questions = (
            journal_club.get(
                "discussion_questions",
                [],
            )
        )

        if (
            isinstance(
                questions,
                list,
            )
            and questions
        ):

            for question in questions:

                st.markdown(
                    f"""
                    <div class="journal-question-card">
                        {question}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:

            st.caption(
                "No discussion prompts are currently available."
            )
