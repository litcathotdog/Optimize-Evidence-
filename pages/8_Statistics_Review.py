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

# Protect against malformed top-level JSON
if not isinstance(evidence_db, list):
    evidence_db = []


# =========================================================
# HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def get_metadata(record):
    if not isinstance(record, dict):
        return {}

    value = record.get(
        "metadata",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_statistics(record):
    if not isinstance(record, dict):
        return {}

    value = record.get(
        "statistics",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_appraisal(record):
    if not isinstance(record, dict):
        return {}

    value = record.get(
        "appraisal",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_translation(record):
    if not isinstance(record, dict):
        return {}

    value = record.get(
        "clinical_translation",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_title(record):
    metadata = get_metadata(
        record
    )

    title = clean_text(
        metadata.get(
            "title",
            "",
        )
    )

    return (
        title
        if title
        else "Untitled paper"
    )


def get_year(record):
    metadata = get_metadata(
        record
    )

    value = (
        metadata.get(
            "publication_year"
        )
        or metadata.get(
            "year"
        )
        or ""
    )

    return clean_text(
        value
    )


def get_year_number(record):
    year = get_year(
        record
    )

    try:
        return int(
            str(year)[:4]
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def get_journal(record):
    metadata = get_metadata(
        record
    )

    return clean_text(
        metadata.get(
            "journal",
            "",
        )
    )


def get_pubmed_url(record):
    metadata = get_metadata(
        record
    )

    url = clean_text(
        metadata.get(
            "pubmed_url",
            "",
        )
    )

    if url.startswith(
        ("http://", "https://")
    ):
        return url

    return ""


def get_clinical_area(record):
    translation = get_translation(
        record
    )

    value = clean_text(
        translation.get(
            "clinical_area",
            "",
        )
    )

    if value:
        return value

    return "Other"


def get_statistics_score(record):
    statistics = get_statistics(
        record
    )

    scores = statistics.get(
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

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0


def get_evidence_score(record):
    appraisal = get_appraisal(
        record
    )

    scores = appraisal.get(
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

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0


def normalize_confidence(value):
    value = clean_text(
        value
    )

    if not value:
        return "Unknown"

    normalized = value.lower()

    mapping = {
        "high": "High",
        "moderate": "Moderate",
        "medium": "Moderate",
        "low": "Low",
        "very low": "Very Low",
        "very-low": "Very Low",
        "very_low": "Very Low",
        "unknown": "Unknown",
    }

    return mapping.get(
        normalized,
        value,
    )


def get_statistical_confidence(record):
    statistics = get_statistics(
        record
    )

    return normalize_confidence(
        statistics.get(
            "statistical_confidence",
            "",
        )
    )


def get_reporting_flags(record):
    statistics = get_statistics(
        record
    )

    value = statistics.get(
        "reporting_flags",
        [],
    )

    if isinstance(
        value,
        list,
    ):
        return [
            clean_text(flag)
            for flag in value
            if clean_text(flag)
        ]

    if isinstance(
        value,
        str,
    ) and value.strip():

        return [
            value.strip()
        ]

    return []


def get_review_summary(record):
    statistics = get_statistics(
        record
    )

    value = clean_text(
        statistics.get(
            "review_summary",
            "",
        )
    )

    if value:
        return value

    return "No statistical review summary available."


def needs_full_text(record):
    translation = get_translation(
        record
    )

    value = translation.get(
        "requires_full_text_review",
        False,
    )

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        return (
            value.strip().lower()
            in {
                "true",
                "yes",
                "1",
            }
        )

    return bool(value)


# =========================================================
# PREPARE RECORDS
# =========================================================

reviewed_records = []

for record in evidence_db:

    if not isinstance(
        record,
        dict,
    ):
        continue

    statistics = get_statistics(
        record
    )

    if statistics:
        reviewed_records.append(
            record
        )


# =========================================================
# HEADER
# =========================================================

st.caption(
    "EULER • STATISTICAL REVIEW"
)

st.title(
    "Statistics Review"
)

st.write(
    "Evaluate statistical quality, reporting concerns, confidence, "
    "and methodological weaknesses across the evidence base."
)

st.write("")


# =========================================================
# SUMMARY METRICS
# =========================================================

high_confidence = sum(
    1
    for record in reviewed_records
    if get_statistical_confidence(
        record
    )
    == "High"
)

moderate_confidence = sum(
    1
    for record in reviewed_records
    if get_statistical_confidence(
        record
    )
    == "Moderate"
)

flagged_records = sum(
    1
    for record in reviewed_records
    if get_reporting_flags(
        record
    )
)

full_text_needed = sum(
    1
    for record in reviewed_records
    if needs_full_text(
        record
    )
)


m1, m2, m3, m4, m5 = st.columns(
    5,
    gap="medium",
)


with m1:

    st.metric(
        "Papers Reviewed",
        len(
            reviewed_records
        ),
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
        flagged_records,
        border=True,
    )


with m5:

    st.metric(
        "Needs Full Text",
        full_text_needed,
        border=True,
    )


st.write("")


# =========================================================
# SCORE DISTRIBUTION
# =========================================================

st.subheader(
    "Statistical Quality Overview"
)

score_buckets = {
    "8–10": 0,
    "6–7": 0,
    "4–5": 0,
    "1–3": 0,
    "Unscored": 0,
}


for record in reviewed_records:

    score = get_statistics_score(
        record
    )

    if score >= 8:
        score_buckets[
            "8–10"
        ] += 1

    elif score >= 6:
        score_buckets[
            "6–7"
        ] += 1

    elif score >= 4:
        score_buckets[
            "4–5"
        ] += 1

    elif score >= 1:
        score_buckets[
            "1–3"
        ] += 1

    else:
        score_buckets[
            "Unscored"
        ] += 1


bucket_cols = st.columns(
    5,
    gap="small",
)


for col, (
    label,
    count,
) in zip(
    bucket_cols,
    score_buckets.items(),
):

    with col:

        with st.container(
            border=True,
        ):

            st.metric(
                label,
                count,
            )


st.write("")


# =========================================================
# FILTERS
# =========================================================

clinical_areas = sorted(
    {
        get_clinical_area(
            record
        )
        for record in reviewed_records
    }
)


confidence_options = [
    "High",
    "Moderate",
    "Low",
    "Very Low",
    "Unknown",
]


f1, f2, f3, f4 = st.columns(
    4,
    gap="medium",
)


with f1:

    selected_area = st.selectbox(
        "Clinical Area",
        [
            "All Clinical Areas",
            *clinical_areas,
        ],
    )


with f2:

    selected_confidence = (
        st.selectbox(
            "Statistical Confidence",
            [
                "All Confidence Levels",
                *confidence_options,
            ],
        )
    )


with f3:

    selected_flag_status = (
        st.selectbox(
            "Reporting Flags",
            [
                "All Papers",
                "Flagged Only",
                "No Flags",
            ],
        )
    )


with f4:

    sort_option = st.selectbox(
        "Sort By",
        [
            "Lowest Statistics Score",
            "Highest Statistics Score",
            "Most Flags",
            "Highest Evidence Score",
            "Newest",
        ],
    )


# =========================================================
# FILTER RECORDS
# =========================================================

filtered_records = []


for record in reviewed_records:

    if (
        selected_area
        != "All Clinical Areas"
        and get_clinical_area(
            record
        )
        != selected_area
    ):
        continue


    if (
        selected_confidence
        != "All Confidence Levels"
        and get_statistical_confidence(
            record
        )
        != selected_confidence
    ):
        continue


    flags = get_reporting_flags(
        record
    )


    if (
        selected_flag_status
        == "Flagged Only"
        and not flags
    ):
        continue


    if (
        selected_flag_status
        == "No Flags"
        and flags
    ):
        continue


    filtered_records.append(
        record
    )


# =========================================================
# SORT
# =========================================================

if (
    sort_option
    == "Lowest Statistics Score"
):

    filtered_records.sort(
        key=lambda record: (
            get_statistics_score(
                record
            )
            if get_statistics_score(
                record
            ) > 0
            else float("inf")
        )
    )


elif (
    sort_option
    == "Highest Statistics Score"
):

    filtered_records.sort(
        key=get_statistics_score,
        reverse=True,
    )


elif (
    sort_option
    == "Most Flags"
):

    filtered_records.sort(
        key=lambda record: len(
            get_reporting_flags(
                record
            )
        ),
        reverse=True,
    )


elif (
    sort_option
    == "Highest Evidence Score"
):

    filtered_records.sort(
        key=get_evidence_score,
        reverse=True,
    )


else:

    filtered_records.sort(
        key=get_year_number,
        reverse=True,
    )


# =========================================================
# FLAG SUMMARY
# =========================================================

st.subheader(
    "Most Common Statistical Concerns"
)

flag_counts = {}


for record in reviewed_records:

    for flag in get_reporting_flags(
        record
    ):

        flag_counts[
            flag
        ] = (
            flag_counts.get(
                flag,
                0,
            )
            + 1
        )


top_flags = sorted(
    flag_counts.items(),
    key=lambda item: item[1],
    reverse=True,
)[:6]


if top_flags:

    flag_cols = st.columns(
        3,
        gap="medium",
    )


    for index, (
        flag,
        count,
    ) in enumerate(
        top_flags
    ):

        col = flag_cols[
            index % 3
        ]


        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"**{flag}**"
                )

                st.metric(
                    "Papers",
                    count,
                )


else:

    st.success(
        "No statistical reporting concerns are currently flagged."
    )


st.write("")


# =========================================================
# PAPER REVIEWS
# =========================================================

st.subheader(
    "Paper-Level Statistical Reviews"
)

st.caption(
    f"{len(filtered_records)} papers shown"
)


if not filtered_records:

    st.info(
        "No papers match the current filters."
    )


else:

    for index, record in enumerate(
        filtered_records,
        start=1,
    ):

        title = get_title(
            record
        )

        journal = get_journal(
            record
        )

        year = get_year(
            record
        )

        area = get_clinical_area(
            record
        )

        stats_score = (
            get_statistics_score(
                record
            )
        )

        evidence_score = (
            get_evidence_score(
                record
            )
        )

        confidence = (
            get_statistical_confidence(
                record
            )
        )

        flags = get_reporting_flags(
            record
        )


        with st.expander(
            f"{index}. {title}"
        ):

            source_parts = []


            if journal:
                source_parts.append(
                    journal
                )

            if year:
                source_parts.append(
                    year
                )

            if area:
                source_parts.append(
                    area
                )


            if source_parts:

                st.caption(
                    " • ".join(
                        source_parts
                    )
                )


            c1, c2, c3, c4 = (
                st.columns(
                    4
                )
            )


            with c1:

                st.metric(
                    "Statistics Score",
                    stats_score,
                )


            with c2:

                st.metric(
                    "Evidence Score",
                    evidence_score,
                )


            with c3:

                st.metric(
                    "Confidence",
                    confidence,
                )


            with c4:

                st.metric(
                    "Reporting Flags",
                    len(
                        flags
                    ),
                )


            st.markdown(
                "**Euler's review**"
            )

            st.write(
                get_review_summary(
                    record
                )
            )


            if flags:

                st.markdown(
                    "**Statistical concerns**"
                )

                for flag in flags:

                    st.write(
                        f"• {flag}"
                    )


            else:

                st.success(
                    "No statistical reporting flags were identified."
                )


            if needs_full_text(
                record
            ):

                st.warning(
                    "Full-text review is recommended before drawing "
                    "strong statistical conclusions."
                )


            pubmed_url = (
                get_pubmed_url(
                    record
                )
            )

            if pubmed_url:

                st.link_button(
                    "Open PubMed",
                    pubmed_url,
                )


# =========================================================
# STATISTICS WORKSPACE
# =========================================================

st.write("")

st.divider()

st.subheader(
    "Euler Workspace"
)

st.write(
    "Use this section to describe a study or analysis question. "
    "For Stage 1 this is a structured workspace; later we can connect "
    "Euler to an AI model for interactive statistical guidance."
)


workspace_1, workspace_2 = (
    st.columns(
        2
    )
)


with workspace_1:

    study_design = st.selectbox(
        "Study Design",
        [
            "Randomized Controlled Trial",
            "Prospective Cohort",
            "Retrospective Cohort",
            "Cross-Sectional Study",
            "Case-Control Study",
            "Method Comparison Study",
            "Diagnostic Accuracy Study",
            "Systematic Review",
            "Meta-Analysis",
            "Other",
        ],
        key="euler_study_design",
    )


with workspace_2:

    analysis_goal = st.selectbox(
        "Primary Analysis Goal",
        [
            "Compare two methods",
            "Compare groups",
            "Evaluate association",
            "Predict an outcome",
            "Assess reliability",
            "Assess diagnostic accuracy",
            "Estimate treatment effect",
            "Other",
        ],
        key="euler_analysis_goal",
    )


variables = st.text_area(
    "Describe the variables",
    placeholder=(
        "Example: body fat percentage measured by DXA and "
        "AI-estimated body fat percentage measured once per participant."
    ),
    key="euler_variables",
)


if st.button(
    "Review analysis setup",
    width="stretch",
    key="euler_review_setup",
):

    if not variables.strip():

        st.warning(
            "Describe the variables first."
        )


    else:

        st.info(
            f"Study design: {study_design}\n\n"
            f"Analysis goal: {analysis_goal}\n\n"
            "The interface is ready. In Stage 2, Euler can use this "
            "information to recommend statistical tests, assumptions, "
            "agreement analyses, effect-size reporting, and sensitivity checks."
        )
