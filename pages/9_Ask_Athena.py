import streamlit as st

from athena_agent import (
    athena_status,
    synthesize_question,
)


# =========================================================
# SESSION STATE
# =========================================================

if "athena_messages" not in st.session_state:
    st.session_state["athena_messages"] = []

if "athena_last_result" not in st.session_state:
    st.session_state["athena_last_result"] = None


# =========================================================
# HEADER
# =========================================================

st.caption(
    "ATHENA • EVIDENCE SYNTHESIS"
)

st.title(
    "Ask Athena"
)

st.write(
    "Ask questions about clinical problems, interventions, "
    "evidence quality, disagreement across studies, and "
    "practice relevance."
)

st.write("")


# =========================================================
# ATHENA STATUS
# =========================================================

status = athena_status()

s1, s2, s3 = st.columns(
    3,
    gap="medium",
)

with s1:
    st.metric(
        "Indexed Papers",
        status.get(
            "indexed_papers",
            0,
        ),
        border=True,
    )

with s2:
    st.metric(
        "API",
        (
            "Connected"
            if status.get(
                "api_configured",
                False,
            )
            else "Not configured"
        ),
        border=True,
    )

with s3:
    st.metric(
        "Model",
        status.get(
            "model",
            "Unknown",
        ),
        border=True,
    )


if not status.get(
    "api_configured",
    False,
):
    st.error(
        "OpenAI is not configured for Athena. "
        "Add OPENAI_API_KEY to Streamlit Secrets."
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
    "What does the evidence suggest about sprint performance and power?",
    "Where do the strongest studies disagree?",
]

suggestion_cols = st.columns(
    2,
    gap="medium",
)

for index, suggestion in enumerate(
    suggestions,
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
# CONVERSATION
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

        st.markdown(
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
# RUN ATHENA
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

    with st.spinner(
        "Athena is reviewing the evidence..."
    ):

        try:

            result = synthesize_question(
                question
            )

        except Exception as error:

            result = {
                "answer": (
                    "Athena could not complete the synthesis.\n\n"
                    f"Technical error: {error}"
                ),
                "papers": [],
                "paper_count": 0,
                "model": status.get(
                    "model",
                    "Unknown",
                ),
            }

    st.session_state[
        "athena_last_result"
    ] = result

    st.session_state[
        "athena_messages"
    ].append(
        {
            "role": "assistant",
            "content": result.get(
                "answer",
                "No synthesis was returned.",
            ),
        }
    )

    st.rerun()


# =========================================================
# SUPPORTING EVIDENCE
# =========================================================

last_result = st.session_state.get(
    "athena_last_result"
)

if (
    isinstance(
        last_result,
        dict,
    )
    and last_result
):

    papers = last_result.get(
        "papers",
        [],
    )

    if not isinstance(
        papers,
        list,
    ):
        papers = []

    st.write("")

    st.divider()

    st.subheader(
        "Supporting Evidence"
    )

    st.caption(
        f"{len(papers)} papers used in the synthesis"
    )


    if papers:

        for paper in papers:

            number = paper.get(
                "number",
                "",
            )

            title = paper.get(
                "title",
                "Untitled paper",
            )

            with st.expander(
                f"[{number}] {title}"
            ):

                journal = paper.get(
                    "journal",
                    "",
                )

                year = paper.get(
                    "year",
                    "",
                )

                clinical_area = paper.get(
                    "clinical_area",
                    "",
                )

                source_parts = []

                if journal:
                    source_parts.append(
                        str(journal)
                    )

                if year:
                    source_parts.append(
                        str(year)
                    )

                if clinical_area:
                    source_parts.append(
                        str(
                            clinical_area
                        )
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
                        paper.get(
                            "evidence_score",
                            0,
                        ),
                    )

                with c2:

                    st.metric(
                        "Statistics",
                        paper.get(
                            "statistics_score",
                            0,
                        ),
                    )

                with c3:

                    st.metric(
                        "Practice Readiness",
                        paper.get(
                            "practice_readiness",
                            "Unknown",
                        ),
                    )


                if paper.get(
                    "requires_full_text",
                    False,
                ):

                    st.warning(
                        "This paper is flagged for full-text review."
                    )


                pubmed_url = paper.get(
                    "pubmed_url",
                    "",
                )

                if pubmed_url:

                    st.link_button(
                        "Open PubMed",
                        pubmed_url,
                    )

    else:

        st.info(
            "Athena did not retrieve supporting papers for the last question."
        )


# =========================================================
# RESPONSE DETAILS
# =========================================================

if (
    isinstance(
        last_result,
        dict,
    )
    and last_result
):

    st.write("")

    with st.expander(
        "Athena response details"
    ):

        st.write(
            f"Model: {last_result.get('model', 'Unknown')}"
        )

        st.write(
            f"Papers used: {last_result.get('paper_count', 0)}"
        )


# =========================================================
# CLEAR CONVERSATION
# =========================================================

st.write("")

if st.button(
    "Clear conversation"
):

    st.session_state[
        "athena_messages"
    ] = []

    st.session_state[
        "athena_last_result"
    ] = None

    st.rerun()
