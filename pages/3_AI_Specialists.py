import json
from pathlib import Path

import streamlit as st


# =========================================================
# LOAD DATA
# =========================================================

def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


evidence_db = load_json(
    "data/evidence_database.json",
    [],
)

journal_club = load_json(
    "data/journal_club.json",
    {},
)


# =========================================================
# SPECIALISTS
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
            "Reviews kinetics, kinematics, force production, "
            "movement mechanics, stiffness, and measurement systems."
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


# =========================================================
# HELPERS
# =========================================================

def get_specialty_review(
    record,
    specialty_key,
):
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

    if isinstance(
        review,
        dict,
    ):
        return review

    return {}


def get_metadata(record):
    metadata = record.get(
        "metadata",
        {},
    )

    if isinstance(
        metadata,
        dict,
    ):
        return metadata

    return {}


def count_specialty_papers(
    specialty_key,
):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

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


def count_high_confidence(
    specialty_key,
):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        review = get_specialty_review(
            record,
            specialty_key,
        )

        if review.get(
            "specialist_confidence"
        ) == "High":
            count += 1

    return count


def count_moderate_confidence(
    specialty_key,
):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        review = get_specialty_review(
            record,
            specialty_key,
        )

        if review.get(
            "specialist_confidence"
        ) == "Moderate":
            count += 1

    return count


def count_flagged(
    specialty_key,
):
    if not specialty_key:
        return 0

    count = 0

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        review = get_specialty_review(
            record,
            specialty_key,
        )

        flags = review.get(
            "domain_flags",
            [],
        )

        if (
            isinstance(flags, list)
            and flags
        ):
            count += 1

    return count


def get_euler_records():
    reviewed = []

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        statistics = record.get(
            "statistics",
            {},
        )

        if (
            isinstance(statistics, dict)
            and statistics
        ):
            reviewed.append(
                (
                    record,
                    statistics,
                )
            )

    return reviewed


def get_artemis_summary():
    summary = journal_club.get(
        "executive_summary",
        {},
    )

    if isinstance(
        summary,
        dict,
    ):
        return summary

    return {}


def get_specialist_card_metrics(
    name,
):
    config = SPECIALISTS[
        name
    ]

    specialty_key = config[
        "specialty_key"
    ]

    if specialty_key:
        return (
            count_specialty_papers(
                specialty_key
            ),
            count_high_confidence(
                specialty_key
            ),
        )

    if name == "Euler":

        reviewed = get_euler_records()

        high_confidence = sum(
            1
            for _, statistics
            in reviewed
            if statistics.get(
                "statistical_confidence"
            ) == "High"
        )

        return (
            len(reviewed),
            high_confidence,
        )

    if name == "Artemis":

        summary = (
            get_artemis_summary()
        )

        return (
            summary.get(
                "high_priority_papers",
                0,
            ),
            summary.get(
                "practice_informing_papers",
                0,
            ),
        )

    return 0, 0


# =========================================================
# HEADER
# =========================================================

st.caption(
    "YOUR RESEARCH TEAM"
)

st.title(
    "Meet your AI specialists"
)

st.write(
    "Each specialist reviews the evidence through a different lens. "
    "Together, they help turn research into clinical intelligence."
)

st.write("")


# =========================================================
# SPECIALIST CARDS
# =========================================================

