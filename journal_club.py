"""
Optimize Evidence: Formula-Based Journal Club Editor

Reads:
    data/knowledge_graph.json
    data/evidence_database.json

Writes:
    data/journal_club.json

Purpose
-------
Generate a structured weekly journal-club briefing from the evidence
knowledge graph.

The Journal Club Editor:
- identifies the highest-priority papers
- selects a paper of the week
- highlights practice-informing studies
- surfaces conflicting evidence
- identifies evidence gaps
- groups important studies by specialty
- produces concise discussion prompts

No external AI API is required.
"""

from __future__ import annotations

import json
import re
import sys

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GRAPH_PATH = Path("data/knowledge_graph.json")
DATABASE_PATH = Path("data/evidence_database.json")
OUTPUT_PATH = Path("data/journal_club.json")


# ===========================================================================
# HELPERS
# ===========================================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def dictionary_or_empty(
    value: Any,
) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    return {}


def list_or_empty(
    value: Any,
) -> list[Any]:
    if isinstance(value, list):
        return value

    return []


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

    if not isinstance(data, dict):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return data


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

    if not isinstance(data, list):
        raise ValueError(
            f"{path} must contain a JSON list."
        )

    return [
        item
        for item in data
        if isinstance(item, dict)
    ]


def save_json(
    path: Path,
    data: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        ".json.tmp"
    )

    with temporary_path.open(
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

    temporary_path.replace(path)


# ===========================================================================
# DATABASE INDEX
# ===========================================================================

def paper_identity(
    record: dict[str, Any],
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
        doi_slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            doi,
        ).strip("-")

        return f"paper:doi:{doi_slug}"

    metadata = dictionary_or_empty(
        record.get("metadata")
    )

    title = clean_text(
        metadata.get("title")
    ).lower()

    title_slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        title,
    ).strip("-")

    return f"paper:title:{title_slug}"


def build_database_index(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        paper_identity(record): record
        for record in records
    }


# ===========================================================================
# PAPER DETAILS
# ===========================================================================

