"""
Optimize Evidence: Athena Evidence Synthesis Agent

Reads:
    data/evidence_database.json

Purpose
-------
Retrieve the most relevant papers for a clinical/research question,
rank them using relevance + evidence quality, and send a compact
evidence packet to the OpenAI Responses API for multi-paper synthesis.

The model is instructed to synthesize ONLY the supplied evidence.
"""

from __future__ import annotations

import json
import os
import re

from pathlib import Path
from typing import Any

from openai import OpenAI


# =========================================================
# CONFIG
# =========================================================

DATABASE_PATH = Path(
    "data/evidence_database.json"
)

DEFAULT_MODEL = "gpt-5-mini"

DEFAULT_MAX_PAPERS = 8


# =========================================================
# OPENAI CONFIG
# =========================================================

def get_api_key() -> str:
    """
    Resolve the OpenAI API key.

    Order:
    1. Streamlit Secrets
    2. Environment variable
    """

    # -----------------------------------------------------
    # Streamlit Secrets
    # -----------------------------------------------------

    try:
        import streamlit as st

        secret_key = st.secrets.get(
            "OPENAI_API_KEY"
        )

        if secret_key:
            return str(
                secret_key
            )

    except Exception:
        pass

    # -----------------------------------------------------
    # Environment variable
    # -----------------------------------------------------

    env_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if env_key:
        return env_key

    raise RuntimeError(
        "OPENAI_API_KEY is not configured. "
        "Add it to Streamlit Secrets or your environment."
    )


def get_model() -> str:
    """
    Resolve the OpenAI model.

    Order:
    1. Streamlit Secrets
    2. Environment variable
    3. Default small model
    """

    # -----------------------------------------------------
    # Streamlit Secrets
    # -----------------------------------------------------

    try:
        import streamlit as st

        secret_model = st.secrets.get(
            "OPENAI_MODEL"
        )

        if secret_model:
            return str(
                secret_model
            )

    except Exception:
        pass

    # -----------------------------------------------------
    # Environment variable
    # -----------------------------------------------------

    env_model = os.getenv(
        "OPENAI_MODEL"
    )

    if env_model:
        return env_model

    return DEFAULT_MODEL


def get_client() -> OpenAI:
    return OpenAI(
        api_key=get_api_key()
    )


# =========================================================
# DATABASE
# =========================================================

def load_database() -> list[dict[str, Any]]:

    if not DATABASE_PATH.exists():
        return []

    try:

        with DATABASE_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return []

    if not isinstance(
        data,
        list,
    ):
        return []

    return [
        record
        for record in data
        if isinstance(
            record,
            dict,
        )
    ]


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def get_dict(
    record: dict[str, Any],
    key: str,
) -> dict[str, Any]:

    value = record.get(
        key,
        {},
    )

    if isinstance(
        value,
        dict,
    ):
        return value

    return {}


def get_metadata(
    record: dict[str, Any],
) -> dict[str, Any]:

    return get_dict(
        record,
        "metadata",
    )


def get_appraisal(
    record: dict[str, Any],
) -> dict[str, Any]:

    return get_dict(
        record,
        "appraisal",
    )


def get_statistics(
    record: dict[str, Any],
) -> dict[str, Any]:

    return get_dict(
        record,
        "statistics",
    )


def get_translation(
    record: dict[str, Any],
) -> dict[str, Any]:

    return get_dict(
        record,
        "clinical_translation",
    )


def get_specialties(
    record: dict[str, Any],
) -> dict[str, Any]:

    return get_dict(
        record,
        "specialties",
    )


# =========================================================
# RECORD FIELDS
# =========================================================

def get_title(
    record: dict[str, Any],
) -> str:

    return (
        clean_text(
            get_metadata(
                record
            ).get(
                "title"
            )
        )
        or "Untitled paper"
    )


def get_abstract(
    record: dict[str, Any],
) -> str:

    return clean_text(
        get_metadata(
            record
        ).get(
            "abstract"
        )
    )


def get_journal(
    record: dict[str, Any],
) -> str:

    return clean_text(
        get_metadata(
            record
        ).get(
            "journal"
        )
    )


def get_year(
    record: dict[str, Any],
) -> str:

    metadata = get_metadata(
        record
    )

    return clean_text(
        metadata.get(
            "publication_year"
        )
        or metadata.get(
            "year"
        )
    )


def get_pubmed_url(
    record: dict[str, Any],
) -> str:

    return clean_text(
        get_metadata(
            record
        ).get(
            "pubmed_url"
        )
    )


def get_clinical_area(
    record: dict[str, Any],
) -> str:

    translation = get_translation(
        record
    )

    return (
        clean_text(
            translation.get(
                "clinical_area"
            )
        )
        or "Other"
    )