rows = [
    (
        "Atlas",
        "Vector",
        "Newton",
    ),
    (
        "Athena",
        "Euler",
        "Artemis",
    ),
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

        (
            relevant_papers,
            high_confidence,
        ) = get_specialist_card_metrics(
            name
        )

        with col:

            with st.container(
                border=True,
            ):

                # -----------------------------------------
                # Agent header
                # -----------------------------------------

                icon_col, name_col = (
                    st.columns(
                        [1, 3]
                    )
                )

                with icon_col:

                    st.markdown(
                        f"# {config['icon']}"
                    )

                with name_col:

                    st.markdown(
                        f"### {name}"
                    )

                    st.caption(
                        config[
                            "role"
                        ]
                    )

                # -----------------------------------------
                # Description
                # -----------------------------------------

                st.write(
                    config[
                        "description"
                    ]
                )

                st.divider()

                # -----------------------------------------
                # Metrics
                # -----------------------------------------

                metric_1, metric_2 = (
                    st.columns(2)
                )

                with metric_1:

                    st.metric(
                        "Relevant Papers",
                        relevant_papers,
                    )

                with metric_2:

                    st.metric(
                        "High Confidence",
                        high_confidence,
                    )

                # -----------------------------------------
                # Open workspace
                # -----------------------------------------

                if st.button(
                    f"Open {name}'s workspace →",
                    key=f"open_{name}",
                    width="stretch",
                ):

                    st.session_state[
                        "selected_specialist"
                    ] = name

                    st.rerun()


# =========================================================
# WORKSPACE
# =========================================================

selected_specialist = (
    st.session_state.get(
        "selected_specialist"
    )
)


if (
    selected_specialist
    and selected_specialist
    not in SPECIALISTS
):
    selected_specialist = None


if selected_specialist:

    st.write("")

    st.divider()

    config = SPECIALISTS[
        selected_specialist
    ]

    # =====================================================
    # WORKSPACE HEADER
    # =====================================================

    header_icon, header_text, close_col = (
        st.columns(
            [1, 6, 1]
        )
    )

    with header_icon:

        st.markdown(
            f"# {config['icon']}"
        )

    with header_text:

        st.subheader(
            selected_specialist
        )

        st.caption(
            config[
                "role"
            ]
        )

        st.write(
            config[
                "description"
            ]
        )

    with close_col:

        if st.button(
            "Close",
            width="stretch",
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

            if not isinstance(
                record,
                dict,
            ):
                continue

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


        reviewed_records.sort(
            key=lambda item: (
                item[1].get(
                    "domain_score",
                    0,
                )
                or 0
            ),
            reverse=True,
        )


        # -------------------------------------------------
        # Metrics
        # -------------------------------------------------

        relevant_count = len(
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


        m1, m2, m3, m4 = (
            st.columns(
                4,
                gap="medium",
            )
        )

        with m1:
            st.metric(
                "Relevant Papers",
                relevant_count,
                border=True,
            )

        with m2:
            st.metric(
                "High Confidence",
                high_confidence,
                border=True,
            )

        with m3:
            st.metric(
                "Moderate Confidence",
                moderate_confidence,
                border=True,
            )

        with m4:
            st.metric(
                "Flagged Papers",
                flagged,
                border=True,
            )


        st.write("")


        # -------------------------------------------------
        # What I'm seeing
        # -------------------------------------------------

        st.subheader(
            f"What {selected_specialist} is seeing"
        )

        if reviewed_records:

            top_record, top_review = (
                reviewed_records[0]
            )

            takeaway = (
                top_review.get(
                    "specialist_takeaway",
                    "",
                )
            )

            if takeaway:

                st.info(
                    takeaway
                )

            else:

                st.info(
                    "Relevant evidence has been identified, "
                    "but a specialist synthesis is not yet available."
                )

        else:

            st.info(
                "No papers are currently routed to this specialty."
            )


        # -------------------------------------------------
        # Recent reviews
        # -------------------------------------------------

        st.subheader(
            "Recent specialist reviews"
        )

        if not reviewed_records:

            st.caption(
                "No reviews to display."
            )

        else:

            for record, review in (
                reviewed_records[:10]
            ):

                metadata = get_metadata(
                    record
                )

                title = metadata.get(
                    "title",
                    "Untitled paper",
                )

                confidence = review.get(
                    "specialist_confidence",
                    "Unknown",
                )

                score = review.get(
                    "domain_score",
                    0,
                )

                with st.expander(
                    title
                ):

                    c1, c2 = (
                        st.columns(2)
                    )

                    with c1:

                        st.metric(
                            "Domain Score",
                            score,
                        )

                    with c2:

                        st.metric(
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

                    flags = review.get(
                        "domain_flags",
                        [],
                    )

                    if (
                        isinstance(flags, list)
                        and flags
                    ):

                        st.markdown(
                            "**What I'm cautious about**"
                        )

                        for flag in flags:

                            st.write(
                                f"• {flag}"
                            )

                    year = (
                        metadata.get(
                            "publication_year"
                        )
                        or metadata.get(
                            "year"
                        )
                    )

                    journal = metadata.get(
                        "journal"
                    )

                    source_parts = []

                    if journal:
                        source_parts.append(
                            str(journal)
                        )

                    if year:
                        source_parts.append(
                            str(year)
                        )

                    if source_parts:

                        st.caption(
                            " • ".join(
                                source_parts
                            )
                        )

                    pubmed_url = (
                        metadata.get(
                            "pubmed_url",
                            "",
                        )
                    )

                    if pubmed_url:

                        st.link_button(
                            "Open PubMed",
                            pubmed_url,
                        )


    # =====================================================
    # EULER
    # =====================================================

    elif selected_specialist == "Euler":

        reviewed = (
            get_euler_records()
        )

        high_confidence = sum(
            1
            for _, statistics
            in reviewed
            if statistics.get(
                "statistical_confidence"
            ) == "High"
        )

        moderate_confidence = sum(
            1
            for _, statistics
            in reviewed
            if statistics.get(
                "statistical_confidence"
            ) == "Moderate"
        )

        flagged = sum(
            1
            for _, statistics
            in reviewed
            if statistics.get(
                "reporting_flags"
            )
        )


        m1, m2, m3, m4 = (
            st.columns(
                4,
                gap="medium",
            )
        )

        with m1:

            st.metric(
                "Papers Reviewed",
                len(reviewed),
                border=True,
            )

        with m2:

            st.metric(
                "High Confidence",
                high_confidence,
                border=True,
            )

        with m3:

            st.metric(
                "Moderate Confidence",
                moderate_confidence,
                border=True,
            )

        with m4:

            st.metric(
                "With Flags",
                flagged,
                border=True,
            )


        st.write("")

        st.subheader(
            "Euler's statistical concerns"
        )

        shown = 0

        for record, statistics in (
            reviewed
        ):

            flags = statistics.get(
                "reporting_flags",
                [],
            )

            if not (
                isinstance(flags, list)
                and flags
            ):
                continue

            metadata = get_metadata(
                record
            )

            title = metadata.get(
                "title",
                "Untitled paper",
            )

            with st.expander(
                title
            ):

                summary = statistics.get(
                    "review_summary",
                    "",
                )

                confidence = (
                    statistics.get(
                        "statistical_confidence",
                        "Unknown",
                    )
                )

                scores = statistics.get(
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

                with c1:

                    st.metric(
                        "Statistics Score",
                        scores.get(
                            "overall_statistics",
                            0,
                        ),
                    )

                with c2:

                    st.metric(
                        "Confidence",
                        confidence,
                    )

                if summary:

                    st.write(
                        summary
                    )

                st.markdown(
                    "**Reporting flags**"
                )

                for flag in flags:

                    st.write(
                        f"• {flag}"
                    )

                pubmed_url = (
                    metadata.get(
                        "pubmed_url",
                        "",
                    )
                )

                if pubmed_url:

                    st.link_button(
                        "Open PubMed",
                        pubmed_url,
                    )

            shown += 1

            if shown >= 10:
                break


        if shown == 0:

            st.success(
                "Euler has not identified statistical reporting "
                "flags in the currently reviewed papers."
            )


    # =====================================================
    # ARTEMIS
    # =====================================================

    elif selected_specialist == "Artemis":

        summary = (
            get_artemis_summary()
        )

        paper_of_week = (
            journal_club.get(
                "paper_of_the_week",
                {},
            )
        )

        if not isinstance(
            paper_of_week,
            dict,
        ):
            paper_of_week = {}


        m1, m2, m3 = (
            st.columns(
                3,
                gap="medium",
            )
        )

        with m1:

            st.metric(
                "High Priority",
                summary.get(
                    "high_priority_papers",
                    0,
                ),
                border=True,
            )

        with m2:

            st.metric(
                "Practice Informing",
                summary.get(
                    "practice_informing_papers",
                    0,
                ),
                border=True,
            )

        with m3:

            st.metric(
                "Evidence Gaps",
                summary.get(
                    "evidence_gaps_highlighted",
                    0,
                ),
                border=True,
            )


        st.write("")

        st.subheader(
            "Artemis' Paper of the Week"
        )

        if paper_of_week:

            with st.container(
                border=True,
            ):

                title = (
                    paper_of_week.get(
                        "title",
                        "Paper of the Week",
                    )
                )

                st.markdown(
                    f"### {title}"
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

                pubmed_url = (
                    paper_of_week.get(
                        "pubmed_url",
                        "",
                    )
                )

                if pubmed_url:

                    st.link_button(
                        "Open Paper",
                        pubmed_url,
                    )

        else:

            st.info(
                "Paper of the Week will appear after "
                "the research pipeline runs."
            )


        st.write("")

        st.subheader(
            "Discussion prompts"
        )

        questions = (
            journal_club.get(
                "discussion_questions",
                [],
            )
        )

        if (
            isinstance(questions, list)
            and questions
        ):

            for question in questions:

                with st.container(
                    border=True,
                ):

                    st.write(
                        question
                    )

        else:

            st.caption(
                "No discussion prompts are currently available."
            )
