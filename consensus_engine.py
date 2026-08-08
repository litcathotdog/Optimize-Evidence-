"""
Optimize Evidence: Formula-Based Consensus Engine

Reads:
    data/evidence_database.json
    data/knowledge_graph.json

Writes:
    data/consensus.json

Purpose
-------
Synthesize multiple studies around the same clinical problem or
evidence concept.

This is NOT a meta-analysis.

The Consensus Engine does not pool effect sizes. Instead, it combines:

- number of studies
- evidence quality
- statistical quality
- study design mix
- result direction
- practice readiness
- specialist confidence
- recurring limitations
- evidence gaps

to create a transparent evidence-consensus summary.

No paid AI API is required.
"""

from __future__ import annotations

import json
import math
import re
import sys

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path("data/evidence_database.json")
GRAPH_PATH = Path("data/knowledge_graph.json")
OUTPUT_PATH = Path("data/consensus.json")


# =========================================================
# GENERAL HELPERS
# =========================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def safe_dict(
    value: Any,
) -> dict[str, Any]:
    return (
        value
        if isinstance(value, dict)
        else {}
    )


def safe_list(
    value: Any,
) -> list[Any]:
    return (
        value
        if isinstance(value, list)
        else []
    )


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


def average(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return round(
        sum(values)
        / len(values),
        2,
    )


# =========================================================
# FILE OPERATIONS
# =========================================================

def load_json_list(
    path: Path,
) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        list,
    ):
        raise ValueError(
            f"{path} must contain a JSON list."
        )

    return [
        item
        for item in data
        if isinstance(
            item,
            dict,
        )
    ]


def load_json_object(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file does not exist: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return data


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = path.with_suffix(
        ".json.tmp"
    )

    with temp_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temp_path.replace(
        path
    )


# =========================================================
# PAPER IDENTIFIERS
# =========================================================

def slugify(
    value: Any,
) -> str:
    text = clean_text(
        value
    ).lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )

    return text.strip("-")


def paper_identifier(
    record: dict[str, Any],
) -> str:
    pmid = clean_text(
        record.get(
            "pmid"
        )
    )

    if pmid:
        return (
            f"paper:pmid:{pmid}"
        )

    doi = clean_text(
        record.get(
            "doi"
        )
    ).lower()

    if doi:
        return (
            "paper:doi:"
            + slugify(doi)
        )

    metadata = safe_dict(
        record.get(
            "metadata"
        )
    )

    title = metadata.get(
        "title",
        "",
    )

    return (
        "paper:title:"
        + slugify(title)
    )


# =========================================================
# RECORD ACCESS
# =========================================================

def get_metadata(
    record: dict[str, Any],
) -> dict[str, Any]:
    return safe_dict(
        record.get(
            "metadata"
        )
    )


def get_appraisal(
    record: dict[str, Any],
) -> dict[str, Any]:
    return safe_dict(
        record.get(
            "appraisal"
        )
    )


def get_statistics(
    record: dict[str, Any],
) -> dict[str, Any]:
    return safe_dict(
        record.get(
            "statistics"
        )
    )


def get_translation(
    record: dict[str, Any],
) -> dict[str, Any]:
    return safe_dict(
        record.get(
            "clinical_translation"
        )
    )


def get_specialties(
    record: dict[str, Any],
) -> dict[str, Any]:
    return safe_dict(
        record.get(
            "specialties"
        )
    )


# =========================================================
# QUALITY EXTRACTION
# =========================================================

def get_evidence_score(
    record: dict[str, Any],
) -> float:
    appraisal = get_appraisal(
        record
    )

    scores = safe_dict(
        appraisal.get(
            "scores"
        )
    )

    return safe_float(
        scores.get(
            "overall_evidence"
        )
    )


def get_statistics_score(
    record: dict[str, Any],
) -> float:
    statistics = get_statistics(
        record
    )

    scores = safe_dict(
        statistics.get(
            "scores"
        )
    )

    return safe_float(
        scores.get(
            "overall_statistics"
        )
    )


def get_relevance_score(
    record: dict[str, Any],
) -> float:
    appraisal = get_appraisal(
        record
    )

    scores = safe_dict(
        appraisal.get(
            "scores"
        )
    )

    return safe_float(
        scores.get(
            "practitioner_relevance"
        )
    )


# =========================================================
# STUDY DESIGN WEIGHTING
# =========================================================

