import json
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Clinical Problems",
    page_icon="🩺",
    layout="wide",
)


# ---------------------------------------------------------
# Load shared CSS
# ---------------------------------------------------------

STYLE_PATH = Path("assets/style.css")

if STYLE_PATH.exists():
    with STYLE_PATH.open("r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Load evidence database
# ---------------------------------------------------------

def load_json(path):
    path = Path(path)

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


evidence_db = load_json(
    "data/evidence_database.json"
)


# ---------------------------------------------------------
# Build problem index
# ---------------------------------------------------------

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

    return (
        translation.get(
            "clinical_area"
        )
        or "Other"
    )


problem_counts = {}

for record in evidence_db:
    problem = extract_problem(
        record
    )

    if problem not in problem_counts:
        problem_counts[
            problem
        ] = []

    problem_counts[
        problem
    ].append(
        record
    )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        CLINICAL INTELLIGENCE
    </div>

    <h1 class="hero-title">
        What <span>problems</span> is research trying to solve?
    </h1>

    <p class="hero-subtitle">
        Explore the clinical challenges receiving the most research
        attention, the interventions being tested, and where uncertainty
        remains.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Search + filters
# ---------------------------------------------------------

search_col, sort_col = st.columns(
    [3, 1]
)

with search_col:
    search = st.text_input(
        "Search problems",
        placeholder=(
            "Patellar tendinopathy, RED-S, ACL, "
            "explosive performance..."
        ),
        label_visibility="collapsed",
    )

with sort_col:
    sort_option = st.selectbox(
        "Sort",
        [
            "Most studied",
            "Alphabetical",
        ],
        label_visibility="collapsed",
    )


# ---------------------------------------------------------
# Filter problems
# ---------------------------------------------------------

problems = list(
    problem_counts.items()
)

if search:
    query = search.lower()

    problems = [
        (
            problem,
            papers,
        )
        for (
            problem,
            papers,
        ) in problems
        if query in problem.lower()
    ]

if sort_option == "Most studied":
    problems.sort(
        key=lambda item: len(
            item[1]
        ),
        reverse=True,
    )

else:
    problems.sort(
        key=lambda item: item[0]
    )


# ---------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------

total_problems = len(
    problem_counts
)

total_papers = len(
    evidence_db
)

avg_per_problem = (
    round(
        total_papers
        / total_problems,
        1,
    )
    if total_problems
    else 0
)

m1, m2, m3 = st.columns(3)

m1.metric(
    "Clinical Problems",
    total_problems,
)

m2.metric(
    "Indexed Papers",
    total_papers,
)

m3.metric(
    "Average Papers / Problem",
    avg_per_problem,
)


st.markdown("## Clinical Problems")


# ---------------------------------------------------------
# Problem cards
# ---------------------------------------------------------

columns_per_row = 3

for i in range(
    0,
    len(problems),
    columns_per_row,
):

    cols = st.columns(
        columns_per_row
    )

    row = problems[
        i : i + columns_per_row
    ]

    for col, (
        problem,
        papers,
    ) in zip(
        cols,
        row,
    ):

        with col:

            paper_count = len(
                papers
            )

            evidence_scores = []

            practice_informing = 0

            full_text_needed = 0

            interventions = set()

            for paper in papers:

                appraisal = paper.get(
                    "appraisal",
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
                        score = scores.get(
                            "overall_evidence"
                        )

                        if isinstance(
                            score,
                            (int, float),
                        ):
                            evidence_scores.append(
                                score
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

                    intervention = translation.get(
                        "intervention_or_exposure"
                    )

                    if (
                        isinstance(
                            intervention,
                            str,
                        )
                        and intervention
                        and "not clearly" not in intervention.lower()
                    ):
                        interventions.add(
                            intervention
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

            top_interventions = list(
                interventions
            )[:3]

            intervention_text = (
                " · ".join(
                    top_interventions
                )
                if top_interventions
                else "Interventions emerging"
            )

            st.markdown(
                f"""
                <div class="clinical-problem-card">

                    <div class="clinical-problem-label">
                        CLINICAL PROBLEM
                    </div>

                    <div class="clinical-problem-title">
                        {problem}
                    </div>

                    <div class="clinical-problem-study-count">
                        {paper_count} studies
                    </div>

                    <div class="clinical-problem-metrics">

                        <div>
                            <div class="clinical-problem-number">
                                {average_evidence}
                            </div>
                            <div class="clinical-problem-small">
                                Avg Evidence
                            </div>
                        </div>

                        <div>
                            <div class="clinical-problem-number">
                                {practice_informing}
                            </div>
                            <div class="clinical-problem-small">
                                Practice Informing
                            </div>
                        </div>

                        <div>
                            <div class="clinical-problem-number">
                                {full_text_needed}
                            </div>
                            <div class="clinical-problem-small">
                                Needs Review
                            </div>
                        </div>

                    </div>

                    <div class="clinical-problem-interventions">
                        {intervention_text}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Explore problem →",
                key=f"problem_{i}_{problem}",
                use_container_width=True,
            ):
                st.session_state[
                    "selected_problem"
                ] = problem

                st.switch_page(
                    "pages/2_Problem_Detail.py"
                )
