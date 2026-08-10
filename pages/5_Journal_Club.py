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


def get_title(record):
    metadata = get_metadata(
        record
    )

    return (
        metadata.get(
            "title"
        )
        or "Untitled paper"
    )


def get_year(record):
    metadata = get_metadata(
        record
    )

    return (
        metadata.get(
            "publication_year"
        )
        or metadata.get(
            "year"
        )
        or ""
    )


def get_journal(record):
    metadata = get_metadata(
        record
    )

    return (
        metadata.get(
            "journal"
        )
        or ""
    )


def get_pubmed_url(record):
    metadata = get_metadata(
        record
    )

    return (
        metadata.get(
            "pubmed_url"
        )
        or ""
    )


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

    return 0


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

    return 0


def get_practice_readiness(record):
    translation = get_translation(
        record
    )

    value = translation.get(
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


def get_clinical_area(record):
    translation = get_translation(
        record
    )

    value = translation.get(
        "clinical_area",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "Other"


def find_record_by_title(title):
    if not title:
        return None

    title_lower = str(
        title
    ).strip().lower()

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        if (
            get_title(
                record
            ).strip().lower()
            == title_lower
        ):
            return record

    return None


# =========================================================
# HEADER
# =========================================================

st.caption(
    "ARTEMIS • JOURNAL CLUB"
)

st.title(
    "Journal Club"
)

st.write(
    "A curated view of the most clinically relevant new research, "
    "with structured discussion prompts and evidence critique."
)

st.write("")


# =========================================================
# EXECUTIVE SUMMARY
# =========================================================

summary = journal_club.get(
    "executive_summary",
    {},
)

if not isinstance(
    summary,
    dict,
):
    summary = {}


m1, m2, m3, m4 = st.columns(
    4,
    gap="medium",
)

with m1:

    st.metric(
        "High Priority Papers",
        summary.get(
            "high_priority_papers",
            0,
        ),
        border=True,
    )


with m2:

    st.metric(
        "Practice-Informing",
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


with m4:

    st.metric(
        "Indexed Papers",
        len(
            evidence_db
        )
        if isinstance(
            evidence_db,
            list,
        )
        else 0,
        border=True,
    )


st.write("")


# =========================================================
# PAPER OF THE WEEK
# =========================================================

st.subheader(
    "⭐ Paper of the Week"
)

paper_of_week = journal_club.get(
    "paper_of_the_week",
    {},
)

if not isinstance(
    paper_of_week,
    dict,
):
    paper_of_week = {}


if paper_of_week:

    title = paper_of_week.get(
        "title",
        "Paper of the Week",
    )

    matching_record = (
        find_record_by_title(
            title
        )
    )

    with st.container(
        border=True,
    ):

        st.caption(
            "ARTEMIS' TOP PICK"
        )

        st.markdown(
            f"## {title}"
        )

        study_design = paper_of_week.get(
            "study_design",
            "",
        )

        if study_design:
            st.caption(
                study_design
            )

        if matching_record:

            metadata = get_metadata(
                matching_record
            )

            source_parts = []

            journal = get_journal(
                matching_record
            )

            year = get_year(
                matching_record
            )

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

            c1, c2, c3 = st.columns(
                3
            )

            with c1:

                st.metric(
                    "Evidence Score",
                    get_evidence_score(
                        matching_record
                    ),
                )

            with c2:

                st.metric(
                    "Statistics Score",
                    get_statistics_score(
                        matching_record
                    ),
                )

            with c3:

                st.metric(
                    "Practice Readiness",
                    get_practice_readiness(
                        matching_record
                    ),
                )

        practitioner_takeaway = (
            paper_of_week.get(
                "practitioner_takeaway",
                "",
            )
        )

        if not practitioner_takeaway and matching_record:

            practitioner_takeaway = (
                get_takeaway(
                    matching_record
                )
            )

        if practitioner_takeaway:

            st.markdown(
                "**Why this matters**"
            )

            st.write(
                practitioner_takeaway
            )

        controversy = paper_of_week.get(
            "controversy",
            "",
        )

        if controversy:

            st.markdown(
                "**What deserves debate**"
            )

            st.warning(
                controversy
            )

        if matching_record:

            pubmed_url = get_pubmed_url(
                matching_record
            )

            if pubmed_url:

                st.link_button(
                    "Open PubMed",
                    pubmed_url,
                )

        else:

            paper_url = paper_of_week.get(
                "pubmed_url",
                "",
            )

            if paper_url:

                st.link_button(
                    "Open Paper",
                    paper_url,
                )


else:

    st.info(
        "Artemis has not selected a Paper of the Week yet. "
        "This will populate after the journal-club pipeline runs."
    )


st.write("")


# =========================================================
# DISCUSSION QUESTIONS
# =========================================================

st.subheader(
    "Discussion Prompts"
)

questions = journal_club.get(
    "discussion_questions",
    [],
)

if (
    isinstance(
        questions,
        list,
    )
    and questions
):

    question_cols = st.columns(
        2,
        gap="medium",
    )

    for index, question in enumerate(
        questions
    ):

        col = question_cols[
            index % 2
        ]

        with col:

            with st.container(
                border=True,
            ):

                st.caption(
                    f"QUESTION {index + 1}"
                )

                st.write(
                    question
                )

else:

    st.caption(
        "No discussion prompts are currently available."
    )


st.write("")


# =========================================================
# HIGH-PRIORITY PAPERS
# =========================================================

st.subheader(
    "High-Priority Papers"
)

priority_papers = journal_club.get(
    "high_priority_papers",
    [],
)

if not isinstance(
    priority_papers,
    list,
):
    priority_papers = []


# If journal_club.json doesn't contain a list, build one
# from the strongest indexed evidence instead.

if not priority_papers:

    candidate_records = [
        record
        for record in evidence_db
        if isinstance(
            record,
            dict,
        )
    ]

    candidate_records.sort(
        key=lambda record: (
            get_evidence_score(
                record
            ),
            get_statistics_score(
                record
            ),
        ),
        reverse=True,
    )

    priority_papers = (
        candidate_records[:10]
    )


for index, item in enumerate(
    priority_papers[:10],
    start=1,
):

    if isinstance(
        item,
        dict,
    ) and "metadata" in item:

        record = item
        title = get_title(
            record
        )

    elif isinstance(
        item,
        dict,
    ):

        title = item.get(
            "title",
            "Untitled paper",
        )

        record = (
            find_record_by_title(
                title
            )
        )

    else:

        title = str(
            item
        )

        record = (
            find_record_by_title(
                title
            )
        )


    with st.expander(
        f"{index}. {title}"
    ):

        if record:

            source_parts = []

            journal = get_journal(
                record
            )

            year = get_year(
                record
            )

            area = get_clinical_area(
                record
            )

            if journal:
                source_parts.append(
                    str(journal)
                )

            if year:
                source_parts.append(
                    str(year)
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

            c1, c2, c3 = st.columns(
                3
            )

            with c1:

                st.metric(
                    "Evidence",
                    get_evidence_score(
                        record
                    ),
                )

            with c2:

                st.metric(
                    "Statistics",
                    get_statistics_score(
                        record
                    ),
                )

            with c3:

                st.metric(
                    "Practice Readiness",
                    get_practice_readiness(
                        record
                    ),
                )

            st.markdown(
                "**Practitioner takeaway**"
            )

            st.write(
                get_takeaway(
                    record
                )
            )

            pubmed_url = get_pubmed_url(
                record
            )

            if pubmed_url:

                st.link_button(
                    "Open PubMed",
                    pubmed_url,
                )

        elif isinstance(
            item,
            dict,
        ):

            takeaway = item.get(
                "practitioner_takeaway",
                "",
            )

            if takeaway:
                st.write(
                    takeaway
                )

            st.caption(
                "This paper is listed by Artemis but was not matched "
                "to a full evidence-database record."
            )


st.write("")


# =========================================================
# JOURNAL CLUB BY CLINICAL AREA
# =========================================================

st.subheader(
    "Explore by Clinical Area"
)

area_counts = {}

for record in evidence_db:

    if not isinstance(
        record,
        dict,
    ):
        continue

    area = get_clinical_area(
        record
    )

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

    area_cols = st.columns(
        3,
        gap="medium",
    )

    for index, (
        area,
        count,
    ) in enumerate(
        sorted_areas[:9]
    ):

        col = area_cols[
            index % 3
        ]

        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"**{area}**"
                )

                st.metric(
                    "Papers",
                    count,
                )

                if st.button(
                    "Explore evidence →",
                    key=f"journal_area_{index}",
                    width="stretch",
                ):

                    st.session_state[
                        "evidence_library_area"
                    ] = area

                    st.switch_page(
                        "pages/evidence_library.py"
                    )

else:

    st.info(
        "Clinical-area data will appear after the evidence pipeline runs."
    )
