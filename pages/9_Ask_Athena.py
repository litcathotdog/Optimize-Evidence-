import json
from pathlib import Path

import streamlit as st


# =========================================================
# LOAD DATA
# =========================================================

def load_json(path, default):
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

journal_club = load_json(
    "data/journal_club.json",
    {},
)

dashboard = load_json(
    "data/dashboard.json",
    {},
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


def get_title(record):
    return (
        get_metadata(record).get("title")
        or "Untitled paper"
    )


def get_clinical_area(record):
    value = get_translation(
        record
    ).get(
        "clinical_area",
        "",
    )

    if (
        isinstance(value, str)
        and value.strip()
    ):
        return value.strip()

    return "Other"


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


def get_evidence_score(record):
    scores = get_appraisal(
        record
    ).get(
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
    scores = get_statistics(
        record
    ).get(
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

    parts = [
        get_title(record),
        metadata.get(
            "abstract",
            "",
        ),
        get_clinical_area(
            record
        ),
        translation.get(
            "clinical_summary",
            "",
        ),
        translation.get(
            "practitioner_takeaway",
            "",
        ),
        translation.get(
            "intervention_or_exposure",
            "",
        ),
        appraisal.get(
            "intervention_or_exposure",
            "",
        ),
    ]

    return " ".join(
        str(part)
        for part in parts
        if part
    ).lower()


def find_relevant_records(
    query,
    limit=5,
):
    if not query.strip():
        return []

    query_terms = [
        term.strip().lower()
        for term in query.split()
        if len(
            term.strip()
        ) >= 3
    ]

    scored = []

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        text = build_search_text(
            record
        )

        relevance = sum(
            1
            for term in query_terms
            if term in text
        )

        if relevance == 0:
            continue

        relevance += (
            get_evidence_score(
                record
            )
            / 10
        )

        scored.append(
            (
                relevance,
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


# =========================================================
# SESSION STATE
# =========================================================

if "athena_messages" not in st.session_state:

    st.session_state[
        "athena_messages"
    ] = []


# =========================================================
# HEADER
# =========================================================

st.caption(
    "ATHENA • CLINICAL RESEARCH ASSISTANT"
)

st.title(
    "Ask Athena"
)

st.write(
    "Ask questions about the research library, clinical problems, "
    "evidence strength, interventions, or areas of uncertainty."
)

st.write("")


# =========================================================
# CONTEXT METRICS
# =========================================================

clinical_areas = {
    get_clinical_area(
        record
    )
    for record in evidence_db
    if isinstance(
        record,
        dict,
    )
}

practice_informing = sum(
    1
    for record in evidence_db
    if isinstance(
        record,
        dict,
    )
    and get_translation(
        record
    ).get(
        "practice_readiness"
    )
    == "Practice-informing"
)


m1, m2, m3 = st.columns(
    3,
    gap="medium",
)

with m1:

    st.metric(
        "Indexed Papers",
        len(
            evidence_db
        )
        if isinstance(
            evidence_db,
            list,
        )
        else 0,
        border=True,
    )


with m2:

    st.metric(
        "Clinical Areas",
        len(
            clinical_areas
        ),
        border=True,
    )


with m3:

    st.metric(
        "Practice-Informing",
        practice_informing,
        border=True,
    )


st.write("")


# =========================================================
# SUGGESTED QUESTIONS
# =========================================================

st.subheader(
    "Try asking"
)

suggestions = [
    "What does the evidence say about PRP for tendinopathy?",
    "What are the biggest evidence gaps in RED-S?",
    "Which papers are most practice-informing?",
    "What research exists on sprint performance and power?",
]

suggestion_cols = st.columns(
    2,
    gap="medium",
)

for index, suggestion in enumerate(
    suggestions
):

    col = suggestion_cols[
        index % 2
    ]

    with col:

        if st.button(
            suggestion,
            key=f"athena_suggestion_{index}",
            width="stretch",
        ):

            st.session_state[
                "athena_pending_question"
            ] = suggestion

            st.rerun()


# =========================================================
# CHAT HISTORY
# =========================================================

st.write("")

st.subheader(
    "Conversation"
)


if not st.session_state[
    "athena_messages"
]:

    st.info(
        "Athena is ready. Ask a question below."
    )


for message in st.session_state[
    "athena_messages"
]:

    role = message.get(
        "role",
        "assistant",
    )

    content = message.get(
        "content",
        "",
    )

    with st.chat_message(
        role
    ):

        st.write(
            content
        )


# =========================================================
# QUESTION INPUT
# =========================================================

pending_question = (
    st.session_state.pop(
        "athena_pending_question",
        None,
    )
)

question = st.chat_input(
    "Ask Athena about the evidence..."
)

if pending_question:
    question = pending_question


# =========================================================
# STAGE 1 RESPONSE ENGINE
# =========================================================

if question:

    st.session_state[
        "athena_messages"
    ].append(
        {
            "role": "user",
            "content": question,
        }
    )

    relevant_records = (
        find_relevant_records(
            question,
            limit=5,
        )
    )

    if relevant_records:

        best_record = (
            relevant_records[0]
        )

        area = get_clinical_area(
            best_record
        )

        takeaway = get_takeaway(
            best_record
        )

        evidence_score = (
            get_evidence_score(
                best_record
            )
        )

        statistics_score = (
            get_statistics_score(
                best_record
            )
        )

        answer = (
            f"I found {len(relevant_records)} closely related papers "
            f"in the current evidence library. The strongest match is in "
            f"**{area}**.\n\n"
            f"**Current evidence signal:** Evidence score "
            f"{evidence_score}/10 and statistics score "
            f"{statistics_score}/10.\n\n"
            f"**Practitioner takeaway:** {takeaway}\n\n"
            "This is a Stage 1 evidence-library response based on keyword "
            "matching and your existing structured reviews. In Stage 2, "
            "Athena can synthesize across multiple papers and generate "
            "a more nuanced answer."
        )

    else:

        answer = (
            "I couldn't find a strong match in the current evidence library. "
            "Try using a condition, intervention, outcome, or research topic "
            "that appears in the indexed papers."
        )

    st.session_state[
        "athena_messages"
    ].append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    st.rerun()


# =========================================================
# SUPPORTING EVIDENCE
# =========================================================

if st.session_state[
    "athena_messages"
]:

    last_user_question = None

    for message in reversed(
        st.session_state[
            "athena_messages"
        ]
    ):

        if (
            message.get(
                "role"
            )
            == "user"
        ):
            last_user_question = (
                message.get(
                    "content",
                    "",
                )
            )

            break

    if last_user_question:

        supporting_records = (
            find_relevant_records(
                last_user_question,
                limit=5,
            )
        )

        if supporting_records:

            st.write("")

            st.subheader(
                "Supporting Evidence"
            )

            for index, record in enumerate(
                supporting_records,
                start=1,
            ):

                metadata = get_metadata(
                    record
                )

                title = get_title(
                    record
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

                with st.expander(
                    f"{index}. {title}"
                ):

                    source_parts = []

                    if journal:
                        source_parts.append(
                            str(journal)
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

                    c1, c2, c3 = (
                        st.columns(3)
                    )

                    with c1:

                        st.metric(
                            "Evidence",
                            get_evidence_score(
                                record
                            ),
                        )

                    with c2:

                        st.metric(
                            "Statistics",
                            get_statistics_score(
                                record
                            ),
                        )

                    with c3:

                        st.metric(
                            "Clinical Area",
                            get_clinical_area(
                                record
                            ),
                        )

                    st.markdown(
                        "**Practitioner takeaway**"
                    )

                    st.write(
                        get_takeaway(
                            record
                        )
                    )

                    pubmed_url = (
                        metadata.get(
                            "pubmed_url",
                            "",
                        )
                    )

                    if pubmed_url:

                        st.link_button(
                            "Open PubMed",
                            pubmed_url,
                        )


# =========================================================
# RESET
# =========================================================

st.write("")

if st.button(
    "Clear conversation",
):

    st.session_state[
        "athena_messages"
    ] = []

    st.rerun()
