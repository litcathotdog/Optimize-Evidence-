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

def extract_problem(record):
    translation = record.get(
        "clinical_translation",
        {},
    )

    if not isinstance(
        translation,
        dict,
    ):
        return "Other"

    problem = translation.get(
        "clinical_area"
    )

    if (
        not isinstance(problem, str)
        or not problem.strip()
    ):
        return "Other"

    return problem.strip()


def get_metadata(record):
    metadata = record.get(
        "metadata",
        {},
    )

    if isinstance(metadata, dict):
        return metadata

    return {}


def get_appraisal(record):
    appraisal = record.get(
        "appraisal",
        {},
    )

    if isinstance(appraisal, dict):
        return appraisal

    return {}


def get_statistics(record):
    statistics = record.get(
        "statistics",
        {},
    )

    if isinstance(statistics, dict):
        return statistics

    return {}


def get_translation(record):
    translation = record.get(
        "clinical_translation",
        {},
    )

    if isinstance(translation, dict):
        return translation

    return {}


def get_overall_evidence(record):
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

    score = scores.get(
        "overall_evidence",
        0,
    )

    if isinstance(
        score,
        (int, float),
    ):
        return score

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

    score = scores.get(
        "overall_statistics",
        0,
    )

    if isinstance(
        score,
        (int, float),
    ):
        return score

    return 0


def get_confidence(record):
    translation = get_translation(
        record
    )

    for key in [
        "clinical_confidence",
        "confidence",
        "evidence_confidence",
    ]:
        value = translation.get(
            key
        )

        if isinstance(
            value,
            str,
        ) and value.strip():
            return value.strip()

    return "Unclear"


def get_practice_readiness(record):
    translation = get_translation(
        record
    )

    value = translation.get(
        "practice_readiness",
        "",
    )

    if isinstance(
        value,
        str,
    ) and value.strip():
        return value.strip()

    return "Not classified"


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


def get_flags(record):
    flags = []

    appraisal = get_appraisal(
        record
    )

    statistics = get_statistics(
        record
    )

    translation = get_translation(
        record
    )

    appraisal_flags = appraisal.get(
        "flags",
        [],
    )

    if isinstance(
        appraisal_flags,
        list,
    ):
        flags.extend(
            str(flag)
            for flag in appraisal_flags
            if flag
        )

    stats_flags = statistics.get(
        "reporting_flags",
        [],
    )

    if isinstance(
        stats_flags,
        list,
    ):
        flags.extend(
            str(flag)
            for flag in stats_flags
            if flag
        )

    if translation.get(
        "requires_full_text_review",
        False,
    ):
        flags.append(
            "Full-text review recommended before applying findings."
        )

    deduplicated = []

    for flag in flags:
        if flag not in deduplicated:
            deduplicated.append(
                flag
            )

    return deduplicated


def sort_papers(records):
    return sorted(
        records,
        key=lambda record: (
            get_overall_evidence(
                record
            ),
            get_statistics_score(
                record
            ),
        ),
        reverse=True,
    )


# =========================================================
# SELECTED PROBLEM
# =========================================================

selected_problem = (
    st.session_state.get(
        "selected_problem"
    )
)


if not selected_problem:

    st.warning(
        "No clinical problem has been selected yet."
    )

    st.page_link(
        "pages/1_Clinical_Problems.py",
        label="← Back to Clinical Problems",
    )

    st.stop()


# =========================================================
# MATCH PAPERS
# =========================================================

problem_papers = []

if isinstance(
    evidence_db,
    list,
):

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        if extract_problem(
            record
        ) == selected_problem:

            problem_papers.append(
                record
            )


problem_papers = sort_papers(
    problem_papers
)


# =========================================================
# HEADER
# =========================================================

st.page_link(
    "pages/1_Clinical_Problems.py",
    label="← Back to Clinical Problems",
)

st.caption(
    "CLINICAL PROBLEM"
)

st.title(
    selected_problem
)

st.write(
    "Evidence synthesis, interventions, methodological quality, "
    "practice relevance, and remaining uncertainty."
)

st.write("")


# =========================================================
# SUMMARY METRICS
# =========================================================

paper_count = len(
    problem_papers
)

evidence_scores = [
    get_overall_evidence(
        record
    )
    for record in problem_papers
    if get_overall_evidence(
        record
    ) > 0
]

statistics_scores = [
    get_statistics_score(
        record
    )
    for record in problem_papers
    if get_statistics_score(
        record
    ) > 0
]

practice_informing = sum(
    1
    for record
    in problem_papers
    if get_practice_readiness(
        record
    )
    == "Practice-informing"
)

needs_full_text = sum(
    1
    for record
    in problem_papers
    if get_translation(
        record
    ).get(
        "requires_full_text_review",
        False,
    )
)


