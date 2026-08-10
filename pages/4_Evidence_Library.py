import json
from pathlib import Path

import streamlit as st


# =========================================================
# LOAD DATA
# =========================================================

def load_json(path, default=None):
    if default is None:
        default = []

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


def get_specialties(record):
    value = record.get(
        "specialties",
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


def get_clinical_area(record):
    translation = get_translation(
        record
    )

    value = translation.get(
        "clinical_area",
        "",
    )

    if isinstance(
        value,
        str,
    ) and value.strip():
        return value.strip()

    return "Other"


def get_intervention(record):
    translation = get_translation(
        record
    )

    value = translation.get(
        "intervention_or_exposure",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    appraisal = get_appraisal(
        record
    )

    value = appraisal.get(
        "intervention_or_exposure",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "Not clearly identified"


def get_study_design(record):
    metadata = get_metadata(
        record
    )

    value = metadata.get(
        "study_design"
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    appraisal = get_appraisal(
        record
    )

    value = appraisal.get(
        "study_design"
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "Unclear"


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


def get_specialty_names(record):
    specialties = get_specialties(
        record
    )

    labels = []

    mapping = {
        "regenerative_medicine": "Regenerative Medicine",
        "sports_performance": "Sports Performance",
        "biomechanics": "Biomechanics",
        "womens_athlete_health": "Women's Athlete Health",
    }

    for key, label in mapping.items():

        review = specialties.get(
            key,
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
            labels.append(
                label
            )

    return labels


def build_search_text(record):
    metadata = get_metadata(
        record
    )

    translation = get_translation(
        record
    )

    appraisal = get_appraisal(
        record
    )

    topics = metadata.get(
        "topics",
        [],
    )

    if not isinstance(
        topics,
        list,
    ):
        topics = []

    parts = [
        get_title(record),
        metadata.get(
            "abstract",
            "",
        ),
        get_journal(record),
        get_clinical_area(record),
        get_intervention(record),
        get_study_design(record),
        translation.get(
            "clinical_summary",
            "",
        ),
        translation.get(
            "practitioner_takeaway",
            "",
        ),
        appraisal.get(
            "population",
            "",
        ),
        " ".join(
            str(topic)
            for topic in topics
        ),
        " ".join(
            get_specialty_names(
                record
            )
        ),
    ]

    return " ".join(
        str(part)
        for part in parts
        if part
    ).lower()


# =========================================================
# HEADER
# =========================================================

st.caption(
    "RESEARCH LIBRARY"
)

st.title(
    "Evidence Library"
)

st.write(
    "Search, filter, and inspect the papers collected by your "
    "research pipeline."
)

st.write("")


# =========================================================
# SEARCH
# =========================================================

search = st.text_input(
    "Search evidence",
    placeholder=(
        "Search by condition, intervention, author, "
        "journal, study design, or keyword..."
    ),
    label_visibility="collapsed",
)


# =========================================================
# FILTER OPTIONS
# =========================================================

clinical_areas = sorted(
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

study_designs = sorted(
    {
        get_study_design(
            record
        )
        for record in evidence_db
        if isinstance(
            record,
            dict,
        )
    }
)

specialty_options = [
    "Regenerative Medicine",
    "Sports Performance",
    "Biomechanics",
    "Women's Athlete Health",
]


filter_1, filter_2, filter_3, filter_4 = (
    st.columns(
        4,
        gap="medium",
    )
)

with filter_1:

    selected_area = st.selectbox(
        "Clinical Area",
        [
            "All Clinical Areas",
            *clinical_areas,
        ],
    )


with filter_2:

    selected_design = st.selectbox(
        "Study Design",
        [
            "All Study Designs",
            *study_designs,
        ],
    )


with filter_3:

    selected_specialty = st.selectbox(
        "Specialty",
        [
            "All Specialties",
            *specialty_options,
        ],
    )


with filter_4:

    sort_option = st.selectbox(
        "Sort By",
        [
            "Highest Evidence Score",
            "Highest Statistics Score",
            "Newest",
            "Alphabetical",
        ],
    )


# =========================================================
# FILTER RECORDS
# =========================================================

filtered_records = []

for record in evidence_db:

    if not isinstance(
        record,
        dict,
    ):
        continue

    if search:

        query = search.lower().strip()

        if query not in build_search_text(
            record
        ):
            continue

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
        selected_design
        != "All Study Designs"
        and get_study_design(
            record
        )
        != selected_design
    ):
        continue

    if (
        selected_specialty
        != "All Specialties"
        and selected_specialty
        not in get_specialty_names(
            record
        )
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
    == "Highest Evidence Score"
):

    filtered_records.sort(
        key=lambda record: (
            get_evidence_score(
                record
            )
        ),
        reverse=True,
    )


elif (
    sort_option
    == "Highest Statistics Score"
):

    filtered_records.sort(
        key=lambda record: (
            get_statistics_score(
                record
            )
        ),
        reverse=True,
    )


elif sort_option == "Newest":

    filtered_records.sort(
        key=lambda record: str(
            get_year(
                record
            )
        ),
        reverse=True,
    )


else:

    filtered_records.sort(
        key=lambda record: (
            get_title(
                record
            ).lower()
        )
    )


# =========================================================
# SUMMARY METRICS
# =========================================================

total_indexed = (
    len(evidence_db)
    if isinstance(
        evidence_db,
        list,
    )
    else 0
)

practice_informing = sum(
    1
    for record in filtered_records
    if get_practice_readiness(
        record
    )
    == "Practice-informing"
)

needs_full_text = sum(
    1
    for record in filtered_records
    if get_translation(
        record
    ).get(
        "requires_full_text_review",
        False,
    )
)

high_evidence = sum(
    1
    for record in filtered_records
    if get_evidence_score(
        record
    )
    >= 8
)


m1, m2, m3, m4 = st.columns(
    4,
    gap="medium",
)

with m1:

    st.metric(
        "Indexed Papers",
        total_indexed,
        border=True,
    )


with m2:

    st.metric(
        "Results",
        len(
            filtered_records
        ),
        border=True,
    )


with m3:

    st.metric(
        "High Evidence",
        high_evidence,
        border=True,
    )


with m4:

    st.metric(
        "Practice-Informing",
        practice_informing,
        border=True,
    )


st.caption(
    f"{needs_full_text} of the current results require full-text review."
)

st.write("")


# =========================================================
# RESULT CONTROLS
# =========================================================

results_left, results_right = (
    st.columns(
        [4, 1],
    )
)

with results_left:

    st.subheader(
        "Research Papers"
    )


with results_right:

    st.caption(
        f"{len(filtered_records)} shown"
    )


# =========================================================
# EMPTY STATE
# =========================================================

if not filtered_records:

    st.info(
        "No papers match the current search and filters."
    )

    st.stop()


# =========================================================
# PAPER CARDS
# =========================================================

for index, record in enumerate(
    filtered_records,
    start=1,
):

    metadata = get_metadata(
        record
    )

    title = get_title(
        record
    )

    year = get_year(
        record
    )

    journal = get_journal(
        record
    )

    design = get_study_design(
        record
    )

    area = get_clinical_area(
        record
    )

    intervention = get_intervention(
        record
    )

    evidence_score = (
        get_evidence_score(
            record
        )
    )

    statistics_score = (
        get_statistics_score(
            record
        )
    )

    readiness = (
        get_practice_readiness(
            record
        )
    )

    specialty_names = (
        get_specialty_names(
            record
        )
    )

    with st.container(
        border=True,
    ):

        st.caption(
            f"RESULT {index}"
        )

        st.markdown(
            f"### {title}"
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

        if design:
            source_parts.append(
                str(design)
            )

        if source_parts:

            st.caption(
                " • ".join(
                    source_parts
                )
            )

        st.write("")

        c1, c2, c3, c4 = st.columns(
            4,
            gap="small",
        )

        with c1:

            st.metric(
                "Evidence",
                evidence_score,
            )


        with c2:

            st.metric(
                "Statistics",
                statistics_score,
            )


        with c3:

            st.metric(
                "Clinical Area",
                area,
            )


        with c4:

            st.metric(
                "Practice Readiness",
                readiness,
            )


        st.markdown(
            "**Intervention / exposure**"
        )

        st.write(
            intervention
        )


        if specialty_names:

            st.caption(
                "Specialists: "
                + " • ".join(
                    specialty_names
                )
            )


        takeaway = get_takeaway(
            record
        )

        with st.expander(
            "Practitioner takeaway"
        ):

            st.write(
                takeaway
            )


        abstract = metadata.get(
            "abstract",
            "",
        )

        if (
            isinstance(
                abstract,
                str,
            )
            and abstract.strip()
        ):

            with st.expander(
                "Abstract"
            ):

                st.write(
                    abstract
                )


        pubmed_url = get_pubmed_url(
            record
        )

        if pubmed_url:

            st.link_button(
                "Open PubMed",
                pubmed_url,
            )
