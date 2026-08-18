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

evidence_db = load_json(
    "data/evidence_database.json",
    [],
)

journal_club = load_json(
    "data/journal_club.json",
    {},
)

# Protect against malformed top-level JSON
if not isinstance(dashboard, dict):
    dashboard = {}

if not isinstance(evidence_db, list):
    evidence_db = []

if not isinstance(journal_club, dict):
    journal_club = {}


# =========================================================
# HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


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


def get_title(record):
    title = clean_text(
        get_metadata(
            record
        ).get(
            "title",
            "",
        )
    )

    return (
        title
        if title
        else "Untitled paper"
    )


def get_clinical_area(record):
    value = clean_text(
        get_translation(
            record
        ).get(
            "clinical_area",
            "",
        )
    )

    if value:
        return value

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

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
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

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0


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


def get_practitioner_takeaway(record):
    translation = get_translation(
        record
    )

    value = clean_text(
        translation.get(
            "practitioner_takeaway",
            "",
        )
    )

    if value:
        return value

    value = clean_text(
        translation.get(
            "clinical_summary",
            "",
        )
    )

    if value:
        return value

    return ""


def has_nonempty_list(value):
    return (
        isinstance(value, list)
        and len(value) > 0
    )


def get_gap_candidates():
    candidates = []

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        translation = get_translation(
            record
        )

        appraisal = get_appraisal(
            record
        )

        statistics = get_statistics(
            record
        )

        flags = []


        # ---------------------------------------------
        # Full-text review
        # ---------------------------------------------

        requires_full_text = translation.get(
            "requires_full_text_review",
            False,
        )

        if requires_full_text is True:
            flags.append(
                "Requires full-text review"
            )


        # ---------------------------------------------
        # Weak evidence
        # ---------------------------------------------

        evidence_score = (
            get_evidence_score(
                record
            )
        )

        if (
            evidence_score > 0
            and evidence_score <= 4
        ):
            flags.append(
                "Low evidence strength"
            )


        # ---------------------------------------------
        # Weak statistics
        # ---------------------------------------------

        statistics_score = (
            get_statistics_score(
                record
            )
        )

        if (
            statistics_score > 0
            and statistics_score <= 4
        ):
            flags.append(
                "Weak statistical support"
            )


        # ---------------------------------------------
        # Statistical flags
        # ---------------------------------------------

        reporting_flags = (
            statistics.get(
                "reporting_flags",
                [],
            )
        )

        if has_nonempty_list(
            reporting_flags
        ):
            flags.append(
                "Statistical reporting concerns"
            )


        # ---------------------------------------------
        # Appraisal flags
        # ---------------------------------------------

        appraisal_flags = appraisal.get(
            "flags",
            [],
        )

        if has_nonempty_list(
            appraisal_flags
        ):
            flags.append(
                "Evidence appraisal concerns"
            )


        # ---------------------------------------------
        # Practice readiness
        # ---------------------------------------------

        readiness = clean_text(
            translation.get(
                "practice_readiness",
                "",
            )
        )

        if (
            readiness
            and readiness.lower()
            != "practice-informing"
        ):
            flags.append(
                "Not yet practice-informing"
            )


        # ---------------------------------------------
        # Add record if any concern exists
        # ---------------------------------------------

        if flags:

            candidates.append(
                {
                    "record": record,
                    "flags": flags,
                    "area": get_clinical_area(
                        record
                    ),
                    "evidence_score": evidence_score,
                    "statistics_score": statistics_score,
                }
            )

    return candidates


# =========================================================
# HEADER
# =========================================================

st.caption(
    "RESEARCH UNCERTAINTY"
)

st.title(
    "Evidence Gaps"
)

st.write(
    "Identify where the current evidence base is weak, incomplete, "
    "conflicting, or not yet ready to support confident clinical decisions."
)

st.write("")


# =========================================================
# BUILD GAP DATA
# =========================================================

gap_candidates = (
    get_gap_candidates()
)


# =========================================================
# SUMMARY METRICS
# =========================================================

full_text_count = sum(
    1
    for item in gap_candidates
    if "Requires full-text review"
    in item["flags"]
)

low_evidence_count = sum(
    1
    for item in gap_candidates
    if "Low evidence strength"
    in item["flags"]
)

statistical_issue_count = sum(
    1
    for item in gap_candidates
    if (
        "Weak statistical support"
        in item["flags"]
        or
        "Statistical reporting concerns"
        in item["flags"]
    )
)

affected_areas = len(
    {
        item["area"]
        for item in gap_candidates
    }
)


m1, m2, m3, m4 = st.columns(
    4,
    gap="medium",
)


with m1:

    st.metric(
        "Flagged Papers",
        len(
            gap_candidates
        ),
        border=True,
    )


with m2:

    st.metric(
        "Needs Full Text",
        full_text_count,
        border=True,
    )