def design_weight(
    design: str,
) -> float:
    """
    Simple transparent evidence-hierarchy weight.

    These values do NOT replace formal risk-of-bias assessment.
    """

    text = clean_text(
        design
    ).lower()

    if (
        "systematic review" in text
        or "meta-analysis" in text
        or "meta analysis" in text
    ):
        return 1.00

    if (
        "randomized controlled trial" in text
        or "randomised controlled trial" in text
        or text == "rct"
    ):
        return 0.95

    if (
        "prospective cohort" in text
    ):
        return 0.75

    if (
        "cohort" in text
    ):
        return 0.70

    if (
        "case-control" in text
        or "case control" in text
    ):
        return 0.60

    if (
        "cross-sectional" in text
        or "cross sectional" in text
    ):
        return 0.50

    if (
        "case series" in text
    ):
        return 0.35

    if (
        "case report" in text
    ):
        return 0.25

    if (
        "animal" in text
        or "preclinical" in text
        or "in vitro" in text
    ):
        return 0.15

    return 0.45


# =========================================================
# RESULT DIRECTION
# =========================================================

def get_result_direction(
    record: dict[str, Any],
) -> str:
    translation = get_translation(
        record
    )

    direction = clean_text(
        translation.get(
            "result_direction"
        )
    ).lower()

    if direction in {
        "favorable",
        "favourable",
        "positive",
    }:
        return "favorable"

    if direction in {
        "neutral",
        "no difference",
        "no clear effect",
    }:
        return "neutral"

    if direction in {
        "unfavorable",
        "unfavourable",
        "negative",
    }:
        return "unfavorable"

    appraisal = get_appraisal(
        record
    )

    direction = clean_text(
        appraisal.get(
            "result_direction"
        )
    ).lower()

    if "favorable" in direction:
        return "favorable"

    if "neutral" in direction:
        return "neutral"

    if "unfavorable" in direction:
        return "unfavorable"

    return "unclear"


# =========================================================
# PAPER QUALITY WEIGHT
# =========================================================

def calculate_paper_weight(
    record: dict[str, Any],
) -> float:
    evidence = get_evidence_score(
        record
    )

    statistics = get_statistics_score(
        record
    )

    relevance = get_relevance_score(
        record
    )

    appraisal = get_appraisal(
        record
    )

    design = clean_text(
        appraisal.get(
            "study_design"
        )
    )

    hierarchy = design_weight(
        design
    )

    normalized_quality = (
        evidence * 0.45
        + statistics * 0.35
        + relevance * 0.20
    ) / 10

    weight = (
        normalized_quality
        * hierarchy
    )

    return round(
        clamp(
            weight,
            0.05,
            1.00,
        ),
        4,
    )


# =========================================================
# CONCEPT MAPPING
# =========================================================

def build_database_index(
    database: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        paper_identifier(
            record
        ): record
        for record in database
    }


def build_concept_papers(
    graph: dict[str, Any],
) -> dict[str, list[str]]:
    edges = safe_list(
        graph.get(
            "edges"
        )
    )

    concept_papers: dict[
        str,
        list[str],
    ] = defaultdict(list)

    for edge in edges:
        if not isinstance(
            edge,
            dict,
        ):
            continue

        source = clean_text(
            edge.get(
                "source"
            )
        )

        target = clean_text(
            edge.get(
                "target"
            )
        )

        if (
            source.startswith(
                "paper:"
            )
            and target
        ):
            concept_papers[
                target
            ].append(
                source
            )

    return {
        concept: sorted(
            set(paper_ids)
        )
        for (
            concept,
            paper_ids,
        ) in concept_papers.items()
    }


# =========================================================
# SPECIALIST CONSENSUS
# =========================================================

