import json
from collections import Counter
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Statistics Review",
    page_icon="Σ",
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
# Helpers
# ---------------------------------------------------------

def safe_dict(value):
    return value if isinstance(value, dict) else {}


def safe_list(value):
    return value if isinstance(value, list) else []


def safe_number(value, default=0):
    return value if isinstance(value, (int, float)) else default


# ---------------------------------------------------------
# Collect reviewed papers
# ---------------------------------------------------------

reviewed_papers = []

for record in evidence_db:

    stats = safe_dict(
        record.get(
            "statistics"
        )
    )

    if stats:
        reviewed_papers.append(
            (
                record,
                stats,
            )
        )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        EULER'S LAB
    </div>

    <h1 class="hero-title">
        Statistical <span>Review</span>
    </h1>

    <p class="hero-subtitle">
        Explore how clearly studies report effect estimates, confidence
        intervals, statistical models, sample sizes, precision, and other
        signals of methodological rigor.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Top metrics
# ---------------------------------------------------------

confidence_counter = Counter()

flagged_papers = 0
full_text_needed = 0
statistics_scores = []


for _, stats in reviewed_papers:

    confidence = stats.get(
        "statistical_confidence"
    )

    if confidence:
        confidence_counter[
            confidence
        ] += 1

    flags = safe_list(
        stats.get(
            "reporting_flags"
        )
    )

    if flags:
        flagged_papers += 1

    if stats.get(
        "requires_full_text_statistical_review",
        False,
    ):
        full_text_needed += 1

    scores = safe_dict(
        stats.get(
            "scores"
        )
    )

    overall = scores.get(
        "overall_statistics"
    )

    if isinstance(
        overall,
        (int, float),
    ):
        statistics_scores.append(
            overall
        )


average_statistics = (
    round(
        sum(statistics_scores)
        / len(statistics_scores),
        1,
    )
    if statistics_scores
    else 0
)


m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(
    "Papers Reviewed",
    len(reviewed_papers),
)

m2.metric(
    "Avg Statistics",
    average_statistics,
)

m3.metric(
    "High Confidence",
    confidence_counter.get(
        "High",
        0,
    ),
)

m4.metric(
    "Flagged Papers",
    flagged_papers,
)

m5.metric(
    "Needs Full Text",
    full_text_needed,
)


# ---------------------------------------------------------
# Confidence overview
# ---------------------------------------------------------

st.markdown(
    "## Statistical Confidence"
)

confidence_cols = st.columns(4)

confidence_categories = [
    "High",
    "Moderate",
    "Low",
    "Very low",
]