with m3:

    st.metric(
        "Statistical Concerns",
        statistical_issue_count,
        border=True,
    )


with m4:

    st.metric(
        "Clinical Areas",
        affected_areas,
        border=True,
    )


st.write("")


# =========================================================
# FILTERS
# =========================================================

clinical_areas = sorted(
    {
        item["area"]
        for item in gap_candidates
        if item.get(
            "area"
        )
    }
)


filter_col, sort_col = st.columns(
    [2, 1],
    gap="medium",
)


with filter_col:

    selected_area = st.selectbox(
        "Clinical Area",
        [
            "All Clinical Areas",
            *clinical_areas,
        ],
    )


with sort_col:

    sort_option = st.selectbox(
        "Sort",
        [
            "Most Concerns",
            "Lowest Evidence",
            "Lowest Statistics",
            "Alphabetical",
        ],
    )


# =========================================================
# FILTER GAP RECORDS
# =========================================================

filtered_gaps = []


for item in gap_candidates:

    if (
        selected_area
        != "All Clinical Areas"
        and item["area"]
        != selected_area
    ):
        continue

    filtered_gaps.append(
        item
    )


# =========================================================
# SORT
# =========================================================

if sort_option == "Most Concerns":

    filtered_gaps.sort(
        key=lambda item: len(
            item["flags"]
        ),
        reverse=True,
    )


elif sort_option == "Lowest Evidence":

    filtered_gaps.sort(
        key=lambda item: (
            item[
                "evidence_score"
            ]
            if item[
                "evidence_score"
            ] > 0
            else float("inf")
        )
    )


elif sort_option == "Lowest Statistics":

    filtered_gaps.sort(
        key=lambda item: (
            item[
                "statistics_score"
            ]
            if item[
                "statistics_score"
            ] > 0
            else float("inf")
        )
    )


else:

    filtered_gaps.sort(
        key=lambda item: (
            get_title(
                item["record"]
            ).lower()
        )
    )


# =========================================================
# AREA-LEVEL GAP OVERVIEW
# =========================================================

st.subheader(
    "Where uncertainty is concentrated"
)

area_counts = {}


for item in gap_candidates:

    area = item["area"]

    area_counts[
        area
    ] = (
        area_counts.get(
            area,
            0,
        )
        + 1
    )


sorted_areas = sorted(
    area_counts.items(),
    key=lambda item: item[1],
    reverse=True,
)


if sorted_areas:

    visible_areas = (
        sorted_areas[:4]
    )

    area_cols = st.columns(
        len(
            visible_areas
        ),
        gap="medium",
    )


    for col, (
        area,
        count,
    ) in zip(
        area_cols,
        visible_areas,
    ):

        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"**{area}**"
                )

                st.metric(
                    "Flagged Papers",
                    count,
                )


else:

    st.success(
        "No evidence gaps are currently flagged."
    )


st.write("")


# =========================================================
# PAPER-LEVEL GAPS
# =========================================================

st.subheader(
    "Flagged Evidence"
)

st.caption(
    f"{len(filtered_gaps)} papers shown"
)


if not filtered_gaps:

    st.info(
        "No papers match the current filters."
    )


else:

    for index, item in enumerate(
        filtered_gaps,
        start=1,
    ):

        record = item[
            "record"
        ]

        metadata = get_metadata(
            record
        )

        title = get_title(
            record
        )

        journal = clean_text(
            metadata.get(
                "journal",
                "",
            )
        )

        year = clean_text(
            metadata.get(
                "publication_year"
            )
            or metadata.get(
                "year"
            )
            or ""
        )


        with st.container(
            border=True,
        ):

            st.caption(
                f"GAP SIGNAL {index}"
            )

            st.markdown(
                f"### {title}"
            )


            source_parts = []

            if journal:
                source_parts.append(
                    journal
                )

            if year:
                source_parts.append(
                    year
                )

            if item["area"]:
                source_parts.append(
                    item["area"]
                )


            if source_parts:

                st.caption(
                    " • ".join(
                        source_parts
                    )
                )


            c1, c2, c3 = st.columns(
                3
            )


            with c1:

                st.metric(
                    "Evidence Score",
                    item[
                        "evidence_score"
                    ],
                )


            with c2:

                st.metric(
                    "Statistics Score",
                    item[
                        "statistics_score"
                    ],
                )


            with c3:

                st.metric(
                    "Gap Signals",
                    len(
                        item["flags"]
                    ),
                )


            st.markdown(
                "**Why this paper is flagged**"
            )


            for flag in item[
                "flags"
            ]:

                st.write(
                    f"• {flag}"
                )


            takeaway = (
                get_practitioner_takeaway(
                    record
                )
            )

            if takeaway:

                with st.expander(
                    "Practitioner takeaway"
                ):

                    st.write(
                        takeaway
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