def get_intervention(
    record: dict[str, Any],
) -> str:

    translation = get_translation(
        record
    )

    value = clean_text(
        translation.get(
            "intervention_or_exposure"
        )
    )

    if value:
        return value

    appraisal = get_appraisal(
        record
    )

    return clean_text(
        appraisal.get(
            "intervention_or_exposure"
        )
    )


def get_takeaway(
    record: dict[str, Any],
) -> str:

    translation = get_translation(
        record
    )

    takeaway = clean_text(
        translation.get(
            "practitioner_takeaway"
        )
    )

    if takeaway:
        return takeaway

    return clean_text(
        translation.get(
            "clinical_summary"
        )
    )


def get_practice_readiness(
    record: dict[str, Any],
) -> str:

    return clean_text(
        get_translation(
            record
        ).get(
            "practice_readiness"
        )
    )


def get_evidence_score(
    record: dict[str, Any],
) -> float:

    appraisal = get_appraisal(
        record
    )

    scores = appraisal.get(
        "scores",
        {},
    )

    if not isinstance(
        scores,
        dict,
    ):
        return 0.0

    value = scores.get(
        "overall_evidence",
        0,
    )

    if isinstance(
        value,
        (int, float),
    ):
        return float(
            value
        )

    return 0.0


def get_statistics_score(
    record: dict[str, Any],
) -> float:

    statistics = get_statistics(
        record
    )

    scores = statistics.get(
        "scores",
        {},
    )

    if not isinstance(
        scores,
        dict,
    ):
        return 0.0

    value = scores.get(
        "overall_statistics",
        0,
    )

    if isinstance(
        value,
        (int, float),
    ):
        return float(
            value
        )

    return 0.0


def get_statistical_confidence(
    record: dict[str, Any],
) -> str:

    return clean_text(
        get_statistics(
            record
        ).get(
            "statistical_confidence"
        )
    )


def get_study_design(
    record: dict[str, Any],
) -> str:

    appraisal = get_appraisal(
        record
    )

    value = clean_text(
        appraisal.get(
            "study_design"
        )
    )

    if value:
        return value

    return clean_text(
        get_metadata(
            record
        ).get(
            "study_design"
        )
    )


def requires_full_text(
    record: dict[str, Any],
) -> bool:

    return bool(
        get_translation(
            record
        ).get(
            "requires_full_text_review",
            False,
        )
    )


def get_statistics_flags(
    record: dict[str, Any],
) -> list[str]:

    flags = get_statistics(
        record
    ).get(
        "reporting_flags",
        [],
    )

    if not isinstance(
        flags,
        list,
    ):
        return []

    return [
        clean_text(
            flag
        )
        for flag in flags
        if clean_text(
            flag
        )
    ]


# =========================================================
# SPECIALTY TEXT
# =========================================================

SPECIALTY_LABELS = {
    "regenerative_medicine": (
        "Regenerative Medicine"
    ),
    "sports_performance": (
        "Sports Performance"
    ),
    "biomechanics": (
        "Biomechanics"
    ),
    "womens_athlete_health": (
        "Women's Athlete Health"
    ),
}


def get_specialty_labels(
    record: dict[str, Any],
) -> list[str]:

    specialties = get_specialties(
        record
    )

    labels = []

    for key, label in (
        SPECIALTY_LABELS.items()
    ):

        value = specialties.get(
            key,
            {},
        )

        if (
            isinstance(
                value,
                dict,
            )
            and value.get(
                "relevant",
                False,
            )
        ):
            labels.append(
                label
            )

    return labels


# =========================================================
# SEARCH TEXT
# =========================================================

def build_search_text(
    record: dict[str, Any],
) -> str:

    metadata = get_metadata(
        record
    )

    appraisal = get_appraisal(
        record
    )

    translation = get_translation(
        record
    )

    topics = metadata.get(
        "topics",
        [],
    )

    if not isinstance(
        topics,
        list,
    ):
        topics = []

    values = [
        get_title(
            record
        ),
        get_abstract(
            record
        ),
        get_clinical_area(
            record
        ),
        get_intervention(
            record
        ),
        get_takeaway(
            record
        ),
        get_study_design(
            record
        ),
        appraisal.get(
            "population"
        ),
        metadata.get(
            "topic"
        ),
        " ".join(
            clean_text(
                topic
            )
            for topic in topics
        ),
        " ".join(
            get_specialty_labels(
                record
            )
        ),
        translation.get(
            "clinical_summary"
        ),
    ]

    return clean_text(
        " ".join(
            clean_text(
                value
            )
            for value in values
            if value
        )
    ).lower()


# =========================================================
# QUERY TOKENIZATION
# =========================================================