def get_paper_details(
    paper_id: str,
    graph_node: dict[str, Any],
    database_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    record = database_index.get(
        paper_id,
        {},
    )

    metadata = dictionary_or_empty(
        record.get("metadata")
    )

    appraisal = dictionary_or_empty(
        record.get("appraisal")
    )

    statistics = dictionary_or_empty(
        record.get("statistics")
    )

    translation = dictionary_or_empty(
        record.get("clinical_translation")
    )

    specialties = dictionary_or_empty(
        record.get("specialties")
    )

    specialist_takeaways: dict[str, str] = {}

    for (
        specialty_name,
        specialty_data,
    ) in specialties.items():

        if not isinstance(
            specialty_data,
            dict,
        ):
            continue

        if not specialty_data.get(
            "reviewed",
            False,
        ):
            continue

        takeaway = clean_text(
            specialty_data.get(
                "specialist_takeaway"
            )
        )

        if takeaway:
            specialist_takeaways[
                specialty_name
            ] = takeaway

    return {
        "paper_id": paper_id,
        "pmid": clean_text(
            record.get("pmid")
        ),
        "doi": clean_text(
            record.get("doi")
        ),
        "title": clean_text(
            metadata.get("title")
            or graph_node.get("label")
        ),
        "journal": clean_text(
            metadata.get("journal")
        ),
        "publication_date": clean_text(
            metadata.get(
                "publication_date"
            )
        ),
        "pubmed_url": clean_text(
            metadata.get("pubmed_url")
        ),
        "study_design": clean_text(
            appraisal.get(
                "study_design"
            )
        ),
        "sample_size": appraisal.get(
            "sample_size"
        ),
        "evidence_strength": clean_text(
            appraisal.get(
                "evidence_strength"
            )
        ),
        "risk_of_bias": clean_text(
            appraisal.get(
                "risk_of_bias"
            )
        ),
        "statistical_confidence": clean_text(
            statistics.get(
                "statistical_confidence"
            )
        ),
        "practice_readiness": clean_text(
            translation.get(
                "practice_readiness"
            )
        ),
        "clinical_area": clean_text(
            translation.get(
                "clinical_area"
            )
        ),
        "result_direction": clean_text(
            graph_node.get(
                "result_direction"
            )
        ),
        "clinical_summary": clean_text(
            translation.get(
                "clinical_summary"
            )
        ),
        "practitioner_takeaway": clean_text(
            translation.get(
                "practitioner_takeaway"
            )
        ),
        "research_takeaway": clean_text(
            translation.get(
                "research_takeaway"
            )
        ),
        "major_cautions": list_or_empty(
            translation.get(
                "major_cautions"
            )
        ),
        "specialist_takeaways": (
            specialist_takeaways
        ),
        "evidence_score": safe_int(
            graph_node.get(
                "evidence_score"
            )
        ),
        "statistics_score": safe_int(
            graph_node.get(
                "statistics_score"
            )
        ),
        "practitioner_relevance": safe_int(
            graph_node.get(
                "practitioner_relevance"
            )
        ),
        "translation_priority": safe_int(
            graph_node.get(
                "translation_priority"
            )
        ),
        "requires_full_text_review": bool(
            graph_node.get(
                "requires_full_text_review",
                False,
            )
        ),
    }


# ===========================================================================
# PAPER RANKING
# ===========================================================================

def paper_priority_score(
    paper: dict[str, Any],
) -> float:
    """
    Journal-club priority score.

    Evidence quality       30%
    Statistics quality     20%
    Practitioner relevance 25%
    Translation priority   25%
    """

    score = (
        paper["evidence_score"] * 0.30
        + paper["statistics_score"] * 0.20
        + paper["practitioner_relevance"] * 0.25
        + paper["translation_priority"] * 0.25
    )

    if (
        paper.get(
            "practice_readiness"
        )
        == "Practice-informing"
    ):
        score += 0.75

    if (
        paper.get(
            "result_direction"
        )
        == "unclear"
    ):
        score -= 0.25

    return round(
        score,
        2,
    )


def rank_papers(
    graph: dict[str, Any],
    database_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    nodes = list_or_empty(
        graph.get("nodes")
    )

    papers: list[
        dict[str, Any]
    ] = []

    for node in nodes:

        if not isinstance(
            node,
            dict,
        ):
            continue

        if node.get(
            "type"
        ) != "paper":
            continue

        paper_id = clean_text(
            node.get("id")
        )

        paper = get_paper_details(
            paper_id=paper_id,
            graph_node=node,
            database_index=database_index,
        )

        paper[
            "journal_club_priority"
        ] = paper_priority_score(
            paper
        )

        papers.append(
            paper
        )

    papers.sort(
        key=lambda paper: (
            paper.get(
                "journal_club_priority",
                0,
            ),
            paper.get(
                "evidence_score",
                0,
            ),
            paper.get(
                "statistics_score",
                0,
            ),
        ),
        reverse=True,
    )

    return papers


# ===========================================================================
# PAPER OF THE WEEK
# ===========================================================================

def select_paper_of_week(
    ranked_papers: list[dict[str, Any]],
) -> dict[str, Any] | None:

    if not ranked_papers:
        return None

    # Prefer papers with meaningful practitioner relevance.
    candidates = [
        paper
        for paper in ranked_papers
        if paper.get(
            "practitioner_relevance",
            0,
        ) >= 6
    ]

    if not candidates:
        candidates = ranked_papers

    paper = candidates[0]

    why_selected: list[str] = []

    if paper.get(
        "evidence_score",
        0,
    ) >= 7:
        why_selected.append(
            "High evidence-quality score."
        )

    if paper.get(
        "statistics_score",
        0,
    ) >= 7:
        why_selected.append(
            "Strong statistical-reporting score."
        )

    if paper.get(
        "practitioner_relevance",
        0,
    ) >= 8:
        why_selected.append(
            "Highly relevant to practitioners."
        )

    if (
        paper.get(
            "practice_readiness"
        )
        == "Practice-informing"
    ):
        why_selected.append(
            "Classified as potentially practice-informing."
        )

    if paper.get(
        "specialist_takeaways"
    ):
        why_selected.append(
            "Received relevant specialty review."
        )

    if not why_selected:
        why_selected.append(
            "Highest composite journal-club priority score."
        )

    return {
        **paper,
        "why_selected": (
            why_selected
        ),
    }


# ===========================================================================
# SPECIALTY GROUPING
# ===========================================================================

def group_by_specialty(
    ranked_papers: list[dict[str, Any]],
    database_index: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    grouped: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for paper in ranked_papers:

        record = database_index.get(
            paper.get(
                "paper_id",
                "",
            ),
            {},
        )

        specialties = dictionary_or_empty(
            record.get(
                "specialties"
            )
        )

        for (
            specialty_name,
            specialty_data,
        ) in specialties.items():

            if not isinstance(
                specialty_data,
                dict,
            ):
                continue

            if not specialty_data.get(
                "relevant",
                False,
            ):
                continue

            grouped[
                specialty_name
            ].append(
                {
                    "paper_id": paper[
                        "paper_id"
                    ],
                    "title": paper[
                        "title"
                    ],
                    "journal_club_priority": (
                        paper[
                            "journal_club_priority"
                        ]
                    ),
                    "evidence_score": (
                        paper[
                            "evidence_score"
                        ]
                    ),
                    "specialist_confidence": clean_text(
                        specialty_data.get(
                            "specialist_confidence"
                        )
                    ),
                    "specialist_takeaway": clean_text(
                        specialty_data.get(
                            "specialist_takeaway"
                        )
                    ),
                }
            )

    for specialty in grouped:
        grouped[
            specialty
        ] = grouped[
            specialty
        ][:5]

    return dict(
        grouped
    )


# ===========================================================================
# PRACTICE-INFORMING PAPERS
# ===========================================================================

def get_practice_informing_papers(
    ranked_papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    return [
        {
            "paper_id": paper[
                "paper_id"
            ],
            "title": paper[
                "title"
            ],
            "clinical_area": paper[
                "clinical_area"
            ],
            "evidence_strength": paper[
                "evidence_strength"
            ],
            "statistical_confidence": paper[
                "statistical_confidence"
            ],
            "practitioner_takeaway": paper[
                "practitioner_takeaway"
            ],
        }
        for paper in ranked_papers
        if paper.get(
            "practice_readiness"
        )
        == "Practice-informing"
    ][:10]


# ===========================================================================
# CONFLICTING EVIDENCE
# ===========================================================================

def identify_conflicts(
    graph: dict[str, Any],
) -> list[dict[str, Any]]:

    syntheses = list_or_empty(
        graph.get(
            "evidence_synthesis"
        )
    )

    conflicts: list[
        dict[str, Any]
    ] = []

    for synthesis in syntheses:

        if not isinstance(
            synthesis,
            dict,
        ):
            continue

        directions = dictionary_or_empty(
            synthesis.get(
                "result_direction"
            )
        )

        favorable = safe_int(
            directions.get(
                "favorable"
            )
        )

        neutral = safe_int(
            directions.get(
                "neutral"
            )
        )

        unfavorable = safe_int(
            directions.get(
                "unfavorable"
            )
        )

        known_results = (
            favorable
            + neutral
            + unfavorable
        )

        if known_results < 3:
            continue

        distinct_directions = sum(
            1
            for count in (
                favorable,
                neutral,
                unfavorable,
            )
            if count > 0
        )

        if distinct_directions < 2:
            continue

        conflicts.append(
            {
                "concept": clean_text(
                    synthesis.get(
                        "concept"
                    )
                ),
                "concept_type": clean_text(
                    synthesis.get(
                        "concept_type"
                    )
                ),
                "paper_count": safe_int(
                    synthesis.get(
                        "paper_count"
                    )
                ),
                "favorable": favorable,
                "neutral": neutral,
                "unfavorable": unfavorable,
                "average_evidence_score": (
                    synthesis.get(
                        "average_evidence_score"
                    )
                ),
                "discussion_point": (
                    "Evidence direction is inconsistent across the "
                    "currently indexed studies. Differences in study "
                    "design, population, intervention protocol, comparator, "
                    "or outcome definition should be examined."
                ),
            }
        )

    conflicts.sort(
        key=lambda conflict: (
            conflict.get(
                "paper_count",
                0,
            ),
            conflict.get(
                "average_evidence_score",
                0,
            )
            or 0,
        ),
        reverse=True,
    )

    return conflicts[:10]


# ===========================================================================
# EVIDENCE GAPS
# ===========================================================================

def select_evidence_gaps(
    graph: dict[str, Any],
) -> list[dict[str, Any]]:

    gaps = list_or_empty(
        graph.get(
            "evidence_gaps"
        )
    )

    sorted_gaps = sorted(
        [
            gap
            for gap in gaps
            if isinstance(
                gap,
                dict,
            )
        ],
        key=lambda gap: (
            safe_int(
                gap.get(
                    "paper_count"
                )
            ),
            clean_text(
                gap.get(
                    "concept"
                )
            ),
        ),
        reverse=True,
    )

    return sorted_gaps[:10]


# ===========================================================================
# DISCUSSION QUESTIONS
# ===========================================================================

def build_discussion_questions(
    paper_of_week: dict[str, Any] | None,
    conflicts: list[dict[str, Any]],
    evidence_gaps: list[dict[str, Any]],
) -> list[str]:

    questions: list[str] = []

    if paper_of_week:

        study_design = clean_text(
            paper_of_week.get(
                "study_design"
            )
        )

        questions.append(
            (
                f"Does the {study_design.lower() if study_design else 'study'} "
                "design justify the strength of the authors' conclusions?"
            )
        )

        questions.append(
            (
                "Are the reported effects large enough to be clinically "
                "meaningful, rather than merely statistically significant?"
            )
        )

        questions.append(
            (
                "How closely does the study population resemble the patients "
                "or athletes seen in actual practice?"
            )
        )

        if paper_of_week.get(
            "requires_full_text_review"
        ):
            questions.append(
                (
                    "Which methodological details must be confirmed in the "
                    "full text before this evidence should influence practice?"
                )
            )

    if conflicts:

        concept = clean_text(
            conflicts[0].get(
                "concept"
            )
        )

        questions.append(
            (
                f"Why might studies concerning {concept} be producing "
                "different result directions?"
            )
        )

    if evidence_gaps:

        concept = clean_text(
            evidence_gaps[0].get(
                "concept"
            )
        )

        questions.append(
            (
                f"What study would most efficiently reduce the current "
                f"evidence gap around {concept}?"
            )
        )

    return questions[:6]


# ===========================================================================
# EXECUTIVE SUMMARY
# ===========================================================================

def generate_executive_summary(
    ranked_papers: list[dict[str, Any]],
    practice_informing: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    evidence_gaps: list[dict[str, Any]],
) -> dict[str, Any]:

    high_priority = [
        paper
        for paper in ranked_papers
        if paper.get(
            "journal_club_priority",
            0,
        ) >= 7
    ]

    full_text = [
        paper
        for paper in ranked_papers
        if paper.get(
            "requires_full_text_review"
        )
    ]

    return {
        "papers_reviewed": len(
            ranked_papers
        ),
        "high_priority_papers": len(
            high_priority
        ),
        "practice_informing_papers": len(
            practice_informing
        ),
        "conflicting_evidence_topics": len(
            conflicts
        ),
        "evidence_gaps_highlighted": len(
            evidence_gaps
        ),
        "papers_flagged_for_full_text_review": len(
            full_text
        ),
    }


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> int:

    print("=" * 72)
    print(
        "Optimize Evidence Journal Club Editor"
    )
    print("=" * 72)

    graph = load_json_object(
        GRAPH_PATH
    )

    database = load_json_list(
        DATABASE_PATH
    )

    database_index = (
        build_database_index(
            database
        )
    )

    ranked_papers = rank_papers(
        graph=graph,
        database_index=database_index,
    )

    paper_of_week = (
        select_paper_of_week(
            ranked_papers
        )
    )

    practice_informing = (
        get_practice_informing_papers(
            ranked_papers
        )
    )

    specialty_highlights = (
        group_by_specialty(
            ranked_papers=ranked_papers,
            database_index=database_index,
        )
    )

    conflicts = (
        identify_conflicts(
            graph
        )
    )

    evidence_gaps = (
        select_evidence_gaps(
            graph
        )
    )

    discussion_questions = (
        build_discussion_questions(
            paper_of_week=paper_of_week,
            conflicts=conflicts,
            evidence_gaps=evidence_gaps,
        )
    )

    executive_summary = (
        generate_executive_summary(
            ranked_papers=ranked_papers,
            practice_informing=practice_informing,
            conflicts=conflicts,
            evidence_gaps=evidence_gaps,
        )
    )

    output = {
        "metadata": {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "journal_club_version": "1.0",
            "source_graph": str(
                GRAPH_PATH
            ),
            "source_database": str(
                DATABASE_PATH
            ),
            "method": (
                "Formula-based ranking and synthesis using the "
                "evidence appraisal, statistical review, clinical "
                "translation, specialty review, and knowledge graph."
            ),
        },

        "executive_summary": (
            executive_summary
        ),

        "paper_of_the_week": (
            paper_of_week
        ),

        "top_papers": (
            ranked_papers[:10]
        ),

        "practice_informing_papers": (
            practice_informing
        ),

        "specialty_highlights": (
            specialty_highlights
        ),

        "conflicting_evidence": (
            conflicts
        ),

        "evidence_gaps": (
            evidence_gaps
        ),

        "discussion_questions": (
            discussion_questions
        ),
    }

    save_json(
        OUTPUT_PATH,
        output
    )

    print(
        f"Papers ranked: {len(ranked_papers)}"
    )

    print(
        f"Practice-informing papers: "
        f"{len(practice_informing)}"
    )

    print(
        f"Conflicting evidence topics: "
        f"{len(conflicts)}"
    )

    print(
        f"Evidence gaps highlighted: "
        f"{len(evidence_gaps)}"
    )

    if paper_of_week:
        print(
            "Paper of the week: "
            f"{paper_of_week.get('title', '')}"
        )

    print()

    print(
        f"Journal club saved to: "
        f"{OUTPUT_PATH}"
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
            "\nJournal club generation cancelled.",
            file=sys.stderr,
        )

        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nJournal Club Editor failed: {error}",
            file=sys.stderr,
        )

        raise SystemExit(1)
