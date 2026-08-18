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
# HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def valid_url(value):
    url = clean_text(value)

    if url.startswith(
        ("http://", "https://")
    ):
        return url

    return ""


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

try:
    status = athena_status()

    if not isinstance(status, dict):
        status = {}

except Exception:
    status = {}


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


messages = st.session_state.get(
    "athena_messages",
    [],
)

if not isinstance(
    messages,
    list,
):
    messages = []

    st.session_state[
        "athena_messages"
    ] = messages


if not messages:

    st.info(
        "Athena is ready. Ask a question below."
    )


for message in messages:

    if not isinstance(
        message,
        dict,
    ):
        continue

    role = clean_text(
        message.get(
            "role",
            "assistant",
        )
    )

    if role not in {
        "user",
        "assistant",
    }:
        role = "assistant"

    content = clean_text(
        message.get(
            "content",
            "",
        )
    )

    if not content:
        continue


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
    question = clean_text(
        pending_question
    )

else:
    question = clean_text(
        question
    )


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

            if not isinstance(
                result,
                dict,
            ):
                result = {
                    "answer": (
                        "Athena did not return a valid synthesis."
                    ),
                    "papers": [],
                    "paper_count": 0,
                    "model": status.get(
                        "model",
                        "Unknown",
                    ),
                }


        except Exception:

            result = {
                "answer": (
                    "Athena could not complete the synthesis. "
                    "Please try again or check the app logs."
                ),
                "papers": [],
                "paper_count": 0,
                "model": status.get(
                    "model",
                    "Unknown",
                ),
            }


    answer = clean_text(
        result.get(
            "answer",
            "",
        )
    )

    if not answer:
        answer = (
            "No synthesis was returned."
        )


    st.session_state[
        "athena_last_result"
    ] = result


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

        for paper_index, paper in enumerate(
            papers,
            start=1,
        ):

            if not isinstance(
                paper,
                dict,
            ):
                continue


            number = clean_text(
                paper.get(
                    "number",
                    paper_index,
                )
            )

            title = clean_text(
                paper.get(
                    "title",
                    "Untitled paper",
                )
            )

            if not title:
                title = "Untitled paper"


            with st.expander(
                f"[{number}] {title}"
            ):

                journal = clean_text(
                    paper.get(
                        "journal",
                        "",
                    )
                )

                year = clean_text(
                    paper.get(
                        "year",
                        "",
                    )
                )

                clinical_area = clean_text(
                    paper.get(
                        "clinical_area",
                        "",
                    )
                )


                source_parts = []

                if journal:
                    source_parts.append(
                        journal
                    )

                if year:
                    source_parts.append(
                        year
                    )

                if clinical_area:
                    source_parts.append(
                        clinical_area
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
                        clean_text(
                            paper.get(
                                "practice_readiness",
                                "Unknown",
                            )
                        )
                        or "Unknown",
                    )


                if bool(
                    paper.get(
                        "requires_full_text",
                        False,
                    )
                ):

                    st.warning(
                        "This paper is flagged for full-text review."
                    )


                pubmed_url = valid_url(
                    paper.get(
                        "pubmed_url",
                        "",
                    )
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
            "Model: "
            + clean_text(
                last_result.get(
                    "model",
                    "Unknown",
                )
            )
        )

        st.write(
            "Papers used: "
            + clean_text(
                last_result.get(
                    "paper_count",
                    0,
                )
            )
        )


# =========================================================
# CLEAR CONVERSATION
# =========================================================

st.write("")


if st.button(
    "Clear conversation",
    key="athena_clear_conversation",
):

    st.session_state[
        "athena_messages"
    ] = []

    st.session_state[
        "athena_last_result"
    ] = None

    st.session_state.pop(
        "athena_pending_question",
        None,
    )

    st.rerun()