average_evidence = (
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

average_statistics = (
    round(
        sum(
            statistics_scores
        )
        / len(
            statistics_scores
        ),
        1,
    )
    if statistics_scores
    else 0
)


m1, m2, m3, m4, m5 = st.columns(
    5,
    gap="medium",
)

with m1:
    st.metric(
        "Studies",
        paper_count,
        border=True,
    )

with m2:
    st.metric(
        "Avg Evidence",
        average_evidence,
        border=True,
    )

with m3:
    st.metric(
        "Avg Statistics",
        average_statistics,
        border=True,
    )

with m4:
    st.metric(
        "Practice-Informing",
        practice_informing,
        border=True,
    )

with m5:
    st.metric(
        "Needs Full Text",
        needs_full_text,
        border=True,
    )


st.write("")


# =========================================================
# EMPTY STATE
# =========================================================

if not problem_papers:

    st.info(
        "No papers are currently indexed for this clinical problem."
    )

    st.stop()


# =========================================================
# INTERVENTION SUMMARY
# =========================================================

st.subheader(
    "Interventions being studied"
)

intervention_counts = {}

for record in problem_papers:

    intervention = get_intervention(
        record
    )

    if (
        intervention
        == "Not clearly identified"
    ):
        continue

    intervention_counts[
        intervention
    ] = (
        intervention_counts.get(
            intervention,
            0,
        )
        + 1
    )


sorted_interventions = sorted(
    intervention_counts.items(),
    key=lambda item: item[1],
    reverse=True,
)


if sorted_interventions:

    intervention_cols = st.columns(
        min(
            4,
            len(
                sorted_interventions
            ),
        ),
        gap="medium",
    )

    for col, (
        intervention,
        count,
    ) in zip(
        intervention_cols,
        sorted_interventions[:4],
    ):

        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"**{intervention}**"
                )

                st.metric(
                    "Papers",
                    count,
                )

else:

    st.info(
        "No clearly identified interventions are available yet."
    )


st.write("")


# =========================================================
# BEST AVAILABLE EVIDENCE
# =========================================================

st.subheader(
    "Best available evidence"
)

top_papers = (
    problem_papers[:3]
)

for index, record in enumerate(
    top_papers,
    start=1,
):

    metadata = get_metadata(
        record
    )

    title = metadata.get(
        "title",
        "Untitled paper",
    )

    journal = metadata.get(
        "journal",
        "",
    )

    year = (
        metadata.get(
            "publication_year"
        )
        or metadata.get(
            "year"
        )
        or ""
    )

    evidence_score = (
        get_overall_evidence(
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

    takeaway = get_takeaway(
        record
    )

    with st.container(
        border=True,
    ):

        st.caption(
            f"TOP EVIDENCE #{index}"
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
                "Practice Readiness",
                readiness,
            )

        st.markdown(
            "**Practitioner takeaway**"
        )

        st.write(
            takeaway
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


st.write("")


# =========================================================
# ALL PAPERS
# =========================================================

st.subheader(
    "All indexed papers"
)

for index, record in enumerate(
    problem_papers,
    start=1,
):

    metadata = get_metadata(
        record
    )

    title = metadata.get(
        "title",
        "Untitled paper",
    )

    with st.expander(
        f"{index}. {title}"
    ):

        journal = metadata.get(
            "journal",
            "",
        )

        year = (
            metadata.get(
                "publication_year"
            )
            or metadata.get(
                "year"
            )
            or ""
        )

        study_design = metadata.get(
            "study_design",
            "",
        )

        if not study_design:

            appraisal = get_appraisal(
                record
            )

            study_design = appraisal.get(
                "study_design",
                "",
            )

        source_parts = []

        if journal:
            source_parts.append(
                journal
            )

        if year:
            source_parts.append(
                str(year)
            )

        if study_design:
            source_parts.append(
                str(
                    study_design
                )
            )

        if source_parts:

            st.caption(
                " • ".join(
                    source_parts
                )
            )

        metric_1, metric_2, metric_3 = (
            st.columns(3)
        )

        with metric_1:

            st.metric(
                "Evidence Score",
                get_overall_evidence(
                    record
                ),
            )

        with metric_2:

            st.metric(
                "Statistics Score",
                get_statistics_score(
                    record
                ),
            )

        with metric_3:

            st.metric(
                "Confidence",
                get_confidence(
                    record
                ),
            )

        intervention = get_intervention(
            record
        )

        st.markdown(
            "**Intervention / exposure**"
        )

        st.write(
            intervention
        )

        st.markdown(
            "**Practitioner takeaway**"
        )

        st.write(
            get_takeaway(
                record
            )
        )

        flags = get_flags(
            record
        )

        if flags:

            st.markdown(
                "**Cautions / review flags**"
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