STOPWORDS = {
    "what",
    "does",
    "the",
    "evidence",
    "say",
    "about",
    "for",
    "with",
    "from",
    "that",
    "this",
    "are",
    "and",
    "how",
    "why",
    "which",
    "there",
    "into",
    "have",
    "has",
    "been",
    "can",
    "could",
    "would",
    "should",
    "show",
    "tell",
    "research",
    "study",
    "studies",
}


def tokenize_query(
    query: str,
) -> list[str]:

    raw_terms = re.findall(
        r"[a-z0-9]+(?:-[a-z0-9]+)?",
        query.lower(),
    )

    terms = []

    for term in raw_terms:

        if (
            len(term) >= 3
            and term not in STOPWORDS
        ):
            terms.append(
                term
            )

    return list(
        dict.fromkeys(
            terms
        )
    )


# =========================================================
# RETRIEVAL
# =========================================================

def retrieve_evidence(
    query: str,
    limit: int = DEFAULT_MAX_PAPERS,
) -> list[dict[str, Any]]:

    records = load_database()

    query_terms = tokenize_query(
        query
    )

    if not query_terms:
        return []

    scored_records = []

    for record in records:

        title = get_title(
            record
        ).lower()

        clinical_area = (
            get_clinical_area(
                record
            ).lower()
        )

        intervention = (
            get_intervention(
                record
            ).lower()
        )

        search_text = build_search_text(
            record
        )

        relevance = 0.0

        matched_terms = 0

        for term in query_terms:

            matched = False

            if term in title:
                relevance += 6.0
                matched = True

            if term in clinical_area:
                relevance += 5.0
                matched = True

            if term in intervention:
                relevance += 4.5
                matched = True

            if term in search_text:
                relevance += 1.0
                matched = True

            if matched:
                matched_terms += 1

        if relevance <= 0:
            continue

        # -------------------------------------------------
        # Reward multi-term coverage
        # -------------------------------------------------

        coverage = (
            matched_terms
            / max(
                len(
                    query_terms
                ),
                1,
            )
        )

        relevance += (
            coverage * 3.0
        )

        # -------------------------------------------------
        # Quality weighting
        # -------------------------------------------------

        evidence_score = (
            get_evidence_score(
                record
            )
        )

        statistics_score = (
            get_statistics_score(
                record
            )
        )

        quality_bonus = (
            evidence_score * 0.25
            + statistics_score * 0.15
        )

        # -------------------------------------------------
        # Practice-ready bonus
        # -------------------------------------------------

        readiness_bonus = 0.0

        if (
            get_practice_readiness(
                record
            )
            == "Practice-informing"
        ):
            readiness_bonus = 1.0

        # -------------------------------------------------
        # Full-text penalty
        # -------------------------------------------------

        full_text_penalty = (
            1.0
            if requires_full_text(
                record
            )
            else 0.0
        )

        final_score = (
            relevance
            + quality_bonus
            + readiness_bonus
            - full_text_penalty
        )

        scored_records.append(
            (
                final_score,
                record,
            )
        )

    scored_records.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        record
        for _, record
        in scored_records[
            :limit
        ]
    ]


# =========================================================
# EVIDENCE PACKET
# =========================================================

def build_evidence_packet(
    records: list[dict[str, Any]],
) -> str:

    paper_sections = []

    for index, record in enumerate(
        records,
        start=1,
    ):

        section = f"""
PAPER [{index}]

Title:
{get_title(record)}

Journal:
{get_journal(record)}

Year:
{get_year(record)}

Study design:
{get_study_design(record)}

Clinical area:
{get_clinical_area(record)}

Specialties:
{", ".join(
    get_specialty_labels(
        record
    )
)}

Intervention or exposure:
{get_intervention(record)}

Evidence score:
{get_evidence_score(record)}/10

Statistics score:
{get_statistics_score(record)}/10

Statistical confidence:
{get_statistical_confidence(record)}

Practice readiness:
{get_practice_readiness(record)}

Requires full-text review:
{requires_full_text(record)}

Practitioner takeaway:
{get_takeaway(record)}

Statistical flags:
{"; ".join(
    get_statistics_flags(
        record
    )
)}

Abstract:
{get_abstract(record)[:2400]}
"""

        paper_sections.append(
            section.strip()
        )

    return (
        "\n\n"
        "----------------------------------------"
        "\n\n"
    ).join(
        paper_sections
    )


# =========================================================
# ATHENA SYSTEM INSTRUCTIONS
# =========================================================

