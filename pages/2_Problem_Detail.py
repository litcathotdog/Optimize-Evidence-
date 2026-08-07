import json
from collections import Counter
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Problem Detail",
    page_icon="🧩",
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

knowledge_graph = load_json(
    "data/knowledge_graph.json",
    {},
)


# ---------------------------------------------------------
# Selected problem
# ---------------------------------------------------------

selected_problem = st.session_state.get(
    "selected_problem",
    None,
)

if not selected_problem:
    st.warning(
        "No clinical problem selected yet."
    )

    if st.button("← Back to Clinical Problems"):
        st.switch_page(
            "pages/1_Clinical_Problems.py"
        )

    st.stop()


# ---------------------------------------------------------
# Filter records
# ---------------------------------------------------------

def get_clinical_area(record):
    translation = record.get(
        "clinical_translation",
        {},
    )

    if not isinstance(
        translation,
        dict,
    ):
        return ""

    return translation.get(
        "clinical_area",
        "",
    )


papers = [
    paper
    for paper in evidence_db
    if get_clinical_area(paper)
    == selected_problem
]


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

if st.button("← Clinical Problems"):
    st.switch_page(
        "pages/1_Clinical_Problems.py"
    )


st.markdown(
    f"""
    <div class="hero-eyebrow">
        CLINICAL PROBLEM
    </div>

    <h1 class="hero-title">
        {selected_problem}
    </h1>

    <p class="hero-subtitle">
        What researchers are trying to solve, what interventions
        are being tested, and where uncertainty remains.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Metrics
# ---------------------------------------------------------

paper_count = len(
    papers
)

evidence_scores = []
statistics_scores = []
practice_informing = 0
full_text_needed = 0


for paper in papers:

    appraisal = paper.get(
        "appraisal",
        {},
    )

    statistics = paper.get(
        "statistics",
        {},
    )

    translation = paper.get(
        "clinical_translation",
        {},
    )

    if isinstance(
        appraisal,
        dict,
    ):
        scores = appraisal.get(
            "scores",
            {},
        )

        if isinstance(
            scores,
            dict,
        ):
            value = scores.get(
                "overall_evidence"
            )

            if isinstance(
                value,
                (int, float),
            ):
                evidence_scores.append(
                    value
                )

    if isinstance(
        statistics,
        dict,
    ):
        scores = statistics.get(
            "scores",
            {},
        )

        if isinstance(
            scores,
            dict,
        ):
            value = scores.get(
                "overall_statistics"
            )

            if isinstance(
                value,
                (int, float),
            ):
                statistics_scores.append(
                    value
                )

    if isinstance(
        translation,
        dict,
    ):
        if (
            translation.get(
                "practice_readiness"
            )
            == "Practice-informing"
        ):
            practice_informing += 1

        if translation.get(
            "requires_full_text_review",
            False,
        ):
            full_text_needed += 1


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


avg_statistics = (
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


m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Studies",
    paper_count,
)

m2.metric(
    "Evidence Score",
    avg_evidence,
)

m3.metric(
    "Statistics Score",
    avg_statistics,
)

m4.metric(
    "Practice-Informing",
    practice_informing,
)


# ---------------------------------------------------------
# What researchers are trying to solve
# ---------------------------------------------------------

st.markdown(
    "## What researchers are trying to solve"
)

outcome_counter = Counter()


for paper in papers:

    translation = paper.get(
        "clinical_translation",
        {},
    )

    if not isinstance(
        translation,
        dict,
    ):
        continue

    outcomes = translation.get(
        "clinically_relevant_outcomes",
        [],
    )

    if not isinstance(
        outcomes,
        list,
    ):
        continue

    for outcome in outcomes:
        if isinstance(
            outcome,
            str,
        ):
            outcome_counter[
                outcome
            ] += 1


if outcome_counter:

    cols = st.columns(
        min(
            4,
            len(
                outcome_counter
            ),
        )
    )

    for col, (
        outcome,
        count,
    ) in zip(
        cols,
        outcome_counter.most_common(
            4
        ),
    ):

        with col:
            st.markdown(
                f"""
                <div class="solution-card">
                    <div class="solution-title">
                        {outcome}
                    </div>

                    <div class="solution-count">
                        {count} studies
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

else:
    st.info(
        "Outcome patterns will appear after the evidence pipeline runs."
    )


# ---------------------------------------------------------
# Interventions
# ---------------------------------------------------------

st.markdown(
    "## Interventions being tested"
)

intervention_counter = Counter()


for paper in papers:

    translation = paper.get(
        "clinical_translation",
        {},
    )

    if not isinstance(
        translation,
        dict,
    ):
        continue

    intervention = translation.get(
        "intervention_or_exposure",
        "",
    )

    if (
        isinstance(
            intervention,
            str,
        )
        and intervention
        and "not clearly" not in intervention.lower()
        and "not reliably" not in intervention.lower()
    ):
        intervention_counter[
            intervention
        ] += 1


if intervention_counter:

    for intervention, count in (
        intervention_counter.most_common(
            10
        )
    ):

        st.markdown(
            f"""
            <div class="intervention-row">

                <div>
                    <div class="intervention-name">
                        {intervention}
                    </div>

                    <div class="intervention-sub">
                        {count} studies
                    </div>
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

else:
    st.info(
        "No standardized interventions identified yet."
    )


# ---------------------------------------------------------
# Evidence disagreement
# ---------------------------------------------------------

st.markdown(
    "## Where the evidence disagrees"
)

matching_synthesis = None


for synthesis in knowledge_graph.get(
    "evidence_synthesis",
    [],
):

    if not isinstance(
        synthesis,
        dict,
    ):
        continue

    if (
        synthesis.get(
            "concept"
        )
        == selected_problem
    ):
        matching_synthesis = synthesis
        break


if matching_synthesis:

    directions = matching_synthesis.get(
        "result_direction",
        {},
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Favorable",
        directions.get(
            "favorable",
            0,
        ),
    )

    c2.metric(
        "Neutral",
        directions.get(
            "neutral",
            0,
        ),
    )

    c3.metric(
        "Unfavorable",
        directions.get(
            "unfavorable",
            0,
        ),
    )

    c4.metric(
        "Unclear",
        directions.get(
            "unclear",
            0,
        ),
    )

else:
    st.info(
        "No disagreement summary is available yet."
    )


# ---------------------------------------------------------
# Evidence gaps
# ---------------------------------------------------------

st.markdown(
    "## What we still don't know"
)

gaps = []


for gap in knowledge_graph.get(
    "evidence_gaps",
    [],
):

    if not isinstance(
        gap,
        dict,
    ):
        continue

    if (
        gap.get(
            "concept"
        )
        == selected_problem
    ):
        gaps.append(
            gap
        )


if gaps:

    for gap in gaps:

        reasons = gap.get(
            "reasons",
            [],
        )

        for reason in reasons:
            st.warning(
                reason
            )

else:
    st.info(
        "No problem-specific evidence gaps are currently flagged."
    )


# ---------------------------------------------------------
# Specialist perspectives
# ---------------------------------------------------------

st.markdown(
    "## Specialist perspectives"
)

specialist_reviews = {
    "regenerative_medicine": [],
    "sports_performance": [],
    "biomechanics": [],
    "womens_athlete_health": [],
}


for paper in papers:

    specialties = paper.get(
        "specialties",
        {},
    )

    if not isinstance(
        specialties,
        dict,
    ):
        continue

    for specialty in specialist_reviews:

        review = specialties.get(
            specialty,
            {},
        )

        if not isinstance(
            review,
            dict,
        ):
            continue

        takeaway = review.get(
            "specialist_takeaway",
            "",
        )

        if (
            review.get(
                "reviewed",
                False,
            )
            and takeaway
        ):
            specialist_reviews[
                specialty
            ].append(
                takeaway
            )


specialist_labels = {
    "regenerative_medicine": (
        "Atlas",
        "Regenerative Medicine",
    ),
    "sports_performance": (
        "Vector",
        "Sports Performance",
    ),
    "biomechanics": (
        "Newton",
        "Biomechanics",
    ),
    "womens_athlete_health": (
        "Athena",
        "Women's Athlete Health",
    ),
}


cols = st.columns(4)


for col, specialty in zip(
    cols,
    specialist_reviews,
):

    name, role = specialist_labels[
        specialty
    ]

    takeaways = specialist_reviews[
        specialty
    ]

    with col:

        st.markdown(
            f"### {name}"
        )

        st.caption(
            role
        )

        if takeaways:

            st.write(
                takeaways[0]
            )

        else:
            st.write(
                "No major specialty-specific insight yet."
            )


# ---------------------------------------------------------
# Highest-priority papers
# ---------------------------------------------------------

st.markdown(
    "## Highest-priority papers"
)


def priority_score(paper):

    appraisal = paper.get(
        "appraisal",
        {},
    )

    translation = paper.get(
        "clinical_translation",
        {},
    )

    scores = (
        appraisal.get(
            "scores",
            {},
        )
        if isinstance(
            appraisal,
            dict,
        )
        else {}
    )

    return (
        scores.get(
            "overall_evidence",
            0,
        )
        * 0.6
        + translation.get(
            "translation_priority",
            0,
        )
        * 0.4
    )


ranked_papers = sorted(
    papers,
    key=priority_score,
    reverse=True,
)


for paper in ranked_papers[:10]:

    metadata = paper.get(
        "metadata",
        {},
    )

    appraisal = paper.get(
        "appraisal",
        {},
    )

    translation = paper.get(
        "clinical_translation",
        {},
    )

    title = metadata.get(
        "title",
        "Untitled paper",
    )

    with st.expander(
        title
    ):

        st.caption(
            " · ".join(
                value
                for value in [
                    metadata.get(
                        "journal",
                        "",
                    ),
                    appraisal.get(
                        "study_design",
                        "",
                    ),
                    metadata.get(
                        "publication_date",
                        "",
                    ),
                ]
                if value
            )
        )

        st.write(
            translation.get(
                "practitioner_takeaway",
                "",
            )
        )

        c1, c2, c3 = st.columns(3)

        scores = appraisal.get(
            "scores",
            {},
        )

        c1.metric(
            "Evidence",
            scores.get(
                "overall_evidence",
                0,
            ),
        )

        statistics = paper.get(
            "statistics",
            {},
        )

        statistics_scores = (
            statistics.get(
                "scores",
                {},
            )
            if isinstance(
                statistics,
                dict,
            )
            else {}
        )

        c2.metric(
            "Statistics",
            statistics_scores.get(
                "overall_statistics",
                0,
            ),
        )

        c3.metric(
            "Relevance",
            scores.get(
                "practitioner_relevance",
                0,
            ),
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
