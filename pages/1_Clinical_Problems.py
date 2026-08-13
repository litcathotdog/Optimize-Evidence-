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

    if not isinstance(translation, dict):
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


def get_problem_metrics(papers):
    evidence_scores = []
    practice_informing = 0
    full_text_needed = 0
    interventions = []

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        appraisal = paper.get(
            "appraisal",
            {},
        )

        translation = paper.get(
            "clinical_translation",
            {},
        )

        # ---------------------------------------------
        # Evidence score
        # ---------------------------------------------

        if isinstance(appraisal, dict):

            scores = appraisal.get(
                "scores",
                {},
            )

            if isinstance(scores, dict):

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

        # ---------------------------------------------
        # Clinical translation
        # ---------------------------------------------

        if not isinstance(
            translation,
            dict,
        ):
            continue

        readiness = translation.get(
            "practice_readiness",
            "",
        )

        if readiness == "Practice-informing":
            practice_informing += 1

        if translation.get(
            "requires_full_text_review",
            False,
        ):
            full_text_needed += 1

        intervention = translation.get(
            "intervention_or_exposure",
            "",
        )

        if (
            isinstance(intervention, str)
            and intervention.strip()
            and "not clearly"
            not in intervention.lower()
        ):

            intervention = (
                intervention.strip()
            )

            if intervention not in interventions:
                interventions.append(
                    intervention
                )

    # ---------------------------------------------
    # Average evidence
    # ---------------------------------------------

    if evidence_scores:

        average_evidence = round(
            sum(evidence_scores)
            / len(evidence_scores),
            1,
        )

    else:
        average_evidence = 0

    return {
        "paper_count": len(papers),
        "average_evidence": average_evidence,
        "practice_informing": practice_informing,
        "full_text_needed": full_text_needed,
        "interventions": interventions[:3],
    }


# =========================================================
# BUILD PROBLEM INDEX
# =========================================================

problem_counts = {}

if isinstance(evidence_db, list):

    for record in evidence_db:

        if not isinstance(record, dict):
            continue

        problem = extract_problem(
            record
        )

        if problem not in problem_counts:
            problem_counts[problem] = []

        problem_counts[
            problem
        ].append(
            record
        )


# =========================================================
# HEADER
# =========================================================

st.caption(
    "CLINICAL INTELLIGENCE"
)

st.title(
    "What problems is research trying to solve?"
)

st.write(
    "Explore the clinical challenges receiving the most research "
    "attention, the interventions being tested, and where "
    "uncertainty remains."
)

st.write("")


# =========================================================
# SEARCH + SORT
# =========================================================

search_col, sort_col = st.columns(
    [3, 1],
    gap="medium",
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
            "Highest evidence",
            "Most practice-informing",
            "Alphabetical",
        ],
        label_visibility="collapsed",
    )


# =========================================================
# PREPARE PROBLEM DATA
# =========================================================

problems = []

for problem, papers in (
    problem_counts.items()
):

    metrics = get_problem_metrics(
        papers
    )

    problems.append(
        {
            "name": problem,
            "papers": papers,
            **metrics,
        }
    )


# =========================================================
# SEARCH FILTER
# =========================================================

if search:

    query = search.lower().strip()

    problems = [
        problem
        for problem in problems
        if (
            query
            in problem["name"].lower()
            or any(
                query
                in intervention.lower()
                for intervention
                in problem[
                    "interventions"
                ]
            )
        )
    ]


# =========================================================
# SORT
# =========================================================

if sort_option == "Most studied":

    problems.sort(
        key=lambda item: (
            item["paper_count"]
        ),
        reverse=True,
    )


elif (
    sort_option
    == "Highest evidence"
):

    problems.sort(
        key=lambda item: (
            item["average_evidence"]
        ),
        reverse=True,
    )


elif (
    sort_option
    == "Most practice-informing"
):

    problems.sort(
        key=lambda item: (
            item[
                "practice_informing"
            ]
        ),
        reverse=True,
    )


else:

    problems.sort(
        key=lambda item: (
            item["name"].lower()
        )
    )


# =========================================================
# SUMMARY METRICS
# =========================================================

total_problems = len(
    problem_counts
)

total_papers = (
    len(evidence_db)
    if isinstance(
        evidence_db,
        list,
    )
    else 0
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

practice_informing_total = sum(
    problem[
        "practice_informing"
    ]
    for problem in problems
)


m1, m2, m3, m4 = st.columns(
    4,
    gap="medium",
)

with m1:

    st.metric(
        "Clinical Problems",
        total_problems,
        border=True,
    )


with m2:

    st.metric(
        "Indexed Papers",
        total_papers,
        border=True,
    )


with m3:

    st.metric(
        "Average Papers / Problem",
        avg_per_problem,
        border=True,
    )


with m4:

    st.metric(
        "Practice-Informing",
        practice_informing_total,
        border=True,
    )


st.write("")


# =========================================================
# RESULTS HEADER
# =========================================================

results_left, results_right = (
    st.columns(
        [4, 1],
    )
)

with results_left:

    st.subheader(
        "Clinical Problems"
    )


with results_right:

    st.caption(
        f"{len(problems)} shown"
    )


# =========================================================
# EMPTY STATE
# =========================================================

if not problems:

    st.info(
        "No clinical problems match your search."
    )


# =========================================================
# PROBLEM CARDS
# =========================================================

columns_per_row = 3


for row_start in range(
    0,
    len(problems),
    columns_per_row,
):

    cols = st.columns(
        columns_per_row,
        gap="medium",
    )

    row = problems[
        row_start:
        row_start + columns_per_row
    ]


    for col, problem in zip(
        cols,
        row,
    ):

        with col:

            with st.container(
                border=True,
            ):

                # -------------------------------------
                # Problem heading
                # -------------------------------------

                st.caption(
                    "CLINICAL PROBLEM"
                )

                st.markdown(
                    f"### {problem['name']}"
                )

                st.caption(
                    f"{problem['paper_count']} studies"
                )

                st.write("")

                # -------------------------------------
                # Evidence metrics
                # -------------------------------------

                score_col, practice_col = (
                    st.columns(2)
                )

                with score_col:

                    st.metric(
                        "Avg Evidence",
                        problem[
                            "average_evidence"
                        ],
                    )

                with practice_col:

                    st.metric(
                        "Practice Informing",
                        problem[
                            "practice_informing"
                        ],
                    )

                st.caption(
                    f"🔎 {problem['full_text_needed']} "
                    "papers need full-text review"
                )

                st.write("")

                # -------------------------------------
                # Interventions
                # -------------------------------------

                st.markdown(
                    "**Interventions being studied**"
                )

                if problem[
                    "interventions"
                ]:

                    for intervention in (
                        problem[
                            "interventions"
                        ]
                    ):

                        st.caption(
                            f"• {intervention}"
                        )

                else:

                    st.caption(
                        "Interventions still emerging"
                    )

                st.write("")

                # -------------------------------------
                # Open problem
                # -------------------------------------

                if st.button(
                    "Explore problem →",
                    key=(
                        "problem_"
                        + str(row_start)
                        + "_"
                        + problem["name"]
                    ),
                    width="stretch",
                ):

                    st.session_state[
                        "selected_problem"
                    ] = problem[
                        "name"
                    ]

                    st.switch_page(
                        "pages/2_Problem_Detail.py"
                    )
