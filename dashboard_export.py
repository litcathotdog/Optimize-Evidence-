"""
Optimize Evidence: Dashboard Export

Reads:
    data/evidence_database.json
    data/knowledge_graph.json
    data/journal_club.json

Writes:
    data/dashboard.json

Purpose
-------
Create a compact, dashboard-friendly representation of the research
pipeline outputs.

No external packages are required.
"""

from __future__ import annotations

import json
import sys

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path("data/evidence_database.json")
GRAPH_PATH = Path("data/knowledge_graph.json")
JOURNAL_CLUB_PATH = Path("data/journal_club.json")
OUTPUT_PATH = Path("data/dashboard.json")


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def dictionary_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"{path} must contain a JSON object."
        )

    return data


def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
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


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(".json.tmp")

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


def build_specialty_summary(
    database: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    counts = Counter()

    for record in database:

        specialties = dictionary_or_empty(
            record.get("specialties")
        )

        for specialty_name, specialty_data in specialties.items():

            if not isinstance(
                specialty_data,
                dict,
            ):
                continue

            if specialty_data.get(
                "relevant",
                False,
            ):
                counts[
                    specialty_name
                ] += 1

    return [
        {
            "specialty": specialty,
            "paper_count": count,
        }
        for specialty, count in counts.most_common()
    ]


def build_practice_readiness_summary(
    database: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    counts = Counter()

    for record in database:

        translation = dictionary_or_empty(
            record.get(
                "clinical_translation"
            )
        )

        readiness = clean_text(
            translation.get(
                "practice_readiness"
            )
        )

        if readiness:
            counts[
                readiness
            ] += 1

    return [
        {
            "category": category,
            "paper_count": count,
        }
        for category, count in counts.most_common()
    ]


def build_top_papers(
    journal_club: dict[str, Any],
) -> list[dict[str, Any]]:

    top_papers = list_or_empty(
        journal_club.get(
            "top_papers"
        )
    )

    compact: list[dict[str, Any]] = []

    for paper in top_papers[:10]:

        if not isinstance(
            paper,
            dict,
        ):
            continue

        compact.append(
            {
                "paper_id": clean_text(
                    paper.get(
                        "paper_id"
                    )
                ),
                "title": clean_text(
                    paper.get(
                        "title"
                    )
                ),
                "clinical_area": clean_text(
                    paper.get(
                        "clinical_area"
                    )
                ),
                "study_design": clean_text(
                    paper.get(
                        "study_design"
                    )
                ),
                "evidence_score": safe_int(
                    paper.get(
                        "evidence_score"
                    )
                ),
                "statistics_score": safe_int(
                    paper.get(
                        "statistics_score"
                    )
                ),
                "practitioner_relevance": safe_int(
                    paper.get(
                        "practitioner_relevance"
                    )
                ),
                "journal_club_priority": (
                    paper.get(
                        "journal_club_priority",
                        0,
                    )
                ),
                "practice_readiness": clean_text(
                    paper.get(
                        "practice_readiness"
                    )
                ),
                "result_direction": clean_text(
                    paper.get(
                        "result_direction"
                    )
                ),
                "pubmed_url": clean_text(
                    paper.get(
                        "pubmed_url"
                    )
                ),
            }
        )

    return compact


def build_evidence_gap_summary(
    graph: dict[str, Any],
) -> list[dict[str, Any]]:

    gaps = list_or_empty(
        graph.get(
            "evidence_gaps"
        )
    )

    result: list[dict[str, Any]] = []

    for gap in gaps[:10]:

        if not isinstance(
            gap,
            dict,
        ):
            continue

        result.append(
            {
                "concept": clean_text(
                    gap.get(
                        "concept"
                    )
                ),
                "concept_type": clean_text(
                    gap.get(
                        "concept_type"
                    )
                ),
                "paper_count": safe_int(
                    gap.get(
                        "paper_count"
                    )
                ),
                "reasons": list_or_empty(
                    gap.get(
                        "reasons"
                    )
                ),
            }
        )

    return result


def build_conflict_summary(
    journal_club: dict[str, Any],
) -> list[dict[str, Any]]:

    conflicts = list_or_empty(
        journal_club.get(
            "conflicting_evidence"
        )
    )

    result: list[dict[str, Any]] = []

    for conflict in conflicts[:10]:

        if not isinstance(
            conflict,
            dict,
        ):
            continue

        result.append(
            {
                "concept": clean_text(
                    conflict.get(
                        "concept"
                    )
                ),
                "concept_type": clean_text(
                    conflict.get(
                        "concept_type"
                    )
                ),
                "paper_count": safe_int(
                    conflict.get(
                        "paper_count"
                    )
                ),
                "favorable": safe_int(
                    conflict.get(
                        "favorable"
                    )
                ),
                "neutral": safe_int(
                    conflict.get(
                        "neutral"
                    )
                ),
                "unfavorable": safe_int(
                    conflict.get(
                        "unfavorable"
                    )
                ),
                "discussion_point": clean_text(
                    conflict.get(
                        "discussion_point"
                    )
                ),
            }
        )

    return result


def main() -> int:

    print("=" * 72)
    print("Optimize Evidence Dashboard Export")
    print("=" * 72)

    database = load_json_list(
        DATABASE_PATH
    )

    graph = load_json_object(
        GRAPH_PATH
    )

    journal_club = load_json_object(
        JOURNAL_CLUB_PATH
    )

    paper_of_week = dictionary_or_empty(
        journal_club.get(
            "paper_of_the_week"
        )
    )

    graph_stats = dictionary_or_empty(
        graph.get(
            "statistics"
        )
    )

    executive_summary = dictionary_or_empty(
        journal_club.get(
            "executive_summary"
        )
    )

    output = {
        "metadata": {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "dashboard_version": "1.0",
        },

        "overview": {
            "total_papers": len(
                database
            ),
            "knowledge_graph_nodes": safe_int(
                graph_stats.get(
                    "total_nodes"
                )
            ),
            "knowledge_graph_edges": safe_int(
                graph_stats.get(
                    "total_edges"
                )
            ),
            "practice_informing_papers": safe_int(
                executive_summary.get(
                    "practice_informing_papers"
                )
            ),
            "high_priority_papers": safe_int(
                executive_summary.get(
                    "high_priority_papers"
                )
            ),
            "conflicting_evidence_topics": safe_int(
                executive_summary.get(
                    "conflicting_evidence_topics"
                )
            ),
            "evidence_gaps": safe_int(
                executive_summary.get(
                    "evidence_gaps_highlighted"
                )
            ),
        },

        "paper_of_the_week": (
            paper_of_week
        ),

        "top_papers": build_top_papers(
            journal_club
        ),

        "specialty_summary": (
            build_specialty_summary(
                database
            )
        ),

        "practice_readiness": (
            build_practice_readiness_summary(
                database
            )
        ),

        "evidence_gaps": (
            build_evidence_gap_summary(
                graph
            )
        ),

        "conflicting_evidence": (
            build_conflict_summary(
                journal_club
            )
        ),

        "discussion_questions": list_or_empty(
            journal_club.get(
                "discussion_questions"
            )
        ),
    }

    save_json(
        OUTPUT_PATH,
        output,
    )

    print(
        f"Dashboard records exported: {len(database)}"
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
            "\nDashboard export cancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nDashboard export failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