for col, category in zip(
    confidence_cols,
    confidence_categories,
):

    with col:

        st.markdown(
            f"""
            <div class="stats-confidence-card">

                <div class="stats-confidence-label">
                    {category.upper()}
                </div>

                <div class="stats-confidence-number">
                    {confidence_counter.get(category, 0)}
                </div>

                <div class="stats-confidence-sub">
                    studies
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Common statistical problems
# ---------------------------------------------------------

st.markdown(
    "## Common Statistical Problems"
)

flag_counter = Counter()


for _, stats in reviewed_papers:

    flags = safe_list(
        stats.get(
            "reporting_flags"
        )
    )

    for flag in flags:

        text = str(
            flag
        ).strip()

        if text:
            flag_counter[
                text
            ] += 1


if flag_counter:

    for flag, count in (
        flag_counter.most_common(
            12
        )
    ):

        st.markdown(
            f"""
            <div class="stats-problem-row">

                <div class="stats-problem-text">
                    {flag}
                </div>

                <div class="stats-problem-count">
                    {count} studies
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.info(
        "No recurring statistical-reporting problems are currently identified."
    )


# ---------------------------------------------------------
# Statistical methods
# ---------------------------------------------------------

st.markdown(
    "## Most Common Statistical Methods"
)

test_counter = Counter()


for _, stats in reviewed_papers:

    tests = safe_list(
        stats.get(
            "identified_statistical_tests"
        )
    )

    for test in tests:

        test = str(
            test
        ).strip()

        if test:
            test_counter[
                test
            ] += 1


if test_counter:

    method_cols = st.columns(4)

    for col, (
        test,
        count,
    ) in zip(
        method_cols,
        test_counter.most_common(
            4
        ),
    ):

        with col:

            st.markdown(
                f"""
                <div class="stats-method-card">

                    <div class="stats-method-title">
                        {test}
                    </div>

                    <div class="stats-method-count">
                        {count} studies
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

else:

    st.info(
        "Statistical methods will appear after studies have been reviewed."
    )


# ---------------------------------------------------------
# Reporting quality
# ---------------------------------------------------------

st.markdown(
    "## Reporting Quality"
)

reporting_scores = []
precision_scores = []
rigor_scores = []
interpretation_scores = []


for _, stats in reviewed_papers:

    scores = safe_dict(
        stats.get(
            "scores"
        )
    )

    values = {
        "reporting": scores.get(
            "statistical_reporting"
        ),
        "precision": scores.get(
            "precision_and_power"
        ),
        "rigor": scores.get(
            "analysis_rigor"
        ),
        "interpretation": scores.get(
            "interpretation_quality"
        ),
    }

    if isinstance(
        values["reporting"],
        (int, float),
    ):
        reporting_scores.append(
            values["reporting"]
        )

    if isinstance(
        values["precision"],
        (int, float),
    ):
        precision_scores.append(
            values["precision"]
        )

    if isinstance(
        values["rigor"],
        (int, float),
    ):
        rigor_scores.append(
            values["rigor"]
        )

    if isinstance(
        values["interpretation"],
        (int, float),
    ):
        interpretation_scores.append(
            values["interpretation"]
        )


def average(values):
    if not values:
        return 0

    return round(
        sum(values)
        / len(values),
        1,
    )


q1, q2, q3, q4 = st.columns(4)

q1.metric(
    "Reporting",
    average(
        reporting_scores
    ),
)

q2.metric(
    "Precision / Power",
    average(
        precision_scores
    ),
)

q3.metric(
    "Analysis Rigor",
    average(
        rigor_scores
    ),
)

q4.metric(
    "Interpretation",
    average(
        interpretation_scores
    ),
)


# ---------------------------------------------------------
# Search / filters
# ---------------------------------------------------------

st.markdown(
    "## Euler's Study Reviews"
)

search_col, confidence_col = st.columns(
    [3, 1]
)

with search_col:

    search = st.text_input(
        "Search statistical reviews",
        placeholder=(
            "Regression, confidence interval, "
            "sample size, RCT..."
        ),
        label_visibility="collapsed",
    )


with confidence_col:

    confidence_filter = st.selectbox(
        "Confidence",
        [
            "All",
            "High",
            "Moderate",
            "Low",
            "Very low",
        ],
        label_visibility="collapsed",
    )


# ---------------------------------------------------------
# Filter records
# ---------------------------------------------------------

filtered = []


for record, stats in reviewed_papers:

    metadata = safe_dict(
        record.get(
            "metadata"
        )
    )

    if (
        confidence_filter != "All"
        and stats.get(
            "statistical_confidence"
        )
        != confidence_filter
    ):
        continue

    if search:

        searchable = json.dumps(
            {
                "title": metadata.get(
                    "title"
                ),
                "statistics": stats,
            },
            ensure_ascii=False,
        ).lower()

        if (
            search.lower()
            not in searchable
        ):
            continue

    filtered.append(
        (
            record,
            stats,
        )
    )


# ---------------------------------------------------------
# Sort worst first
# ---------------------------------------------------------

filtered.sort(
    key=lambda item: (
        safe_dict(
            item[1].get(
                "scores"
            )
        ).get(
            "overall_statistics",
            0,
        )
    )
)


st.caption(
    f"{len(filtered)} statistical reviews"
)


# ---------------------------------------------------------
# Paper review cards
# ---------------------------------------------------------

for record, stats in filtered[:100]:

    metadata = safe_dict(
        record.get(
            "metadata"
        )
    )

    translation = safe_dict(
        record.get(
            "clinical_translation"
        )
    )

    title = metadata.get(
        "title",
        "Untitled paper",
    )

    scores = safe_dict(
        stats.get(
            "scores"
        )
    )

    overall = safe_number(
        scores.get(
            "overall_statistics"
        )
    )

    confidence = stats.get(
        "statistical_confidence",
        "Unknown",
    )

    flags = safe_list(
        stats.get(
            "reporting_flags"
        )
    )

    tests = safe_list(
        stats.get(
            "identified_statistical_tests"
        )
    )

    effects = safe_list(
        stats.get(
            "reported_effect_estimates"
        )
    )

    with st.expander(
        title
    ):

        st.caption(
            " · ".join(
                value
                for value in [
                    translation.get(
                        "clinical_area",
                        "",
                    ),
                    metadata.get(
                        "journal",
                        "",
                    ),
                    stats.get(
                        "study_design",
                        "",
                    ),
                ]
                if value
            )
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Statistics Score",
            overall,
        )

        c2.metric(
            "Confidence",
            confidence,
        )

        c3.metric(
            "Sample Size",
            stats.get(
                "sample_size",
                "—",
            ),
        )

        st.markdown(
            "### Euler's Summary"
        )

        st.write(
            stats.get(
                "review_summary",
                "No statistical summary available.",
            )
        )

        if tests:

            st.markdown(
                "**Methods identified**"
            )

            for test in tests:
                st.write(
                    f"• {test}"
                )

        if effects:

            st.markdown(
                "**Reported effect estimates**"
            )

            for effect in effects:
                st.write(
                    f"• {effect}"
                )

        if flags:

            st.markdown(
                "**Euler is cautious about**"
            )

            for flag in flags:
                st.warning(
                    flag
                )

        st.markdown(
            "**Component scores**"
        )

        s1, s2, s3, s4 = st.columns(
            4
        )

        s1.metric(
            "Reporting",
            scores.get(
                "statistical_reporting",
                0,
            ),
        )

        s2.metric(
            "Precision",
            scores.get(
                "precision_and_power",
                0,
            ),
        )

        s3.metric(
            "Rigor",
            scores.get(
                "analysis_rigor",
                0,
            ),
        )

        s4.metric(
            "Interpretation",
            scores.get(
                "interpretation_quality",
                0,
            ),
        )

        if stats.get(
            "requires_full_text_statistical_review",
            False,
        ):

            st.info(
                "Euler recommends full-text statistical review before relying heavily on this paper."
            )

        pubmed_url = metadata.get(
            "pubmed_url",
            "",
        )

        if pubmed_url:

            st.link_button(
                "Open PubMed ↗",
                pubmed_url,
            )


# ---------------------------------------------------------
# Euler's principles
# ---------------------------------------------------------

st.markdown(
    "## What Euler Watches For"
)

st.markdown(
    """
    Euler currently looks for abstract-level signals including:

    **Effect estimates**
    ·
    **Confidence intervals**
    ·
    **Sample size**
    ·
    **Statistical models**
    ·
    **Power calculations**
    ·
    **Missing-data handling**
    ·
    **Confounder adjustment**
    ·
    **Multiple-comparison correction**
    ·
    **Clinical vs statistical significance**

    These checks assess **reporting quality and apparent rigor**.
    They do not prove that the underlying analysis was performed correctly;
    that requires full-text methods, tables, protocols, and raw data where
    appropriate.
    """
)
