import json
import re
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Ask Athena",
    page_icon="♡",
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
# Helpers
# ---------------------------------------------------------

def safe_dict(value):
    return value if isinstance(value, dict) else {}


def safe_list(value):
    return value if isinstance(value, list) else []


def normalize(text):
    return re.sub(
        r"[^a-z0-9\s-]",
        " ",
        str(text).lower(),
    )


def tokenize(text):
    words = normalize(text).split()

    stopwords = {
        "the", "a", "an", "and", "or", "of", "for", "to",
        "in", "on", "with", "is", "are", "what", "does",
        "do", "about", "tell", "me", "show", "evidence",
        "research", "paper", "papers",
    }

    return {
        word
        for word in words
        if len(word) > 2
        and word not in stopwords
    }


def paper_search_text(record):
    metadata = safe_dict(
        record.get("metadata")
    )

    appraisal = safe_dict(
        record.get("appraisal")
    )

    translation = safe_dict(
        record.get(
            "clinical_translation"
        )
    )

    specialties = safe_dict(
        record.get(
            "specialties"
        )
    )

    parts = [
        metadata.get("title", ""),
        metadata.get("abstract", ""),
        metadata.get("topic", ""),
        translation.get(
            "clinical_area",
            "",
        ),
        translation.get(
            "intervention_or_exposure",
            "",
        ),
        translation.get(
            "clinical_summary",
            "",
        ),
        translation.get(
            "practitioner_takeaway",
            "",
        ),
        appraisal.get(
            "study_design",
            "",
        ),
    ]

    for specialty_data in specialties.values():

        if not isinstance(
            specialty_data,
            dict,
        ):
            continue

        parts.append(
            specialty_data.get(
                "specialist_takeaway",
                "",
            )
        )

        parts.extend(
            safe_list(
                specialty_data.get(
                    "domain_flags"
                )
            )
        )

    return normalize(
        " ".join(
            str(part)
            for part in parts
        )
    )


def score_record(
    record,
    query_tokens,
):
    text = paper_search_text(
        record
    )

    score = 0

    for token in query_tokens:

        occurrences = text.count(
            token
        )

        score += occurrences

        metadata = safe_dict(
            record.get(
                "metadata"
            )
        )

        title = normalize(
            metadata.get(
                "title",
                "",
            )
        )

        if token in title:
            score += 4

        translation = safe_dict(
            record.get(
                "clinical_translation"
            )
        )

        clinical_area = normalize(
            translation.get(
                "clinical_area",
                "",
            )
        )

        if token in clinical_area:
            score += 5

    appraisal = safe_dict(
        record.get(
            "appraisal"
        )
    )

    scores = safe_dict(
        appraisal.get(
            "scores"
        )
    )

    evidence_score = scores.get(
        "overall_evidence",
        0,
    )

    relevance_score = scores.get(
        "practitioner_relevance",
        0,
    )

    if isinstance(
        evidence_score,
        (int, float),
    ):
        score += evidence_score * 0.15

    if isinstance(
        relevance_score,
        (int, float),
    ):
        score += relevance_score * 0.15

    return score


def find_relevant_papers(
    query,
    limit=8,
):
    query_tokens = tokenize(
        query
    )

    if not query_tokens:
        return []

    scored = []

    for record in evidence_db:

        score = score_record(
            record,
            query_tokens,
        )

        if score > 0:
            scored.append(
                (
                    score,
                    record,
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        record
        for _, record
        in scored[:limit]
    ]


def find_graph_matches(
    query,
    limit=8,
):
    query_tokens = tokenize(
        query
    )

    nodes = safe_list(
        knowledge_graph.get(
            "nodes"
        )
    )

    scored = []

    for node in nodes:

        if not isinstance(
            node,
            dict,
        ):
            continue

        if node.get(
            "type"
        ) == "paper":
            continue

        label = normalize(
            node.get(
                "label",
                "",
            )
        )

        score = sum(
            3
            for token in query_tokens
            if token in label
        )

        if score > 0:
            scored.append(
                (
                    score,
                    node,
                )
            )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        node
        for _, node
        in scored[:limit]
    ]


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        ATHENA
    </div>

    <h1 class="hero-title">
        Ask <span>Athena</span>
    </h1>

    <p class="hero-subtitle">
        Ask a clinical or performance question and Athena will search
        your curated evidence library, specialist reviews, and knowledge graph.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Prompt suggestions
