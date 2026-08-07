import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Evidence Library",
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


evidence_db = load_json(
    "data/evidence_database.json",
    [],
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        EVIDENCE LIBRARY
    </div>

    <h1 class="hero-title">
        Search the <span>evidence</span>
    </h1>

    <p class="hero-subtitle">
        Search across the full evidence database and filter studies by
        clinical area, specialty, study design, evidence quality,
        statistical confidence, and practice readiness.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

search_query = st.text_input(
    "Search",
    placeholder=(
        "Try: PRP, patellar tendinopathy, RED-S, "
        "sprint performance, ACL..."
    ),
    label_visibility="collapsed",
)


# ---------------------------------------------------------
# Build filter options
# ---------------------------------------------------------

clinical_areas = set()
study_designs = set()
practice_readiness_options = set()
specialty_options = {
    "Regenerative Medicine": "regenerative_medicine",
    "Sports Performance": "sports_performance",
    "Biomechanics": "biomechanics",
    "Women's Athlete Health": "womens_athlete_health",
}


for record in evidence_db:

    translation = record.get(
        "clinical_translation",
        {},
    )

    appraisal = record.get(
        "appraisal",
        {},
    )

    if isinstance(
        translation,
        dict,
    ):
        clinical_area = translation.get(
            "clinical_area"
        )

        if clinical_area:
            clinical_areas.add(
                clinical_area
            )

        readiness = translation.get(
            "practice_readiness"
        )

        if readiness:
            practice_readiness_options.add(
                readiness
            )

    if isinstance(
        appraisal,
        dict,
    ):
        design = appraisal.get(
            "study_design"
        )

        if design:
            study_designs.add(
                design
            )


# ---------------------------------------------------------
# Filters
# ---------------------------------------------------------

f1, f2, f3, f4 = st.columns(4)

with f1:
    selected_area = st.selectbox(
        "Clinical Area",
        [
            "All",
            *sorted(
                clinical_areas
            ),
        ],
    )

with f2:
    selected_specialty = st.selectbox(
        "Specialty",
        [
            "All",
            *specialty_options.keys(),
        ],
    )

with f3:
    selected_design = st.selectbox(
        "Study Design",
        [
            "All",
            *sorted(
                study_designs
            ),
        ],
    )

with f4:
    selected_readiness = st.selectbox(
        "Practice Readiness",
        [
            "All",
            *sorted(
                practice_readiness_options
            ),
        ],
    )


# ---------------------------------------------------------
# Score filters
# ---------------------------------------------------------

s1, s2 = st.columns(2)

with s1:
    minimum_evidence = st.slider(
        "Minimum Evidence Score",
        min_value=0,
        max_value=10,
        value=0,
    )

with s2:
    minimum_statistics = st.slider(
        "Minimum Statistics Score",
        min_value=0,
        max_value=10,
        value=0,
    )


# ---------------------------------------------------------
# Filtering
# ---------------------------------------------------------

def paper_matches(record):

    metadata = record.get(
        "metadata",
        {},
    )

    appraisal = record.get(
        "appraisal",
        {},
    )

    statistics = record.get(
        "statistics",
        {},
    )

    translation = record.get(
        "clinical_translation",
        {},
    )

    specialties = record.get(
        "specialties",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    if not isinstance(
        appraisal,
        dict,
    ):
        appraisal = {}

    if not isinstance(
        statistics,
        dict,
    ):
        statistics = {}

    if not isinstance(
        translation,
        dict,
    ):
        translation = {}

    if not isinstance(
        specialties,
        dict,
    ):
        specialties = {}

    # Search
    if search_query:

        searchable = json.dumps(
            record,
            ensure_ascii=False,
        ).lower()

        if (
            search_query.lower()
            not in searchable
        ):
            return False

    # Clinical area
    if (
        selected_area != "All"
        and translation.get(
            "clinical_area"
        )
        != selected_area
    ):
        return False

    # Specialty
    if selected_specialty != "All":

        key = specialty_options[
            selected_specialty
        ]

        specialty_data = specialties.get(
            key,
            {},
        )

        if not (
            isinstance(
                specialty_data,
                dict,
            )
            and specialty_data.get(
                "relevant",
                False,
            )
        ):
            return False

    # Study design
    if (
        selected_design != "All"
        and appraisal.get(
            "study_design"
        )
        != selected_design
    ):
        return False

    # Practice readiness
    if (
        selected_readiness != "All"
        and translation.get(
            "practice_readiness"
        )
        != selected_readiness
    ):
        return False

    # Evidence score
    appraisal_scores = appraisal.get(
        "scores",
        {},
    )

    if not isinstance(
        appraisal_scores,
        dict,
    ):
        appraisal_scores = {}

    evidence_score = appraisal_scores.get(
        "overall_evidence",
        0,
    )

    if (
        not isinstance(
            evidence_score,
            (int, float),
        )
    ):
        evidence_score = 0

    if (
        evidence_score
        < minimum_evidence
    ):
        return False

    # Statistics score
    statistics_scores = statistics.get(
        "scores",
        {},
    )

    if not isinstance(
        statistics_scores,
        dict,
    ):
        statistics_scores = {}

    statistics_score = statistics_scores.get(
        "overall_statistics",
        0,
    )

    if (
        not isinstance(
            statistics_score,
            (int, float),
        )
    ):
        statistics_score = 0

    if (
        statistics_score
        < minimum_statistics
    ):
        return False

    return True


filtered_papers = [
    record
    for record in evidence_db
    if paper_matches(
        record
    )
]


# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------

sort_option = st.selectbox(
    "Sort results",
    [
        "Highest Evidence",
        "Highest Statistics",
        "Highest Practitioner Relevance",
        "Newest",
    ],
)


def get_score(
    record,
    category,
):
    appraisal = record.get(
        "appraisal",
        {},
    )

    statistics = record.get(
        "statistics",
        {},
    )

    if not isinstance(
        appraisal,
        dict,
    ):
        appraisal = {}

    if not isinstance(
        statistics,
        dict,
    ):
        statistics = {}

    if category == "evidence":
        return (
            appraisal.get(
                "scores",
                {},
            ).get(
                "overall_evidence",
                0,
            )
        )

    if category == "statistics":
        return (
            statistics.get(
                "scores",
                {},
            ).get(
                "overall_statistics",
                0,
            )
        )

    if category == "relevance":
        return (
            appraisal.get(
                "scores",
                {},
            ).get(
                "practitioner_relevance",
                0,
            )
        )

    return 0


if sort_option == "Highest Evidence":

    filtered_papers.sort(
        key=lambda record: get_score(
            record,
            "evidence",
        ),
        reverse=True,
    )

elif sort_option == "Highest Statistics":

    filtered_papers.sort(
        key=lambda record: get_score(
            record,
            "statistics",
        ),
        reverse=True,
    )

elif sort_option == "Highest Practitioner Relevance":

    filtered_papers.sort(
        key=lambda record: get_score(
            record,
            "relevance",
        ),
        reverse=True,
    )

elif sort_option == "Newest":

    filtered_papers.sort(
        key=lambda record: (
            record.get(
                "metadata",
                {},
            ).get(
                "publication_date",
                "",
            )
        ),
        reverse=True,
    )


# ---------------------------------------------------------
# Results summary
# ---------------------------------------------------------

st.markdown(
    f"### {len(filtered_papers)} studies"
)


# ---------------------------------------------------------
# Paper cards
# ---------------------------------------------------------

for record in filtered_papers[:100]:

    metadata = record.get(
        "metadata",
        {},
    )

    appraisal = record.get(
        "appraisal",
        {},
    )

    statistics = record.get(
        "statistics",
        {},
    )

    translation = record.get(
        "clinical_translation",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    if not isinstance(
        appraisal,
        dict,
    ):
        appraisal = {}

    if not isinstance(
        statistics,
        dict,
    ):
        statistics = {}

    if not isinstance(
        translation,
        dict,
    ):
        translation = {}

    title = metadata.get(
        "title",
        "Untitled paper",
    )

    journal = metadata.get(
        "journal",
        "",
    )

    publication_date = metadata.get(
        "publication_date",
        "",
    )

    study_design = appraisal.get(
        "study_design",
        "Unknown design",
    )

    evidence_scores = appraisal.get(
        "scores",
        {},
    )

    statistics_scores = statistics.get(
        "scores",
        {},
    )

    if not isinstance(
        evidence_scores,
        dict,
    ):
        evidence_scores = {}

    if not isinstance(
        statistics_scores,
        dict,
    ):
        statistics_scores = {}

    evidence_score = evidence_scores.get(
        "overall_evidence",
        0,
    )

    relevance_score = evidence_scores.get(
        "practitioner_relevance",
        0,
    )

    statistics_score = statistics_scores.get(
        "overall_statistics",
        0,
    )

    readiness = translation.get(
        "practice_readiness",
        "Unknown",
    )

    clinical_area = translation.get(
        "clinical_area",
        "",
    )

    with st.container(
        border=True
    ):

        top_left, top_right = st.columns(
            [5, 1]
        )

        with top_left:

            if clinical_area:
                st.caption(
                    clinical_area
                )

            st.markdown(
                f"### {title}"
            )

            citation_bits = [
                journal,
                study_design,
                publication_date,
            ]

            st.caption(
                " · ".join(
                    bit
                    for bit in citation_bits
                    if bit
                )
            )

        with top_right:

            st.metric(
                "Evidence",
                evidence_score,
            )

        c1, c2, c3 = st.columns(
            3
        )

        c1.metric(
            "Statistics",
            statistics_score,
        )

        c2.metric(
            "Relevance",
            relevance_score,
        )

        c3.metric(
            "Readiness",
            readiness,
        )

        takeaway = translation.get(
            "practitioner_takeaway",
            "",
        )

        if takeaway:

            st.markdown(
                "**Clinical takeaway**"
            )

            st.write(
                takeaway
            )

        with st.expander(
            "View evidence details"
        ):

            st.markdown(
                "**Population**"
            )

            st.write(
                translation.get(
                    "population",
                    "Not clearly reported.",
                )
            )

            st.markdown(
                "**Intervention / Exposure**"
            )

            st.write(
                translation.get(
                    "intervention_or_exposure",
                    "Not clearly reported.",
                )
            )

            st.markdown(
                "**Outcomes**"
            )

            outcomes = translation.get(
                "clinically_relevant_outcomes",
                [],
            )

            if outcomes:

                for outcome in outcomes:
                    st.write(
                        f"• {outcome}"
                    )

            else:
                st.write(
                    "No standardized outcomes identified."
                )

            st.markdown(
                "**Major cautions**"
            )

            cautions = translation.get(
                "major_cautions",
                [],
            )

            if cautions:

                for caution in cautions:
                    st.write(
                        f"• {caution}"
                    )

            else:
                st.write(
                    "No major abstract-level cautions flagged."
                )

            abstract = metadata.get(
                "abstract",
                "",
            )

            if abstract:

                st.markdown(
                    "**Abstract**"
                )

                st.write(
                    abstract
                )

        pubmed_url = metadata.get(
            "pubmed_url",
            "",
        )

        if pubmed_url:

            st.link_button(
                "Open in PubMed ↗",
                pubmed_url,
            )
