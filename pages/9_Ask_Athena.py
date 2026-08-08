import sys
from pathlib import Path

import streamlit as st


# ---------------------------------------------------------
# Make root-level modules importable
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


from athena import build_athena_response


# ---------------------------------------------------------
# Page config
# ---------------------------------------------------------

st.set_page_config(
    page_title="Ask Athena",
    page_icon="♡",
    layout="wide",
)


# ---------------------------------------------------------
# Load CSS
# ---------------------------------------------------------

STYLE_PATH = ROOT / "assets" / "css" / "style.css"

if not STYLE_PATH.exists():
    STYLE_PATH = ROOT / "assets" / "style.css"

if STYLE_PATH.exists():
    with STYLE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        ATHENA · EVIDENCE COPILOT
    </div>

    <h1 class="hero-title">
        What problem are you trying to <span>solve?</span>
    </h1>

    <p class="hero-subtitle">
        Athena searches the evidence synthesized by your research team
        and shows what the literature collectively supports, where it
        disagrees, and what remains uncertain.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Example questions
# ---------------------------------------------------------

st.markdown(
    "### Try asking Athena"
)

examples = [
    "What does the evidence say about patellar tendinopathy?",
    "What do we know about return to sport after ligament injury?",
    "What does the evidence say about PRP?",
    "Where are the biggest gaps in RED-S research?",
]

example_cols = st.columns(
    4
)

for col, example in zip(
    example_cols,
    examples,
):
    with col:
        if st.button(
            example,
            key=f"example_{example}",
            use_container_width=True,
        ):
            st.session_state[
                "athena_question"
            ] = example


# ---------------------------------------------------------
# Question input
# ---------------------------------------------------------

question = st.text_area(
    "Ask a question",
    value=st.session_state.get(
        "athena_question",
        "",
    ),
    placeholder=(
        "Example: What does the evidence say about "
        "return-to-sport testing after ACL reconstruction?"
    ),
    height=120,
    label_visibility="collapsed",
)

ask_clicked = st.button(
    "Ask Athena ✦",
    type="primary",
    use_container_width=True,
)


# ---------------------------------------------------------
# Athena response
# ---------------------------------------------------------

if ask_clicked and question.strip():

    with st.spinner(
        "Athena is reviewing the evidence..."
    ):
        response = build_athena_response(
            question
        )

    st.session_state[
        "athena_last_response"
    ] = response


response = st.session_state.get(
    "athena_last_response"
)


