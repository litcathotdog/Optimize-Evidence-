"""
Optimize Evidence: Canonical Evidence Database Builder

Purpose
-------
Merge the outputs of the existing research pipeline into one canonical
evidence database.

Current source files:
    data/papers.json
    data/appraised_papers.json
    data/statistically_reviewed_papers.json
    data/clinically_translated_papers.json

Output:
    data/evidence_database.json

Each paper is stored only once.

Canonical structure:
{
    "pmid": "...",
    "doi": "...",
    "metadata": {...},
    "appraisal": {...},
    "statistics": {...},
    "clinical_translation": {...},
    "specialties": {...},
    "journal_club": {...},
    "pipeline": {...}
}

No external packages are required.
"""

from __future__ import annotations

import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------

PAPERS_PATH = Path("data/papers.json")
APPRAISED_PATH = Path("data/appraised_papers.json")
STATISTICS_PATH = Path("data/statistically_reviewed_papers.json")
TRANSLATED_PATH = Path("data/clinically_translated_papers.json")

OUTPUT_PATH = Path("data/evidence_database.json")


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def clean_text(value: Any) -> str:
    """
    Convert a value to a clean single-line string.
    """
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_doi(value: Any) -> str:
    """
    Normalize DOI values so duplicate articles resolve to the same key.
    """
    doi = clean_text(value).lower()

    doi = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        doi,
    )

    return doi


def normalize_title(value: Any) -> str:
    """
    Normalize a title for fallback duplicate matching.
    """
    title = clean_text(value).lower()

    return re.sub(
        r"[^a-z0-9]+",
        "",
        title,
    )


def paper_identity(paper: dict[str, Any]) -> str:
    """
    Determine a stable paper identifier.

    Priority:
    1. PMID
    2. DOI
    3. Normalized title
    """

    pmid = clean_text(paper.get("pmid"))

    if pmid:
        return f"pmid:{pmid}"

    doi = normalize_doi(paper.get("doi"))

    if doi:
        return f"doi:{doi}"

    title = normalize_title(paper.get("title"))

    if title:
        return f"title:{title}"

    raise ValueError(
        "Paper does not contain PMID, DOI, or title."
    )


def load_json_list(
    path: Path,
    required: bool = False,
) -> list[dict[str, Any]]:
    """
    Load a JSON list.

    Optional source files return an empty list if they do not exist.
    """

    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"Required file does not exist: {path}"
            )

        print(
            f"Optional source not found: {path}. "
            "Continuing without it."
        )
        return []

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


def save_json(
    path: Path,
    data: list[dict[str, Any]],
) -> None:
    """
    Save JSON atomically to reduce the chance of corrupting the database.
    """

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