def calculate_specialist_consensus(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    specialty_scores: dict[
        str,
        list[float],
    ] = defaultdict(list)

    confidence_counts: dict[
        str,
        Counter,
    ] = defaultdict(
        Counter
    )

    for record in records:
        specialties = get_specialties(
            record
        )

        for (
            specialty_name,
            specialty,
        ) in specialties.items():

            if not isinstance(
                specialty,
                dict,
            ):
                continue

            if not specialty.get(
                "reviewed",
                False,
            ):
                continue

            score = specialty.get(
                "domain_score"
            )

            if isinstance(
                score,
                (int, float),
            ):
                specialty_scores[
                    specialty_name
                ].append(
                    float(score)
                )

            confidence = clean_text(
                specialty.get(
                    "specialist_confidence"
                )
            )

            if confidence:
                confidence_counts[
                    specialty_name
                ][
                    confidence
                ] += 1

    result = {}

    for specialty_name in set(
        list(
            specialty_scores.keys()
        )
        + list(
            confidence_counts.keys()
        )
    ):

        result[
            specialty_name
        ] = {
            "average_domain_score": average(
                specialty_scores.get(
                    specialty_name,
                    [],
                )
            ),
            "confidence_distribution": dict(
                confidence_counts.get(
                    specialty_name,
                    Counter(),
                )
            ),
        }

    return result


# =========================================================
# RECURRING LIMITATIONS
# =========================================================

def collect_recurring_issues(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counter = Counter()

    for record in records:
        translation = get_translation(
            record
        )

        statistics = get_statistics(
            record
        )

        specialties = get_specialties(
            record
        )

        for issue in safe_list(
            translation.get(
                "major_cautions"
            )
        ):
            text = clean_text(
                issue
            )

            if text:
                counter[
                    text
                ] += 1

        for issue in safe_list(
            statistics.get(
                "reporting_flags"
            )
        ):
            text = clean_text(
                issue
            )

            if text:
                counter[
                    text
                ] += 1

        for specialty in (
            specialties.values()
        ):

            if not isinstance(
                specialty,
                dict,
            ):
                continue

            for issue in safe_list(
                specialty.get(
                    "domain_flags"
                )
            ):
                text = clean_text(
                    issue
                )

                if text:
                    counter[
                        text
                    ] += 1

    return [
        {
            "issue": issue,
            "count": count,
        }
        for (
            issue,
            count,
        ) in counter.most_common(
            10
        )
    ]


# =========================================================
# AGREEMENT SCORE
# =========================================================

def calculate_direction_agreement(
    weighted_directions: dict[str, float],
) -> float:
    known = (
        weighted_directions.get(
            "favorable",
            0,
        )
        + weighted_directions.get(
            "neutral",
            0,
        )
        + weighted_directions.get(
            "unfavorable",
            0,
        )
    )

    if known <= 0:
        return 0.0

    strongest = max(
        weighted_directions.get(
            "favorable",
            0,
        ),
        weighted_directions.get(
            "neutral",
            0,
        ),
        weighted_directions.get(
            "unfavorable",
            0,
        ),
    )

    return round(
        (
            strongest
            / known
        )
        * 100,
        1,
    )


# =========================================================
# CONSENSUS CLASSIFICATION
# =========================================================

def determine_consensus_label(
    paper_count: int,
    avg_evidence: float | None,
    avg_statistics: float | None,
    agreement: float,
    weighted_directions: dict[str, float],
) -> str:

    if paper_count < 2:
        return "Insufficient evidence"

    known_weight = (
        weighted_directions.get(
            "favorable",
            0,
        )
        + weighted_directions.get(
            "neutral",
            0,
        )
        + weighted_directions.get(
            "unfavorable",
            0,
        )
    )

    if known_weight <= 0:
        return "Unclear"

    dominant = max(
        (
            "favorable",
            weighted_directions.get(
                "favorable",
                0,
            ),
        ),
        (
            "neutral",
            weighted_directions.get(
                "neutral",
                0,
            ),
        ),
        (
            "unfavorable",
            weighted_directions.get(
                "unfavorable",
                0,
            ),
        ),
        key=lambda item: item[1],
    )[0]

    evidence = (
        avg_evidence
        if avg_evidence is not None
        else 0
    )

    statistics = (
        avg_statistics
        if avg_statistics is not None
        else 0
    )

    quality = (
        evidence
        + statistics
    ) / 2

    if (
        agreement >= 80
        and quality >= 7
    ):
        return (
            f"Strong {dominant} consensus"
        )

    if (
        agreement >= 65
        and quality >= 5.5
    ):
        return (
            f"Moderate {dominant} consensus"
        )

    if agreement < 55:
        return "Conflicting evidence"

    return (
        f"Emerging {dominant} signal"
    )


# =========================================================
# CONSENSUS CONFIDENCE
# =========================================================

def calculate_consensus_confidence(
    paper_count: int,
    avg_evidence: float | None,
    avg_statistics: float | None,
    agreement: float,
    practice_informing: int,
) -> tuple[float, str]:

    evidence = (
        avg_evidence
        if avg_evidence is not None
        else 0
    )

    statistics = (
        avg_statistics
        if avg_statistics is not None
        else 0
    )

    volume_score = min(
        math.log2(
            paper_count + 1
        )
        / math.log2(21),
        1,
    )

    practice_fraction = (
        practice_informing
        / paper_count
        if paper_count
        else 0
    )

    score = (
        evidence * 0.30
        + statistics * 0.25
        + (
            agreement / 10
        ) * 0.25
        + (
            volume_score * 10
        ) * 0.10
        + (
            practice_fraction * 10
        ) * 0.10
    )

    score = round(
        clamp(
            score,
            0,
            10,
        ),
        1,
    )

    if score >= 8:
        label = "High"

    elif score >= 6:
        label = "Moderate"

    elif score >= 4:
        label = "Low"

    else:
        label = "Very low"

    return (
        score,
        label,
    )


# =========================================================
# PRACTITIONER SUMMARY
# =========================================================

def build_consensus_takeaway(
    concept: str,
    consensus_label: str,
    confidence_label: str,
    paper_count: int,
    practice_informing: int,
    recurring_issues: list[dict[str, Any]],
) -> str:

    if consensus_label == "Insufficient evidence":
        return (
            f"There is currently too little indexed evidence on {concept} "
            "to support a reliable consensus. Findings should be considered "
            "hypothesis-generating."
        )

    if consensus_label == "Conflicting evidence":
        statement = (
            f"Evidence concerning {concept} remains inconsistent across "
            f"{paper_count} indexed studies. The current body of evidence "
            f"has {confidence_label.lower()} overall consensus confidence."
        )

    else:
        statement = (
            f"The current evidence on {concept} shows "
            f"{consensus_label.lower()} across {paper_count} indexed studies, "
            f"with {confidence_label.lower()} overall consensus confidence."
        )

    if practice_informing > 0:
        statement += (
            f" {practice_informing} paper(s) are currently classified "
            "as potentially practice-informing."
        )

    if recurring_issues:
        statement += (
            " Interpretation should account for recurring limitations, "
            f"including {recurring_issues[0]['issue'].lower()}"
        )

    return statement


# =========================================================
# BUILD ONE CONCEPT CONSENSUS
# =========================================================

def synthesize_concept(
    concept_node: dict[str, Any],
    paper_ids: list[str],
    database_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:

    records = [
        database_index[
            paper_id
        ]
        for paper_id in paper_ids
        if paper_id in database_index
    ]

    evidence_scores: list[float] = []
    statistics_scores: list[float] = []
    relevance_scores: list[float] = []

    direction_counts = Counter()

    weighted_directions = {
        "favorable": 0.0,
        "neutral": 0.0,
        "unfavorable": 0.0,
        "unclear": 0.0,
    }

    study_designs = Counter()

    practice_informing = 0
    full_text_required = 0

    for record in records:

        evidence = get_evidence_score(
            record
        )

        statistics = get_statistics_score(
            record
        )

        relevance = get_relevance_score(
            record
        )

        if evidence > 0:
            evidence_scores.append(
                evidence
            )

        if statistics > 0:
            statistics_scores.append(
                statistics
            )

        if relevance > 0:
            relevance_scores.append(
                relevance
            )

        direction = get_result_direction(
            record
        )

        direction_counts[
            direction
        ] += 1

        weight = calculate_paper_weight(
            record
        )

        weighted_directions[
            direction
        ] += weight

        appraisal = get_appraisal(
            record
        )

        design = clean_text(
            appraisal.get(
                "study_design"
            )
        )

        if design:
            study_designs[
                design
            ] += 1

        translation = get_translation(
            record
        )

        if (
            translation.get(
                "practice_readiness"
            )
            == "Practice-informing"
        ):
            practice_informing += 1

        if translation.get(
            "requires_full_text_review",
            False,
        ):
            full_text_required += 1

    avg_evidence = average(
        evidence_scores
    )

    avg_statistics = average(
        statistics_scores
    )

    avg_relevance = average(
        relevance_scores
    )

    weighted_directions = {
        key: round(
            value,
            3,
        )
        for (
            key,
            value,
        ) in weighted_directions.items()
    }

    agreement = (
        calculate_direction_agreement(
            weighted_directions
        )
    )

    consensus_label = (
        determine_consensus_label(
            paper_count=len(
                records
            ),
            avg_evidence=avg_evidence,
            avg_statistics=avg_statistics,
            agreement=agreement,
            weighted_directions=weighted_directions,
        )
    )

    consensus_score, confidence_label = (
        calculate_consensus_confidence(
            paper_count=len(
                records
            ),
            avg_evidence=avg_evidence,
            avg_statistics=avg_statistics,
            agreement=agreement,
            practice_informing=practice_informing,
        )
    )

    recurring_issues = (
        collect_recurring_issues(
            records
        )
    )

    specialist_consensus = (
        calculate_specialist_consensus(
            records
        )
    )

    concept = clean_text(
        concept_node.get(
            "label"
        )
    )

    takeaway = (
        build_consensus_takeaway(
            concept=concept,
            consensus_label=consensus_label,
            confidence_label=confidence_label,
            paper_count=len(
                records
            ),
            practice_informing=practice_informing,
            recurring_issues=recurring_issues,
        )
    )

    return {
        "concept_id": concept_node.get(
            "id"
        ),

        "concept": concept,

        "concept_type": concept_node.get(
            "type"
        ),

        "paper_count": len(
            records
        ),

        "paper_ids": [
            paper_identifier(
                record
            )
            for record in records
        ],

        "consensus": {
            "label": consensus_label,
            "confidence_score": (
                consensus_score
            ),
            "confidence": (
                confidence_label
            ),
            "agreement_percent": (
                agreement
            ),
        },

        "evidence_quality": {
            "average_evidence_score": (
                avg_evidence
            ),
            "average_statistics_score": (
                avg_statistics
            ),
            "average_practitioner_relevance": (
                avg_relevance
            ),
        },

        "result_direction": {
            "raw_counts": {
                "favorable": (
                    direction_counts.get(
                        "favorable",
                        0,
                    )
                ),
                "neutral": (
                    direction_counts.get(
                        "neutral",
                        0,
                    )
                ),
                "unfavorable": (
                    direction_counts.get(
                        "unfavorable",
                        0,
                    )
                ),
                "unclear": (
                    direction_counts.get(
                        "unclear",
                        0,
                    )
                ),
            },

            "quality_weighted": (
                weighted_directions
            ),
        },

        "study_designs": dict(
            study_designs.most_common()
        ),

        "practice_readiness": {
            "practice_informing_papers": (
                practice_informing
            ),
            "full_text_review_required": (
                full_text_required
            ),
        },

        "specialist_consensus": (
            specialist_consensus
        ),

        "recurring_issues": (
            recurring_issues
        ),

        "practitioner_consensus_takeaway": (
            takeaway
        ),
    }


# =========================================================
# CLINICAL-PROBLEM CONSENSUS
# =========================================================

def build_clinical_problem_consensus(
    database: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    groups: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for record in database:

        translation = get_translation(
            record
        )

        problem = clean_text(
            translation.get(
                "clinical_area"
            )
        )

        if problem:
            groups[
                problem
            ].append(
                record
            )

    results = []

    for problem, records in (
        groups.items()
    ):

        synthetic_node = {
            "id": (
                "clinical_problem:"
                + slugify(problem)
            ),
            "label": problem,
            "type": (
                "clinical_problem"
            ),
        }

        database_index = {
            paper_identifier(
                record
            ): record
            for record in records
        }

        paper_ids = list(
            database_index.keys()
        )

        results.append(
            synthesize_concept(
                concept_node=synthetic_node,
                paper_ids=paper_ids,
                database_index=database_index,
            )
        )

    results.sort(
        key=lambda item: (
            item.get(
                "paper_count",
                0,
            ),
            safe_float(
                safe_dict(
                    item.get(
                        "consensus"
                    )
                ).get(
                    "confidence_score"
                )
            ),
        ),
        reverse=True,
    )

    return results


# =========================================================
# HIGH-LEVEL RESEARCH PROBLEMS
# =========================================================

def build_global_research_issues(
    database: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    counter = Counter()

    for record in database:

        issues = collect_recurring_issues(
            [
                record
            ]
        )

        for issue in issues:

            counter[
                issue["issue"]
            ] += issue[
                "count"
            ]

    return [
        {
            "issue": issue,
            "occurrences": count,
        }
        for (
            issue,
            count,
        ) in counter.most_common(
            20
        )
    ]


# =========================================================
# MAIN
# =========================================================

def main() -> int:

    print("=" * 72)
    print(
        "Optimize Evidence Consensus Engine"
    )
    print("=" * 72)

    database = load_json_list(
        DATABASE_PATH
    )

    graph = load_json_object(
        GRAPH_PATH
    )

    database_index = (
        build_database_index(
            database
        )
    )

    nodes = safe_list(
        graph.get(
            "nodes"
        )
    )

    concept_papers = (
        build_concept_papers(
            graph
        )
    )

    concept_consensus = []

    for node in nodes:

        if not isinstance(
            node,
            dict,
        ):
            continue

        if node.get(
            "type"
        ) in {
            "paper",
            "journal",
            "study_design",
        }:
            continue

        node_id = clean_text(
            node.get(
                "id"
            )
        )

        paper_ids = (
            concept_papers.get(
                node_id,
                [],
            )
        )

        if not paper_ids:
            continue

        consensus = (
            synthesize_concept(
                concept_node=node,
                paper_ids=paper_ids,
                database_index=database_index,
            )
        )

        concept_consensus.append(
            consensus
        )

    concept_consensus.sort(
        key=lambda item: (
            item.get(
                "paper_count",
                0,
            ),
            safe_float(
                safe_dict(
                    item.get(
                        "consensus"
                    )
                ).get(
                    "confidence_score"
                )
            ),
        ),
        reverse=True,
    )

    clinical_problems = (
        build_clinical_problem_consensus(
            database
        )
    )

    research_issues = (
        build_global_research_issues(
            database
        )
    )

    strong_consensus = [
        item
        for item in concept_consensus
        if "Strong" in clean_text(
            safe_dict(
                item.get(
                    "consensus"
                )
            ).get(
                "label"
            )
        )
    ]

    conflicting = [
        item
        for item in concept_consensus
        if safe_dict(
            item.get(
                "consensus"
            )
        ).get(
            "label"
        )
        == "Conflicting evidence"
    ]

    insufficient = [
        item
        for item in concept_consensus
        if safe_dict(
            item.get(
                "consensus"
            )
        ).get(
            "label"
        )
        == "Insufficient evidence"
    ]

    output = {

        "metadata": {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "version": "1.0",

            "method": (
                "Transparent formula-based evidence synthesis. "
                "This is not a meta-analysis and does not pool effect sizes."
            ),

            "source_database": str(
                DATABASE_PATH
            ),

            "source_graph": str(
                GRAPH_PATH
            ),
        },

        "overview": {
            "concepts_synthesized": len(
                concept_consensus
            ),

            "clinical_problems_synthesized": len(
                clinical_problems
            ),

            "strong_consensus_topics": len(
                strong_consensus
            ),

            "conflicting_topics": len(
                conflicting
            ),

            "insufficient_evidence_topics": len(
                insufficient
            ),
        },

        "clinical_problem_consensus": (
            clinical_problems
        ),

        "concept_consensus": (
            concept_consensus
        ),

        "strong_consensus": (
            strong_consensus
        ),

        "conflicting_evidence": (
            conflicting
        ),

        "insufficient_evidence": (
            insufficient
        ),

        "common_research_problems": (
            research_issues
        ),
    }

    save_json(
        OUTPUT_PATH,
        output,
    )

    print(
        f"Clinical problems synthesized: "
        f"{len(clinical_problems)}"
    )

    print(
        f"Evidence concepts synthesized: "
        f"{len(concept_consensus)}"
    )

    print(
        f"Strong-consensus topics: "
        f"{len(strong_consensus)}"
    )

    print(
        f"Conflicting topics: "
        f"{len(conflicting)}"
    )

    print(
        f"Insufficient-evidence topics: "
        f"{len(insufficient)}"
    )

    print(
        f"Saved to: {OUTPUT_PATH}"
    )

    print("=" * 72)

    return 0


if __name__ == "__main__":

    try:
        raise SystemExit(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\nConsensus synthesis cancelled.",
            file=sys.stderr,
        )

        raise SystemExit(130)

    except Exception as error:

        print(
            f"\nConsensus Engine failed: {error}",
            file=sys.stderr,
        )

        raise SystemExit(1)