if response:

    st.divider()

    if not response.get(
        "found",
        False,
    ):

        st.warning(
            response.get(
                "message",
                "No relevant evidence consensus was found.",
            )
        )

        suggestion = response.get(
            "suggestion"
        )

        if suggestion:
            st.caption(
                suggestion
            )

        st.stop()


    # -----------------------------------------------------
    # Topic heading
    # -----------------------------------------------------

    st.markdown(
        f"""
        <div class="athena-response-card">

            <div class="hero-eyebrow">
                ATHENA'S EVIDENCE BRIEF
            </div>

            <h2 style="
                margin-top: 4px;
                margin-bottom: 8px;
            ">
                {response.get("topic", "Evidence Topic")}
            </h2>

            <div style="
                color: #72768d;
                font-size: 13px;
            ">
                {str(response.get("topic_type", "")).replace("_", " ").title()}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # Consensus metrics
    # -----------------------------------------------------

    st.markdown(
        "## Evidence Snapshot"
    )

    m1, m2, m3, m4, m5 = st.columns(
        5
    )

    m1.metric(
        "Evidence Status",
        response.get(
            "evidence_status",
            "Unknown",
        ),
    )

    m2.metric(
        "Consensus Confidence",
        response.get(
            "consensus_confidence",
            "Unknown",
        ),
    )

    confidence_score = response.get(
        "consensus_confidence_score"
    )

    m3.metric(
        "Confidence Score",
        (
            f"{confidence_score}/10"
            if confidence_score is not None
            else "—"
        ),
    )

    agreement = response.get(
        "agreement_percent"
    )

    m4.metric(
        "Agreement",
        (
            f"{agreement}%"
            if agreement is not None
            else "—"
        ),
    )

    m5.metric(
        "Studies",
        response.get(
            "paper_count",
            0,
        ),
    )


    # -----------------------------------------------------
    # Athena interpretation
    # -----------------------------------------------------

    st.markdown(
        "## Athena's Interpretation"
    )

    interpretation = response.get(
        "athena_interpretation"
    )

    if interpretation:
        st.markdown(
            f"""
            <div class="athena-response-card">
                {interpretation}
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.info(
            "No consensus interpretation is available yet."
        )


    # -----------------------------------------------------
    # Quality
    # -----------------------------------------------------

    st.markdown(
        "## How Strong Is the Evidence?"
    )

    q1, q2, q3 = st.columns(
        3
    )

    evidence_quality = response.get(
        "evidence_quality"
    )

    statistics_quality = response.get(
        "statistical_quality"
    )

    relevance = response.get(
        "practitioner_relevance"
    )

    q1.metric(
        "Evidence Quality",
        (
            f"{evidence_quality}/10"
            if evidence_quality is not None
            else "—"
        ),
    )

    q2.metric(
        "Statistical Quality",
        (
            f"{statistics_quality}/10"
            if statistics_quality is not None
            else "—"
        ),
    )

    q3.metric(
        "Practitioner Relevance",
        (
            f"{relevance}/10"
            if relevance is not None
            else "—"
        ),
    )


    # -----------------------------------------------------
    # Result direction
    # -----------------------------------------------------

    st.markdown(
        "## Where the Studies Point"
    )

    result_direction = response.get(
        "result_direction",
        {},
    )

    raw_counts = result_direction.get(
        "raw_counts",
        {},
    )

    d1, d2, d3, d4 = st.columns(
        4
    )

    d1.metric(
        "Favorable",
        raw_counts.get(
            "favorable",
            0,
        ),
    )

    d2.metric(
        "Neutral",
        raw_counts.get(
            "neutral",
            0,
        ),
    )

    d3.metric(
        "Unfavorable",
        raw_counts.get(
            "unfavorable",
            0,
        ),
    )

    d4.metric(
        "Unclear",
        raw_counts.get(
            "unclear",
            0,
        ),
    )


    # -----------------------------------------------------
    # Practice readiness
    # -----------------------------------------------------

    st.markdown(
        "## Practice Readiness"
    )

    p1, p2 = st.columns(
        2
    )

    p1.metric(
        "Practice-Informing Papers",
        response.get(
            "practice_informing_papers",
            0,
        ),
    )

    p2.metric(
        "Need Full-Text Review",
        response.get(
            "full_text_review_required",
            0,
        ),
    )


    # -----------------------------------------------------
    # Specialist perspectives
    # -----------------------------------------------------

    st.markdown(
        "## What the Specialists Think"
    )

    specialists = response.get(
        "specialist_perspectives",
        [],
    )

    specialist_names = {
        "regenerative_medicine": (
            "Atlas",
            "Regenerative Medicine",
            "🌱",
        ),
        "sports_performance": (
            "Vector",
            "Sports Performance",
            "⚡",
        ),
        "biomechanics": (
            "Newton",
            "Biomechanics",
            "⚙️",
        ),
        "womens_athlete_health": (
            "Athena",
            "Women's Athlete Health",
            "♡",
        ),
    }

    if specialists:

        cols = st.columns(
            min(
                len(specialists),
                4,
            )
        )

        for col, specialist in zip(
            cols,
            specialists[:4],
        ):

            specialty = specialist.get(
                "specialty",
                "",
            )

            name, role, icon = (
                specialist_names.get(
                    specialty,
                    (
                        specialty.replace(
                            "_",
                            " ",
                        ).title(),
                        "Specialist",
                        "✦",
                    ),
                )
            )

            score = specialist.get(
                "average_domain_score"
            )

            confidence_distribution = (
                specialist.get(
                    "confidence_distribution",
                    {},
                )
            )

            high = (
                confidence_distribution.get(
                    "High",
                    0,
                )
            )

            moderate = (
                confidence_distribution.get(
                    "Moderate",
                    0,
                )
            )

            with col:

                st.markdown(
                    f"""
                    <div class="ai-agent-card">

                        <div class="ai-agent-top">

                            <div class="ai-agent-avatar">
                                {icon}
                            </div>

                            <div>
                                <div class="ai-agent-name">
                                    {name}
                                </div>

                                <div class="ai-agent-role">
                                    {role}
                                </div>
                            </div>

                        </div>

                        <div class="ai-agent-stats">

                            <div>
                                <div class="ai-agent-number">
                                    {score if score is not None else "—"}
                                </div>

                                <div class="ai-agent-small">
                                    Domain score
                                </div>
                            </div>

                            <div>
                                <div class="ai-agent-number">
                                    {high + moderate}
                                </div>

                                <div class="ai-agent-small">
                                    Higher-confidence reviews
                                </div>
                            </div>

                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    else:

        st.info(
            "No specialty-level consensus is available for this topic yet."
        )


    # -----------------------------------------------------
    # Research gap
    # -----------------------------------------------------

    st.markdown(
        "## What We Still Don't Know"
    )

    research_gap = response.get(
        "research_gap"
    )

    if research_gap:
        st.warning(
            research_gap
        )


    recurring_issues = response.get(
        "recurring_issues",
        [],
    )

    if recurring_issues:

        with st.expander(
            "Recurring limitations across the literature"
        ):

            for issue in recurring_issues:

                if not isinstance(
                    issue,
                    dict,
                ):
                    continue

                st.write(
                    f"• {issue.get('issue', '')} "
                    f"— seen {issue.get('count', 0)} time(s)"
                )


    # -----------------------------------------------------
    # Related topics
    # -----------------------------------------------------

    related_topics = response.get(
        "related_topics",
        [],
    )

    if related_topics:

        st.markdown(
            "## Related Evidence"
        )

        cols = st.columns(
            min(
                len(related_topics),
                4,
            )
        )

        for col, topic in zip(
            cols,
            related_topics[:4],
        ):

            with col:

                st.markdown(
                    f"""
                    <div class="athena-concept-card">

                        <strong>
                            {topic.get("concept", "")}
                        </strong>

                        <br><br>

                        {topic.get("paper_count", 0)} studies

                        <br>

                        <span style="
                            color:#72768d;
                            font-size:11px;
                        ">
                            {topic.get("consensus", "Unknown")}
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


    # -----------------------------------------------------
    # Supporting papers
    # -----------------------------------------------------

    st.markdown(
        "## Supporting Studies"
    )

    supporting_papers = response.get(
        "supporting_papers",
        [],
    )

    if supporting_papers:

        for number, paper in enumerate(
            supporting_papers,
            start=1,
        ):

            metadata = paper.get(
                "metadata",
                {},
            )

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

            title = metadata.get(
                "title",
                "Untitled paper",
            )

            with st.expander(
                f"{number}. {title}"
            ):

                citation = [
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

                st.caption(
                    " · ".join(
                        item
                        for item in citation
                        if item
                    )
                )

                appraisal_scores = appraisal.get(
                    "scores",
                    {},
                )

                statistics_scores = statistics.get(
                    "scores",
                    {},
                )

                c1, c2, c3 = st.columns(
                    3
                )

                c1.metric(
                    "Evidence",
                    appraisal_scores.get(
                        "overall_evidence",
                        0,
                    ),
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
                    appraisal_scores.get(
                        "practitioner_relevance",
                        0,
                    ),
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
# Footer / transparency
# ---------------------------------------------------------

st.divider()

st.caption(
    "Athena reports synthesized evidence from the Optimize Evidence "
    "pipeline. Consensus scores are formula-based and are not a substitute "
    "for formal systematic review, meta-analysis, clinical judgment, or "
    "full-text appraisal."
)