def dictionary_or_empty(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    return {}


def list_or_empty(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value

    return []


# ---------------------------------------------------------------------------
# Metadata construction
# ---------------------------------------------------------------------------

def build_metadata(
    paper: dict[str, Any],
) -> dict[str, Any]:
    """
    Extract the original bibliographic and PubMed information.
    """

    return {
        "title": clean_text(
            paper.get("title")
        ),
        "abstract": clean_text(
            paper.get("abstract")
        ),
        "authors": list_or_empty(
            paper.get("authors")
        ),
        "journal": clean_text(
            paper.get("journal")
        ),
        "publication_date": clean_text(
            paper.get("publication_date")
        ),
        "electronic_publication_date": clean_text(
            paper.get(
                "electronic_publication_date"
            )
        ),
        "print_publication_date": clean_text(
            paper.get(
                "print_publication_date"
            )
        ),
        "publication_types": list_or_empty(
            paper.get("publication_types")
        ),
        "topic": clean_text(
            paper.get("topic")
        ),
        "topics": list_or_empty(
            paper.get("topics")
        ),
        "study_type": clean_text(
            paper.get("study_type")
        ),
        "pubmed_url": clean_text(
            paper.get("pubmed_url")
        ),
        "retrieved_at": clean_text(
            paper.get("retrieved_at")
        ),
        "librarian_relevance_score": (
            paper.get("relevance_score")
        ),
    }


# ---------------------------------------------------------------------------
# Existing specialty support
# ---------------------------------------------------------------------------

def default_specialty_structure() -> dict[str, Any]:
    """
    Reserve stable sections for current specialty reviewers.

    Future reviewers should fill these dictionaries rather than creating
    separate copies of the paper.
    """

    return {
        "regenerative_medicine": {
            "reviewed": False,
            "relevant": None,
        },
        "sports_performance": {
            "reviewed": False,
            "relevant": None,
        },
        "biomechanics": {
            "reviewed": False,
            "relevant": None,
        },
        "womens_athlete_health": {
            "reviewed": False,
            "relevant": None,
        },
    }


def merge_specialties(
    existing: Any,
) -> dict[str, Any]:
    """
    Preserve specialty information if the master database already exists.
    """

    template = default_specialty_structure()

    if not isinstance(existing, dict):
        return template

    for specialty_name, specialty_data in existing.items():
        if specialty_name not in template:
            template[specialty_name] = specialty_data
            continue

        if isinstance(specialty_data, dict):
            template[specialty_name].update(
                specialty_data
            )

    return template


# ---------------------------------------------------------------------------
# Build source indexes
# ---------------------------------------------------------------------------

def index_papers(
    papers: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Build an identity -> paper index.
    """

    result: dict[str, dict[str, Any]] = {}

    for paper in papers:
        try:
            identity = paper_identity(paper)
        except ValueError as error:
            print(
                f"Skipping paper with no usable identifier: {error}"
            )
            continue

        result[identity] = paper

    return result


# ---------------------------------------------------------------------------
# Canonical record construction
# ---------------------------------------------------------------------------

def build_canonical_record(
    base_paper: dict[str, Any],
    appraisal_paper: dict[str, Any] | None,
    statistics_paper: dict[str, Any] | None,
    translation_paper: dict[str, Any] | None,
    existing_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Merge all pipeline stages into one canonical record.
    """

    appraisal_paper = appraisal_paper or {}
    statistics_paper = statistics_paper or {}
    translation_paper = translation_paper or {}
    existing_record = existing_record or {}

    pmid = clean_text(
        base_paper.get("pmid")
        or appraisal_paper.get("pmid")
        or statistics_paper.get("pmid")
        or translation_paper.get("pmid")
    )

    doi = normalize_doi(
        base_paper.get("doi")
        or appraisal_paper.get("doi")
        or statistics_paper.get("doi")
        or translation_paper.get("doi")
    )

    appraisal = dictionary_or_empty(
        appraisal_paper.get(
            "formulaic_appraisal"
        )
    )

    statistics = dictionary_or_empty(
        statistics_paper.get(
            "statistics_review"
        )
    )

    clinical_translation = dictionary_or_empty(
        translation_paper.get(
            "clinical_translation"
        )
    )

    existing_specialties = existing_record.get(
        "specialties"
    )

    existing_journal_club = dictionary_or_empty(
        existing_record.get(
            "journal_club"
        )
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    record = {
        "pmid": pmid,
        "doi": doi,
        "metadata": build_metadata(
            base_paper
        ),
        "appraisal": appraisal,
        "statistics": statistics,
        "clinical_translation": (
            clinical_translation
        ),
        "specialties": merge_specialties(
            existing_specialties
        ),
        "journal_club": existing_journal_club,
        "pipeline": {
            "librarian_complete": True,
            "appraisal_complete": bool(
                appraisal
            ),
            "statistics_complete": bool(
                statistics
            ),
            "clinical_translation_complete": bool(
                clinical_translation
            ),
            "specialty_review_complete": (
                all(
                    bool(
                        specialty.get(
                            "reviewed",
                            False,
                        )
                    )
                    for specialty in merge_specialties(
                        existing_specialties
                    ).values()
                    if isinstance(
                        specialty,
                        dict,
                    )
                )
            ),
            "database_updated_at": now,
        },
    }

    return record


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def score_from_record(
    record: dict[str, Any],
) -> tuple[int, int, int]:
    """
    Sort the master database by useful evidence measures.
    """

    appraisal = dictionary_or_empty(
        record.get("appraisal")
    )

    appraisal_scores = dictionary_or_empty(
        appraisal.get("scores")
    )

    statistics = dictionary_or_empty(
        record.get("statistics")
    )

    statistics_scores = dictionary_or_empty(
        statistics.get("scores")
    )

    translation = dictionary_or_empty(
        record.get(
            "clinical_translation"
        )
    )

    translation_priority = (
        translation.get(
            "translation_priority",
            0,
        )
        or 0
    )

    overall_evidence = (
        appraisal_scores.get(
            "overall_evidence",
            0,
        )
        or 0
    )

    statistics_score = (
        statistics_scores.get(
            "overall_statistics",
            0,
        )
        or 0
    )

    return (
        int(translation_priority),
        int(overall_evidence),
        int(statistics_score),
    )


# ---------------------------------------------------------------------------
# Main database builder
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 72)
    print("Optimize Evidence Database Builder")
    print("=" * 72)

    papers = load_json_list(
        PAPERS_PATH,
        required=True,
    )

    appraised = load_json_list(
        APPRAISED_PATH
    )

    statistically_reviewed = (
        load_json_list(
            STATISTICS_PATH
        )
    )

    clinically_translated = (
        load_json_list(
            TRANSLATED_PATH
        )
    )

    existing_database = (
        load_json_list(
            OUTPUT_PATH
        )
        if OUTPUT_PATH.exists()
        else []
    )

    print(
        f"Research Librarian records: {len(papers)}"
    )
    print(
        f"Evidence Appraiser records: {len(appraised)}"
    )
    print(
        "Statistics Reviewer records: "
        f"{len(statistically_reviewed)}"
    )
    print(
        "Clinical Translator records: "
        f"{len(clinically_translated)}"
    )
    print()

    base_index = index_papers(
        papers
    )

    appraisal_index = index_papers(
        appraised
    )

    statistics_index = index_papers(
        statistically_reviewed
    )

    translation_index = index_papers(
        clinically_translated
    )

    existing_index: dict[
        str,
        dict[str, Any],
    ] = {}

    for record in existing_database:
        pmid = clean_text(
            record.get("pmid")
        )

        doi = normalize_doi(
            record.get("doi")
        )

        metadata = dictionary_or_empty(
            record.get("metadata")
        )

        if pmid:
            identity = f"pmid:{pmid}"

        elif doi:
            identity = f"doi:{doi}"

        else:
            title = normalize_title(
                metadata.get("title")
            )

            if not title:
                continue

            identity = f"title:{title}"

        existing_index[
            identity
        ] = record

    canonical_database: list[
        dict[str, Any]
    ] = []

    for identity, base_paper in (
        base_index.items()
    ):
        canonical_record = (
            build_canonical_record(
                base_paper=base_paper,
                appraisal_paper=(
                    appraisal_index.get(
                        identity
                    )
                ),
                statistics_paper=(
                    statistics_index.get(
                        identity
                    )
                ),
                translation_paper=(
                    translation_index.get(
                        identity
                    )
                ),
                existing_record=(
                    existing_index.get(
                        identity
                    )
                ),
            )
        )

        canonical_database.append(
            canonical_record
        )

        title = canonical_record.get(
            "metadata",
            {},
        ).get(
            "title",
            "",
        )

        pipeline = canonical_record[
            "pipeline"
        ]

        status = []

        if pipeline[
            "appraisal_complete"
        ]:
            status.append(
                "appraised"
            )

        if pipeline[
            "statistics_complete"
        ]:
            status.append(
                "statistics"
            )

        if pipeline[
            "clinical_translation_complete"
        ]:
            status.append(
                "translated"
            )

        print(
            f"Built: {clean_text(title)[:70]} "
            f"| {', '.join(status) or 'metadata only'}"
        )

    canonical_database.sort(
        key=score_from_record,
        reverse=True,
    )

    save_json(
        OUTPUT_PATH,
        canonical_database,
    )

    print()
    print("=" * 72)
    print(
        "Canonical papers saved: "
        f"{len(canonical_database)}"
    )
    print(
        f"Database: {OUTPUT_PATH}"
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
            "\nDatabase build cancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nEvidence database builder failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