SYSTEM_INSTRUCTIONS = """
You are Athena, the evidence-synthesis assistant inside Optimize Evidence.

Your audience includes clinicians, sports medicine practitioners,
sports scientists, researchers, and performance professionals.

You will receive:
1. A user question.
2. A packet of scientific papers retrieved from an internal evidence database.

You must synthesize ONLY the supplied evidence packet.

CORE RULES

- Never invent a paper, result, effect size, sample size, mechanism, endpoint, or conclusion.
- Never imply that you searched literature outside the supplied evidence packet.
- Do not treat association as causation.
- Do not treat preclinical evidence as proof of clinical effectiveness.
- Do not equate statistical significance with clinical significance.
- Distinguish evidence quality from statistical quality.
- If evidence is weak, say so clearly.
- If findings conflict, describe the conflict rather than forcing consensus.
- If multiple papers require full-text review, mention this as a major limitation.
- Prefer conclusions supported across multiple stronger papers over isolated findings.
- Consider applicability to athletes when the study population differs from competitive athletes.
- Avoid treatment recommendations that go beyond the supplied evidence.
- Use cautious wording when evidence is preliminary.

CITATIONS

Use paper numbers exactly as supplied:
[1], [2], [3], etc.

Every substantive scientific claim should cite one or more supplied papers.

RESPONSE FORMAT

Use exactly these headings:

### Bottom line

Give the clearest concise answer to the user's question.

### What the evidence supports

Describe the strongest areas of agreement across the retrieved papers.

### Where the evidence is mixed

Describe disagreement, inconsistent findings, or unresolved questions.
If there is no meaningful disagreement, say so.

### Clinical interpretation

Explain what a practitioner can reasonably take from the evidence now.
Separate practical relevance from certainty.

### Confidence

Choose exactly one:
High
Moderate
Low
Very low

Then briefly explain why.

### Important limitations

List the most important limitations affecting interpretation.

### Sources used

List each cited paper as:
[number] Title
"""


# =========================================================
# SYNTHESIS
# =========================================================

def synthesize_question(
    question: str,
    max_papers: int = DEFAULT_MAX_PAPERS,
    model: str | None = None,
) -> dict[str, Any]:

    cleaned_question = clean_text(
        question
    )

    if not cleaned_question:

        return {
            "answer": (
                "Please enter a research or clinical question."
            ),
            "papers": [],
            "paper_count": 0,
            "model": None,
        }

    # -----------------------------------------------------
    # Retrieve evidence
    # -----------------------------------------------------

    records = retrieve_evidence(
        cleaned_question,
        limit=max_papers,
    )

    if not records:

        return {
            "answer": (
                "I couldn't find sufficiently relevant papers "
                "in the current Optimize Evidence database."
            ),
            "papers": [],
            "paper_count": 0,
            "model": None,
        }

    # -----------------------------------------------------
    # Build compact evidence packet
    # -----------------------------------------------------

    evidence_packet = (
        build_evidence_packet(
            records
        )
    )

    # -----------------------------------------------------
    # Resolve model
    # -----------------------------------------------------

    selected_model = (
        model
        or get_model()
    )

    # -----------------------------------------------------
    # OpenAI call
    # -----------------------------------------------------

    client = get_client()

    response = (
        client.responses.create(
            model=selected_model,
            instructions=(
                SYSTEM_INSTRUCTIONS
            ),
            input=(
                "USER QUESTION:\n\n"
                f"{cleaned_question}\n\n"
                "EVIDENCE PACKET:\n\n"
                f"{evidence_packet}"
            ),
        )
    )

    answer = clean_text(
        response.output_text
    )

    if not answer:

        answer = (
            "Athena did not return a synthesis."
        )

    # -----------------------------------------------------
    # Supporting paper metadata
    # -----------------------------------------------------

    papers = []

    for index, record in enumerate(
        records,
        start=1,
    ):

        papers.append(
            {
                "number": index,
                "title": get_title(
                    record
                ),
                "journal": get_journal(
                    record
                ),
                "year": get_year(
                    record
                ),
                "pubmed_url": get_pubmed_url(
                    record
                ),
                "clinical_area": (
                    get_clinical_area(
                        record
                    )
                ),
                "evidence_score": (
                    get_evidence_score(
                        record
                    )
                ),
                "statistics_score": (
                    get_statistics_score(
                        record
                    )
                ),
                "practice_readiness": (
                    get_practice_readiness(
                        record
                    )
                ),
                "requires_full_text": (
                    requires_full_text(
                        record
                    )
                ),
            }
        )

    return {
        "answer": answer,
        "papers": papers,
        "paper_count": len(
            papers
        ),
        "model": selected_model,
    }


# =========================================================
# SIMPLE HEALTH CHECK
# =========================================================

def athena_status() -> dict[str, Any]:
    """
    Useful for checking whether Athena has access to its
    database, model setting, and API configuration.
    """

    records = load_database()

    try:
        api_configured = bool(
            get_api_key()
        )

    except Exception:
        api_configured = False

    return {
        "database_found": (
            DATABASE_PATH.exists()
        ),
        "indexed_papers": len(
            records
        ),
        "api_configured": (
            api_configured
        ),
        "model": get_model(),
    }
