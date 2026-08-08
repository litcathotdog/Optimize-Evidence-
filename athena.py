"""
Optimize Evidence — Athena

Athena is the practitioner-facing evidence synthesis layer.

Reads:
    data/consensus.json
    data/evidence_database.json

Purpose:
    - Search clinical problems and evidence concepts
    - Rank relevant consensus results
    - Retrieve supporting papers
    - Present evidence strength, agreement, limitations, and gaps
    - Preserve traceability to source studies

Athena does NOT generate new scientific conclusions.
She communicates conclusions produced by the evidence pipeline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CONSENSUS_PATH = Path("data/consensus.json")
DATABASE_PATH = Path("data/evidence_database.json")


# =========================================================
# FILE HELPERS
# =========================================================

def load_json(path: Path) -> Any:
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def safe_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> list:
    return value if isinstance(value, list) else []


# =========================================================
# LOAD ATHENA KNOWLEDGE
# =========================================================

def load_athena_data():

    consensus = load_json(CONSENSUS_PATH) or {}
    database = load_json(DATABASE_PATH) or []

    if not isinstance(consensus, dict):
        consensus = {}

    if not isinstance(database, list):
        database = []

    return consensus, database


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize(text: str) -> str:

    text = clean_text(text).lower()

    text = re.sub(
        r"[^a-z0-9\s\-]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(text: str) -> set[str]:

    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "for",
        "how",
        "in",
        "is",
        "of",
        "on",
        "the",
        "to",
        "what",
        "with",
        "does",
        "do",
        "about",
        "should",
        "can",
        "could",
        "would",
        "from",
    }

    return {
        word
        for word in normalize(text).split()
        if (
            len(word) > 2
            and word not in stop_words
        )
    }


# =========================================================
# SEARCH SCORING
# =========================================================

def relevance_score(
    query: str,
    item: dict,
) -> float:

    query_normalized = normalize(query)
    query_tokens = tokenize(query)

    concept = normalize(
        item.get("concept", "")
    )

    concept_tokens = tokenize(concept)

    score = 0.0

    # Exact phrase match
    if (
        query_normalized
        and query_normalized in concept
    ):
        score += 10

    if (
        concept
        and concept in query_normalized
    ):
        score += 8

    # Token overlap
    overlap = (
        query_tokens
        & concept_tokens
    )

    score += len(overlap) * 3

    # Consensus takeaway
    takeaway = normalize(
        item.get(
            "practitioner_consensus_takeaway",
            "",
        )
    )

    takeaway_tokens = tokenize(takeaway)

    score += (
        len(
            query_tokens
            & takeaway_tokens
        )
        * 1.5
    )

    # Recurring issues
    for issue in safe_list(
        item.get("recurring_issues")
    ):

        issue_text = normalize(
            safe_dict(issue).get(
                "issue",
                ""
            )
        )

        issue_tokens = tokenize(
            issue_text
        )

        score += (
            len(
                query_tokens
                & issue_tokens
            )
            * 0.75
        )

    # Slight preference for concepts
    # backed by more papers.
    paper_count = item.get(
        "paper_count",
        0,
    )

    try:
        paper_count = int(
            paper_count
        )
    except (TypeError, ValueError):
        paper_count = 0

    score += min(
        paper_count / 20,
        2,
    )

    return round(
        score,
        3,
    )


# =========================================================
# BUILD SEARCH INDEX
# =========================================================

def build_search_index(
    consensus: dict,
) -> list[dict]:

    results = []

    for item in safe_list(
        consensus.get(
            "clinical_problem_consensus"
        )
    ):

        if not isinstance(item, dict):
            continue

        copy = dict(item)

        copy["_athena_source"] = (
            "clinical_problem"
        )

        results.append(copy)

    for item in safe_list(
        consensus.get(
            "concept_consensus"
        )
    ):

        if not isinstance(item, dict):
            continue

        copy = dict(item)

        copy["_athena_source"] = (
            "evidence_concept"
        )

        results.append(copy)

    return results


# =========================================================
# SEARCH CONSENSUS
# =========================================================

def search_consensus(
    query: str,
    limit: int = 5,
) -> list[dict]:

    consensus, _ = load_athena_data()

    index = build_search_index(
        consensus
    )

    ranked = []

    for item in index:

        score = relevance_score(
            query,
            item,
        )

        if score <= 0:
            continue

        result = dict(item)

        result["_athena_relevance"] = (
            score
        )

        ranked.append(result)

    ranked.sort(
        key=lambda item: (
            item.get(
                "_athena_relevance",
                0,
            ),
            item.get(
                "paper_count",
                0,
            ),
        ),
        reverse=True,
    )

    return ranked[:limit]


# =========================================================
# PAPER INDEX
# =========================================================

def paper_identifier(
    record: dict,
) -> str:

    pmid = clean_text(
        record.get("pmid")
    )

    if pmid:
        return f"paper:pmid:{pmid}"

    doi = clean_text(
        record.get("doi")
    ).lower()

    if doi:
        safe_doi = re.sub(
            r"[^a-z0-9]+",
            "-",
            doi,
        ).strip("-")

        return f"paper:doi:{safe_doi}"

    metadata = safe_dict(
        record.get("metadata")
    )

    title = normalize(
        metadata.get(
            "title",
            ""
        )
    )

    title = re.sub(
        r"[^a-z0-9]+",
        "-",
        title,
    ).strip("-")

    return f"paper:title:{title}"


def build_paper_index(
    database: list,
) -> dict[str, dict]:

    return {
        paper_identifier(record): record
        for record in database
        if isinstance(record, dict)
    }


# =========================================================
# SUPPORTING PAPERS
# =========================================================

def get_supporting_papers(
    consensus_item: dict,
    limit: int = 10,
) -> list[dict]:

    _, database = load_athena_data()

    index = build_paper_index(
        database
    )

    paper_ids = safe_list(
        consensus_item.get(
            "paper_ids"
        )
    )

    papers = []

    for paper_id in paper_ids:

        paper = index.get(
            paper_id
        )

        if not paper:
            continue

        papers.append(paper)

    # Prefer stronger evidence papers.
    def paper_score(record):

        appraisal = safe_dict(
            record.get("appraisal")
        )

        scores = safe_dict(
            appraisal.get("scores")
        )

        try:
            return float(
                scores.get(
                    "overall_evidence",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return 0

    papers.sort(
        key=paper_score,
        reverse=True,
    )

    return papers[:limit]


# =========================================================
# RESEARCH GAP EXTRACTION
# =========================================================

def extract_research_gap(
    item: dict,
) -> str:

    issues = safe_list(
        item.get(
            "recurring_issues"
        )
    )

    if not issues:
        return (
            "No recurring evidence gap has "
            "yet been identified."
        )

    strongest_issue = safe_dict(
        issues[0]
    )

    issue = clean_text(
        strongest_issue.get(
            "issue"
        )
    )

    if not issue:
        return (
            "Evidence limitations remain "
            "insufficiently characterized."
        )

    return issue


# =========================================================
# SPECIALIST PERSPECTIVES
# =========================================================

def get_specialist_perspectives(
    item: dict,
) -> list[dict]:

    specialists = safe_dict(
        item.get(
            "specialist_consensus"
        )
    )

    output = []

    for name, result in (
        specialists.items()
    ):

        if not isinstance(
            result,
            dict,
        ):
            continue

        output.append(
            {
                "specialty": name,

                "average_domain_score":
                    result.get(
                        "average_domain_score"
                    ),

                "confidence_distribution":
                    result.get(
                        "confidence_distribution",
                        {},
                    ),
            }
        )

    output.sort(
        key=lambda item: (
            item.get(
                "average_domain_score"
            )
            or 0
        ),
        reverse=True,
    )

    return output


# =========================================================
# ATHENA RESPONSE
# =========================================================

def build_athena_response(
    query: str,
) -> dict:

    matches = search_consensus(
        query=query,
        limit=5,
    )

    if not matches:

        return {
            "found": False,

            "query": query,

            "message": (
                "Athena could not identify a "
                "relevant evidence consensus "
                "for this question."
            ),

            "suggestion": (
                "Try a broader clinical topic, "
                "condition, intervention, or "
                "performance question."
            ),
        }

    primary = matches[0]

    consensus = safe_dict(
        primary.get(
            "consensus"
        )
    )

    evidence = safe_dict(
        primary.get(
            "evidence_quality"
        )
    )

    direction = safe_dict(
        primary.get(
            "result_direction"
        )
    )

    readiness = safe_dict(
        primary.get(
            "practice_readiness"
        )
    )

    supporting_papers = (
        get_supporting_papers(
            primary,
            limit=10,
        )
    )

    specialists = (
        get_specialist_perspectives(
            primary
        )
    )

    research_gap = (
        extract_research_gap(
            primary
        )
    )

    return {

        "found": True,

        "query": query,

        "topic": primary.get(
            "concept"
        ),

        "topic_type": primary.get(
            "concept_type"
        ),

        "evidence_status": (
            consensus.get(
                "label"
            )
        ),

        "consensus_confidence": (
            consensus.get(
                "confidence"
            )
        ),

        "consensus_confidence_score": (
            consensus.get(
                "confidence_score"
            )
        ),

        "agreement_percent": (
            consensus.get(
                "agreement_percent"
            )
        ),

        "paper_count": primary.get(
            "paper_count",
            0,
        ),

        "evidence_quality": (
            evidence.get(
                "average_evidence_score"
            )
        ),

        "statistical_quality": (
            evidence.get(
                "average_statistics_score"
            )
        ),

        "practitioner_relevance": (
            evidence.get(
                "average_practitioner_relevance"
            )
        ),

        "result_direction": direction,

        "practice_informing_papers": (
            readiness.get(
                "practice_informing_papers",
                0,
            )
        ),

        "full_text_review_required": (
            readiness.get(
                "full_text_review_required",
                0,
            )
        ),

        "athena_interpretation": (
            primary.get(
                "practitioner_consensus_takeaway"
            )
        ),

        "research_gap": research_gap,

        "recurring_issues": (
            primary.get(
                "recurring_issues",
                [],
            )
        ),

        "specialist_perspectives": (
            specialists
        ),

        "supporting_papers": (
            supporting_papers
        ),

        "related_topics": [
            {
                "concept": item.get(
                    "concept"
                ),

                "paper_count": item.get(
                    "paper_count"
                ),

                "consensus": safe_dict(
                    item.get(
                        "consensus"
                    )
                ).get(
                    "label"
                ),
            }

            for item in matches[1:]
        ],
    }


# =========================================================
# SIMPLE TEST
# =========================================================

if __name__ == "__main__":

    print(
        "ATHENA — Optimize Evidence"
    )

    print(
        "Ask a clinical evidence question."
    )

    query = input(
        "\nQuestion: "
    )

    result = build_athena_response(
        query
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )
