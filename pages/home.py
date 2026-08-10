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


dashboard = load_json(
    "data/dashboard.json",
    {},
)

journal_club = load_json(
    "data/journal_club.json",
    {},
)

evidence_db = load_json(
    "data/evidence_database.json",
    [],
)


# =========================================================
# HELPERS
# =========================================================

def get_translation(record):
    value = record.get(
        "clinical_translation",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_appraisal(record):
    value = record.get(
        "appraisal",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_statistics(record):
    value = record.get(
        "statistics",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_metadata(record):
    value = record.get(
        "metadata",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_title(record):
    return (
        get_metadata(record).get("title")
        or "Untitled paper"
    )


def get_clinical_area(record):
    value = get_translation(
        record
    ).get(
        "clinical_area",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "Other"


def get_evidence_score(record):
    scores = get_appraisal(
        record
    ).get(
        "scores",
        {},
    )

    if not isinstance(
        scores,
        dict,
    ):
        return 0

    value = scores.get(
        "overall_evidence",
        0,
    )

    if isinstance(
        value,
        (int, float),
    ):
        return value

    return 0


def get_statistics_score(record):
    scores = get_statistics(
        record
    ).get(
        "scores",
        {},
    )

    if not isinstance(
        scores,
        dict,
    ):
        return 0

    value = scores.get(
        "overall_statistics",
        0,
    )

    if isinstance(
        value,
        (int, float),
    ):
        return value

    return 0


def get_practice_readiness(record):
    value = get_translation(
        record
    ).get(
        "practice_readiness",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "Not classified"


def get_takeaway(record):
    translation = get_translation(
        record
    )

    value = translation.get(
        "practitioner_takeaway",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    value = translation.get(
        "clinical_summary",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "No practitioner takeaway available."


def count_practice_informing():
    return sum(
        1
        for record in evidence_db
        if isinstance(record, dict)
        and get_practice_readiness(
            record
        ) == "Practice-informing"
    )


def count_clinical_areas():
    return len(
        {
            get_clinical_area(
                record
            )
            for record in evidence_db
            if isinstance(
                record,
                dict,
            )
        }
    )


def get_top_problem_counts():
    counts = {}

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        area = get_clinical_area(
            record
        )

        counts[
            area
        ] = (
            counts.get(
                area,
                0,
            )
            + 1
        )

    return sorted(
        counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )


def get_paper_of_week():
    paper = journal_club.get(
        "paper_of_the_week",
        {},
    )

    return (
        paper
        if isinstance(
            paper,
            dict,
        )
        else {}
    )


# =========================================================
# HEADER
# =========================================================

header_left, header_right = st.columns(
    [1.5, 1],
    gap="large",
)

with header_left:

    st.caption(
        "GOOD MORNING 👋"
    )

    st.title(
        "What problems are we solving today?"
    )

    st.write(
        "AI specialists continuously review, critique, and synthesize "
        "evidence so you can make better clinical decisions."
    )


with header_right:

    search_query = st.text_input(
        "Search",
        placeholder=(
            "Search problems, interventions, papers..."
        ),
        label_visibility="collapsed",
    )

    control_1, control_2 = st.columns(2)

    with control_1:

        st.button(
            "📅 Today",
            width="stretch",
        )

    with control_2:

        st.selectbox(
            "Time",
            [
                "This Week",
                "Last 30 Days",
                "Last 90 Days",
            ],
            label_visibility="collapsed",
        )


st.write("")


# =========================================================
# KPI ROW
# =========================================================

total_papers = (
    len(evidence_db)
    if isinstance(
        evidence_db,
        list,
    )
    else 0
)

practice_informing = (
    count_practice_informing()
)

clinical_areas = (
    count_clinical_areas()
)

needs_full_text = sum(
    1
    for record in evidence_db
    if isinstance(record, dict)
    and get_translation(
        record
    ).get(
        "requires_full_text_review",
        False,
    )
)

evidence_scores = [
    get_evidence_score(
        record
    )
    for record in evidence_db
    if isinstance(
        record,
        dict,
    )
    and get_evidence_score(
        record
    ) > 0
]

avg_evidence = (
    round(
        sum(
            evidence_scores
        )
        / len(
            evidence_scores
        ),
        1,
    )
    if evidence_scores
    else 0
)


k1, k2, k3, k4, k5 = st.columns(
    5,
    gap="medium",
)

with k1:

    st.metric(
        "New Papers",
        total_papers,
        border=True,
    )


with k2:

    st.metric(
        "Practice-Informing",
        practice_informing,
        border=True,
    )


with k3:

    st.metric(
        "Clinical Problems",
        clinical_areas,
        border=True,
    )


with k4:

    st.metric(
        "Needs Full Text",
        needs_full_text,
        border=True,
    )


with k5:

    st.metric(
        "Avg Evidence",
        avg_evidence,
        border=True,
    )


st.write("")


# =========================================================
# MAIN LAYOUT
# =========================================================

main_col, right_col = st.columns(
    [3.2, 1],
    gap="large",
)


# =========================================================
# LEFT SIDE
# =========================================================

with main_col:

    # -----------------------------------------------------
    # TOP CLINICAL PROBLEMS
    # -----------------------------------------------------

    title_col, link_col = st.columns(
        [5, 1],
    )

    with title_col:

        st.subheader(
            "Top Clinical Problems"
        )

    with link_col:

        st.page_link(
            "pages/clinical_problems.py",
            label="View all →",
        )


    top_problems = (
        get_top_problem_counts()[:5]
    )

    if top_problems:

        problem_cols = st.columns(
            len(top_problems),
            gap="small",
        )

        for col, (
            problem,
            paper_count,
        ) in zip(
            problem_cols,
            top_problems,
        ):

            with col:

                matching_records = [
                    record
                    for record in evidence_db
                    if isinstance(
                        record,
                        dict,
                    )
                    and get_clinical_area(
                        record
                    ) == problem
                ]

                scores = [
                    get_evidence_score(
                        record
                    )
                    for record in matching_records
                    if get_evidence_score(
                        record
                    ) > 0
                ]

                avg_score = (
                    round(
                        sum(scores)
                        / len(scores),
                        1,
                    )
                    if scores
                    else 0
                )

                with st.container(
                    border=True,
                ):

                    st.caption(
                        "CLINICAL PROBLEM"
                    )

                    st.markdown(
                        f"### {problem}"
                    )

                    st.caption(
                        f"{paper_count} studies"
                    )

                    st.metric(
                        "Avg Evidence",
                        avg_score,
                    )

                    if st.button(
                        "View problem →",
                        key=f"home_problem_{problem}",
                        width="stretch",
                    ):

                        st.session_state[
                            "selected_problem"
                        ] = problem

                        st.switch_page(
                            "pages/problem_detail.py"
                        )

    else:

        st.info(
            "Clinical problem data will appear after the evidence pipeline runs."
        )


    st.write("")


    # -----------------------------------------------------
    # AI SPECIALISTS
    # -----------------------------------------------------

    title_col, link_col = st.columns(
        [5, 1],
    )

    with title_col:

        st.subheader(
            "Your AI Specialists"
        )

    with link_col:

        st.page_link(
            "pages/ai_specialists.py",
            label="Meet team →",
        )


    specialists = [
        (
            "🌱",
            "Atlas",
            "Regenerative Medicine",
        ),
        (
            "⚡",
            "Vector",
            "Sports Performance",
        ),
        (
            "⚙️",
            "Newton",
            "Biomechanics",
        ),
        (
            "♡",
            "Athena",
            "Women's Athlete Health",
        ),
        (
            "Σ",
            "Euler",
            "Statistical Review",
        ),
        (
            "📚",
            "Artemis",
            "Journal Club",
        ),
    ]


    specialist_cols = st.columns(
        6,
        gap="small",
    )


    for col, (
        icon,
        name,
        role,
    ) in zip(
        specialist_cols,
        specialists,
    ):

        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"## {icon}"
                )

                st.markdown(
                    f"**{name}**"
                )

                st.caption(
                    role
                )

                if st.button(
                    "Open",
                    key=f"home_specialist_{name}",
                    width="stretch",
                ):

                    st.session_state[
                        "selected_specialist"
                    ] = name

                    st.switch_page(
                        "pages/ai_specialists.py"
                    )


    st.write("")


    # -----------------------------------------------------
    # RESEARCH INTELLIGENCE
    # -----------------------------------------------------

    st.subheader(
        "Research Intelligence"
    )


    evidence_col, paper_col, trend_col = (
        st.columns(
            [1.15, 1, 1],
            gap="medium",
        )
    )


    # -----------------------------------------------------
    # Evidence Overview
    # -----------------------------------------------------

    with evidence_col:

        with st.container(
            border=True,
        ):

            st.markdown(
                "#### 📊 Evidence Overview"
            )

            e1, e2 = st.columns(2)

            with e1:

                st.metric(
                    "Indexed",
                    total_papers,
                )

            with e2:

                st.metric(
                    "Practice-Informing",
                    practice_informing,
                )

            st.line_chart(
                {
                    "Papers": [
                        18,
                        24,
                        22,
                        31,
                        29,
                        37,
                        42,
                        38,
                        49,
                        52,
                        47,
                        58,
                    ]
                },
                height=220,
            )


    # -----------------------------------------------------
    # Paper of Week
    # -----------------------------------------------------

    with paper_col:

        with st.container(
            border=True,
        ):

            st.markdown(
                "#### ⭐ Paper of the Week"
            )

            paper = (
                get_paper_of_week()
            )

            if paper:

                title = paper.get(
                    "title",
                    "Paper of the Week",
                )

                study_design = paper.get(
                    "study_design",
                    "",
                )

                takeaway = paper.get(
                    "practitioner_takeaway",
                    "",
                )

                if study_design:
                    st.caption(
                        study_design
                    )

                st.markdown(
                    f"**{title}**"
                )

                if takeaway:
                    st.write(
                        takeaway
                    )

            else:

                st.info(
                    "Artemis will select a Paper of the Week after the pipeline runs."
                )

            st.page_link(
                "pages/journal_club.py",
                label="Read summary →",
            )


    # -----------------------------------------------------
    # Trending
    # -----------------------------------------------------

    with trend_col:

        with st.container(
            border=True,
        ):

            st.markdown(
                "#### 🔥 Trending Topics"
            )

            trending = (
                get_top_problem_counts()[:5]
            )

            if trending:

                max_count = max(
                    count
                    for _, count
                    in trending
                )

                for topic, count in trending:

                    st.write(
                        f"**{topic}**"
                    )

                    st.progress(
                        count / max_count
                    )

                    st.caption(
                        f"{count} indexed papers"
                    )

            else:

                st.caption(
                    "Trending topics will appear after indexing."
                )

            st.page_link(
                "pages/evidence_library.py",
                label="Explore research →",
            )


# =========================================================
# RIGHT SIDE
# =========================================================

with right_col:

    # -----------------------------------------------------
    # AI TEAM ACTIVITY
    # -----------------------------------------------------

    with st.container(
        border=True,
    ):

        st.markdown(
            "#### AI Team Activity"
        )

        specialist_activity = [
            (
                "🌱",
                "Atlas",
                "Regenerative Medicine",
                "Reviewing regenerative evidence",
            ),
            (
                "⚡",
                "Vector",
                "Sports Performance",
                "Tracking performance studies",
            ),
            (
                "⚙️",
                "Newton",
                "Biomechanics",
                "Mapping movement evidence",
            ),
            (
                "♡",
                "Athena",
                "Women's Athlete Health",
                "Reviewing female-athlete evidence",
            ),
            (
                "Σ",
                "Euler",
                "Statistics",
                "Checking methodology",
            ),
            (
                "📚",
                "Artemis",
                "Journal Club",
                "Curating priority papers",
            ),
        ]


        for (
            icon,
            name,
            role,
            activity,
        ) in specialist_activity:

            c1, c2 = st.columns(
                [1, 4],
            )

            with c1:

                st.markdown(
                    f"### {icon}"
                )

            with c2:

                st.markdown(
                    f"**{name}**"
                )

                st.caption(
                    role
                )

                st.caption(
                    activity
                )


    st.write("")


    # -----------------------------------------------------
    # EVIDENCE GAPS
    # -----------------------------------------------------

    with st.container(
        border=True,
    ):

        st.markdown(
            "#### Top Evidence Gaps"
        )

        area_gap_counts = {}

        for record in evidence_db:

            if not isinstance(
                record,
                dict,
            ):
                continue

            translation = (
                get_translation(
                    record
                )
            )

            flagged = (
                translation.get(
                    "requires_full_text_review",
                    False,
                )
                or get_evidence_score(
                    record
                ) <= 4
            )

            if not flagged:
                continue

            area = get_clinical_area(
                record
            )

            area_gap_counts[
                area
            ] = (
                area_gap_counts.get(
                    area,
                    0,
                )
                + 1
            )


        top_gaps = sorted(
            area_gap_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:5]


        if top_gaps:

            for index, (
                gap,
                count,
            ) in enumerate(
                top_gaps,
                start=1,
            ):

                st.markdown(
                    f"**{index}. {gap}**"
                )

                st.caption(
                    f"{count} uncertainty signals"
                )

        else:

            st.success(
                "No major evidence gaps are currently flagged."
            )


        st.page_link(
            "pages/evidence_gaps.py",
            label="View all gaps →",
        )


# =========================================================
# SEARCH FEEDBACK
# =========================================================

if search_query:

    st.write("")

    st.divider()

    st.subheader(
        "Search"
    )

    st.info(
        f'Search is ready for: "{search_query}". '
        "Next we can wire this directly into the Evidence Library."
    )