# ---------------------------------------------------------

st.markdown(
    "### Try asking"
)

suggestion_cols = st.columns(4)

suggestions = [
    "What are researchers trying to solve in patellar tendinopathy?",
    "What does the evidence say about PRP?",
    "Where are the biggest RED-S evidence gaps?",
    "What are common problems in sprint performance research?",
]

for col, suggestion in zip(
    suggestion_cols,
    suggestions,
):

    with col:

        if st.button(
            suggestion,
            use_container_width=True,
        ):
            st.session_state[
                "athena_query"
            ] = suggestion


# ---------------------------------------------------------
# Query
# ---------------------------------------------------------

query = st.text_area(
    "What problem are you trying to solve?",
    value=st.session_state.get(
        "athena_query",
        "",
    ),
    placeholder=(
        "Example: What does the evidence say about PRP "
        "for patellar tendinopathy?"
    ),
    height=120,
)


search_clicked = st.button(
    "Ask Athena",
    type="primary",
    use_container_width=True,
)


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

if search_clicked and query.strip():

    relevant_papers = (
        find_relevant_papers(
            query
        )
    )

    graph_matches = (
        find_graph_matches(
            query
        )
    )

    st.divider()

    st.markdown(
        "## Athena's Evidence Brief"
    )

    if not relevant_papers:

        st.info(
            "I couldn't find a strong match in the current evidence database."
        )

        st.stop()


    # -----------------------------------------------------
    # Overview
    # -----------------------------------------------------

    evidence_scores = []

    practice_informing = 0

    clinical_areas = []

    for record in relevant_papers:

        appraisal = safe_dict(
            record.get(
                "appraisal"
            )
        )

        translation = safe_dict(
            record.get(
                "clinical_translation"
            )
        )

        scores = safe_dict(
            appraisal.get(
                "scores"
            )
        )

        evidence = scores.get(
            "overall_evidence"
        )

        if isinstance(
            evidence,
            (int, float),
        ):
            evidence_scores.append(
                evidence
            )

        if (
            translation.get(
                "practice_readiness"
            )
            == "Practice-informing"
        ):
            practice_informing += 1

        area = translation.get(
            "clinical_area"
        )

        if (
            area
            and area not in clinical_areas
        ):
            clinical_areas.append(
                area
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


    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Relevant Papers",
        len(
            relevant_papers
        ),
    )

    m2.metric(
        "Avg Evidence",
        average_evidence,
    )

    m3.metric(
        "Practice-Informing",
        practice_informing,
    )


    # -----------------------------------------------------
    # Athena answer
    # -----------------------------------------------------

    st.markdown(
        "### What I found"
    )

    top_record = relevant_papers[
        0
    ]

    top_translation = safe_dict(
        top_record.get(
            "clinical_translation"
        )
    )

    top_takeaway = top_translation.get(
        "practitioner_takeaway",
        "",
    )

    if top_takeaway:

        st.markdown(
            f"""
            <div class="athena-response-card">
                {top_takeaway}
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.write(
            "The database contains relevant papers, but no clinical translation is available yet."
        )


    # -----------------------------------------------------
    # Problems / concepts
    # -----------------------------------------------------

    if clinical_areas:

        st.markdown(
            "### Clinical problems connected to your question"
        )

        cols = st.columns(
            min(
                4,
                len(
                    clinical_areas
                ),
            )
        )

        for col, area in zip(
            cols,
            clinical_areas[:4],
        ):

            with col:

                st.markdown(
                    f"""
                    <div class="athena-concept-card">
                        {area}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


    # -----------------------------------------------------
    # Knowledge graph matches
    # -----------------------------------------------------

    if graph_matches:

        st.markdown(
            "### Related concepts"
        )

        for node in graph_matches:

            st.write(
                f"• **{node.get('label', '')}** "
                f"— {str(node.get('type', '')).replace('_', ' ').title()}"
            )


    # -----------------------------------------------------
    # Specialist insights
    # -----------------------------------------------------

    st.markdown(
        "### What the specialists are saying"
    )

    specialist_labels = {
        "regenerative_medicine": "Atlas",
        "sports_performance": "Vector",
        "biomechanics": "Newton",
        "womens_athlete_health": "Athena",
    }

    specialist_messages = []

    for record in relevant_papers:

        specialties = safe_dict(
            record.get(
                "specialties"
            )
        )

        for specialty, review in (
            specialties.items()
        ):

            if not isinstance(
                review,
                dict,
            ):
                continue

            if not review.get(
                "reviewed",
                False,
            ):
                continue

            takeaway = review.get(
                "specialist_takeaway",
                "",
            )

            if not takeaway:
                continue

            name = specialist_labels.get(
                specialty,
                specialty,
            )

            message = (
                name,
                takeaway,
            )

            if (
                message
                not in specialist_messages
            ):
                specialist_messages.append(
                    message
                )


    if specialist_messages:

        for name, takeaway in (
            specialist_messages[:6]
        ):

            with st.container(
                border=True
            ):

                st.markdown(
                    f"**{name}**"
                )

                st.write(
                    takeaway
                )

    else:

        st.write(
            "No specialist reviews are available for these papers yet."
        )


    # -----------------------------------------------------
    # Evidence gaps
    # -----------------------------------------------------

    st.markdown(
        "### What we still don't know"
    )

    query_tokens = tokenize(
        query
    )

    matching_gaps = []

    for gap in safe_list(
        knowledge_graph.get(
            "evidence_gaps"
        )
    ):

        if not isinstance(
            gap,
            dict,
        ):
            continue

        searchable = normalize(
            json.dumps(
                gap
            )
        )

        if any(
            token in searchable
            for token in query_tokens
        ):
            matching_gaps.append(
                gap
            )


    if matching_gaps:

        for gap in matching_gaps[:5]:

            st.warning(
                gap.get(
                    "concept",
                    "Evidence gap",
                )
            )

            for reason in safe_list(
                gap.get(
                    "reasons"
                )
            ):
                st.write(
                    f"• {reason}"
                )

    else:

        st.write(
            "No directly matched evidence gap is currently indexed."
        )


    # -----------------------------------------------------
    # Papers
    # -----------------------------------------------------

    st.markdown(
        "### Best-matching papers"
    )

    for number, record in enumerate(
        relevant_papers,
        start=1,
    ):

        metadata = safe_dict(
            record.get(
                "metadata"
            )
        )

        appraisal = safe_dict(
            record.get(
                "appraisal"
            )
        )

        statistics = safe_dict(
            record.get(
                "statistics"
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

        with st.expander(
            f"{number}. {title}"
        ):

            st.caption(
                " · ".join(
                    value
                    for value in [
                        translation.get(
                            "clinical_area",
                            "",
                        ),
                        appraisal.get(
                            "study_design",
                            "",
                        ),
                        metadata.get(
                            "journal",
                            "",
                        ),
                    ]
                    if value
                )
            )

            appraisal_scores = safe_dict(
                appraisal.get(
                    "scores"
                )
            )

            statistics_scores = safe_dict(
                statistics.get(
                    "scores"
                )
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
# Explanation
# ---------------------------------------------------------

st.divider()

st.caption(
    "Athena v1 uses transparent keyword matching, evidence scores, "
    "specialty reviews, and your knowledge graph. It does not generate "
    "new medical claims or use a paid LLM API."
)
