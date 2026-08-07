import json
from collections import Counter
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Evidence Gaps",
    page_icon="⚠️",
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


knowledge_graph = load_json(
    "data/knowledge_graph.json",
    {},
)

evidence_db = load_json(
    "data/evidence_database.json",
    [],
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def safe_dict(value):
    return value if isinstance(value, dict) else {}


def safe_list(value):
    return value if isinstance(value, list) else []


gaps = safe_list(
    knowledge_graph.get(
        "evidence_gaps"
    )
)

syntheses = safe_list(
    knowledge_graph.get(
        "evidence_synthesis"
    )
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        RESEARCH OPPORTUNITIES
    </div>

    <h1 class="hero-title">
        Where is the <span>evidence missing?</span>
    </h1>

    <p class="hero-subtitle">
        Identify problems that remain poorly studied, clinically uncertain,
        methodologically inconsistent, or underrepresented in current research.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Summary metrics
# ---------------------------------------------------------

low_evidence = 0
conflicting = 0
limited_literature = 0
no_practice_informing = 0


for gap in gaps:

    if not isinstance(
        gap,
        dict,
    ):
        continue

    reasons = safe_list(
        gap.get(
            "reasons"
        )
    )

    reason_text = " ".join(
        str(reason).lower()
        for reason in reasons
    )

    if "low" in reason_text:
        low_evidence += 1

    if "conflict" in reason_text:
        conflicting += 1

    if (
        "few papers" in reason_text
        or "very few" in reason_text
    ):
        limited_literature += 1

    if "practice-informing" in reason_text:
        no_practice_informing += 1


m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Evidence Gaps",
    len(gaps),
)

m2.metric(
    "Limited Literature",
    limited_literature,
)

m3.metric(
    "Low Evidence",
    low_evidence,
)

m4.metric(
    "Conflicting Findings",
    conflicting,
)


# ---------------------------------------------------------
# Priority gaps
# ---------------------------------------------------------

st.markdown(
    "## Highest-Priority Gaps"
)


def gap_priority(gap):

    paper_count = gap.get(
        "paper_count",
        0,
    )

    reasons = safe_list(
        gap.get(
            "reasons"
        )
    )

    score = 0

    if paper_count <= 2:
        score += 4

    elif paper_count <= 5:
        score += 2

    reason_text = " ".join(
        str(reason).lower()
        for reason in reasons
    )

    if "low" in reason_text:
        score += 3

    if "conflict" in reason_text:
        score += 3

    if "practice-informing" in reason_text:
        score += 2

    return score


ranked_gaps = sorted(
    [
        gap
        for gap in gaps
        if isinstance(
            gap,
            dict,
        )
    ],
    key=gap_priority,
    reverse=True,
)


if ranked_gaps:

    for i in range(
        0,
        min(
            len(ranked_gaps),
            6,
        ),
        3,
    ):

        cols = st.columns(3)

        for col, gap in zip(
            cols,
            ranked_gaps[
                i : i + 3
            ],
        ):

            concept = gap.get(
                "concept",
                "Unknown",
            )

            concept_type = str(
                gap.get(
                    "concept_type",
                    "",
                )
            ).replace(
                "_",
                " ",
            ).title()

            paper_count = gap.get(
                "paper_count",
                0,
            )

            priority = gap_priority(
                gap
            )

            with col:

                st.markdown(
                    f"""
                    <div class="gap-card">

                        <div class="gap-priority">
                            PRIORITY {priority}
                        </div>

                        <div class="gap-title">
                            {concept}
                        </div>

                        <div class="gap-type">
                            {concept_type}
                        </div>

                        <div class="gap-study-count">
                            {paper_count} indexed studies
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                reasons = safe_list(
                    gap.get(
                        "reasons"
                    )
                )

                with st.expander(
                    "Why this is a gap"
                ):

                    for reason in reasons:
                        st.write(
                            f"• {reason}"
                        )

else:

    st.info(
        "No evidence gaps are currently flagged."
    )


# ---------------------------------------------------------
# Gap explorer
# ---------------------------------------------------------

st.markdown(
    "## Explore All Evidence Gaps"
)

gap_types = sorted(
    {
        str(
            gap.get(
                "concept_type",
                "",
            )
        )
        for gap in gaps
        if isinstance(
            gap,
            dict,
        )
        and gap.get(
            "concept_type"
        )
    }
)


type_filter = st.selectbox(
    "Concept type",
    [
        "All",
        *[
            gap_type.replace(
                "_",
                " ",
            ).title()
            for gap_type
            in gap_types
        ],
    ],
)


search = st.text_input(
    "Search gaps",
    placeholder=(
        "Female athletes, PRP formulation, "
        "return to sport, bone health..."
    ),
)


filtered_gaps = []

for gap in ranked_gaps:

    concept = str(
        gap.get(
            "concept",
            "",
        )
    )

    concept_type = str(
        gap.get(
            "concept_type",
            "",
        )
    )

    if (
        type_filter != "All"
        and concept_type.replace(
            "_",
            " ",
        ).title()
        != type_filter
    ):
        continue

    if (
        search
        and search.lower()
        not in json.dumps(
            gap
        ).lower()
    ):
        continue

    filtered_gaps.append(
        gap
    )


st.caption(
    f"{len(filtered_gaps)} gaps shown"
)


for gap in filtered_gaps:

    concept = gap.get(
        "concept",
        "Unknown",
    )

    reasons = safe_list(
        gap.get(
            "reasons"
        )
    )

    with st.expander(
        concept
    ):

        c1, c2 = st.columns(
            2
        )

        c1.metric(
            "Indexed Studies",
            gap.get(
                "paper_count",
                0,
            ),
        )

        c2.metric(
            "Gap Priority",
            gap_priority(
                gap
            ),
        )

        st.markdown(
            "**Why the evidence is incomplete**"
        )

        for reason in reasons:
            st.write(
                f"• {reason}"
            )


# ---------------------------------------------------------
# Common recurring problems in research
# ---------------------------------------------------------

st.markdown(
    "## Common Problems Across the Literature"
)

problem_counter = Counter()


for record in evidence_db:

    translation = safe_dict(
        record.get(
            "clinical_translation"
        )
    )

    statistics = safe_dict(
        record.get(
            "statistics"
        )
    )

    specialties = safe_dict(
        record.get(
            "specialties"
        )
    )

    cautions = safe_list(
        translation.get(
            "major_cautions"
        )
    )

    reporting_flags = safe_list(
        statistics.get(
            "reporting_flags"
        )
    )

    for issue in (
        cautions
        + reporting_flags
    ):

        issue = str(
            issue
        ).strip()

        if issue:
            problem_counter[
                issue
            ] += 1

    for specialty_data in specialties.values():

        if not isinstance(
            specialty_data,
            dict,
        ):
            continue

        flags = safe_list(
            specialty_data.get(
                "domain_flags"
            )
        )

        for issue in flags:

            issue = str(
                issue
            ).strip()

            if issue:
                problem_counter[
                    issue
                ] += 1


if problem_counter:

    for issue, count in (
        problem_counter.most_common(
            12
        )
    ):

        st.markdown(
            f"""
            <div class="recurring-problem-row">

                <div class="recurring-problem-main">
                    {issue}
                </div>

                <div class="recurring-problem-count">
                    Seen in {count} analyses
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.info(
        "Recurring methodological problems will appear after more papers are reviewed."
    )


# ---------------------------------------------------------
# Understudied topics
# ---------------------------------------------------------

st.markdown(
    "## Understudied Topics"
)

understudied = []

for synthesis in syntheses:

    if not isinstance(
        synthesis,
        dict,
    ):
        continue

    count = synthesis.get(
        "paper_count",
        0,
    )

    if (
        isinstance(
            count,
            int,
        )
        and count <= 3
    ):
        understudied.append(
            synthesis
        )


understudied.sort(
    key=lambda item: (
        item.get(
            "paper_count",
            0,
        ),
        item.get(
            "average_evidence_score",
            0,
        )
        or 0,
    )
)


if understudied:

    cols = st.columns(4)

    for col, item in zip(
        cols,
        understudied[:4],
    ):

        with col:

            st.markdown(
                f"""
                <div class="understudied-card">

                    <div class="understudied-label">
                        UNDERSTUDIED
                    </div>

                    <div class="understudied-title">
                        {item.get("concept", "Unknown")}
                    </div>

                    <div class="understudied-count">
                        {item.get("paper_count", 0)} papers
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

else:

    st.info(
        "No clearly understudied graph concepts are currently identified."
    )


# ---------------------------------------------------------
# Research opportunity framing
# ---------------------------------------------------------

st.markdown(
    "## Research Opportunities"
)

st.markdown(
    """
    The strongest opportunities are not necessarily the topics with
    the fewest publications.

    High-value research questions often sit at the intersection of:

    **High clinical importance**
    ×
    **High uncertainty**
    ×
    **Weak methodology**
    ×
    **Underrepresented populations**
    ×
    **Poorly standardized interventions**

    This page is designed to surface those intersections.
    """
)
