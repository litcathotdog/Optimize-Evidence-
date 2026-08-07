"""
Optimize Evidence: Knowledge Graph Builder

Reads:
    data/evidence_database.json

Writes:
    data/knowledge_graph.json

Purpose
-------
Transform the canonical evidence database into a connected evidence graph.

The graph connects:

Paper
  -> Specialty
  -> Clinical area
  -> Intervention
  -> Condition / tissue
  -> Outcome
  -> Study design
  -> Journal

It also creates evidence synthesis summaries so downstream systems can ask
questions such as:

- Which interventions have the most evidence?
- Which specialties contain the strongest studies?
- Where do studies agree or conflict?
- Which topics have weak evidence?
- Which papers deserve full-text review?
- What evidence gaps exist?

No external AI API or Python package is required.
"""

from __future__ import annotations

import json
import re
import sys

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ===========================================================================
# PATHS
# ===========================================================================

DATABASE_PATH = Path("data/evidence_database.json")
GRAPH_PATH = Path("data/knowledge_graph.json")


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


def slugify(value: Any) -> str:
    text = clean_text(value).lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )

    return text.strip("-")


def safe_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        return int(value)
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


def unique_strings(
    values: list[Any],
) -> list[str]:
    cleaned: list[str] = []

    for value in values:
        text = clean_text(value)

        if text and text not in cleaned:
            cleaned.append(text)

    return cleaned


# ===========================================================================
# FILE OPERATIONS
# ===========================================================================

def load_database() -> list[dict[str, Any]]:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Evidence database does not exist: {DATABASE_PATH}"
        )

    with DATABASE_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "evidence_database.json must contain a JSON list."
        )

    return [
        record
        for record in data
        if isinstance(record, dict)
    ]


def save_graph(
    graph: dict[str, Any],
) -> None:
    GRAPH_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = GRAPH_PATH.with_suffix(
        ".json.tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            graph,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write("\n")

    temporary_path.replace(
        GRAPH_PATH
    )


# ===========================================================================
# RECORD ACCESS
# ===========================================================================

def get_metadata(
    record: dict[str, Any],
) -> dict[str, Any]:
    return dictionary_or_empty(
        record.get("metadata")
    )


def get_appraisal(
    record: dict[str, Any],
) -> dict[str, Any]:
    return dictionary_or_empty(
        record.get("appraisal")
    )


def get_statistics(
    record: dict[str, Any],
) -> dict[str, Any]:
    return dictionary_or_empty(
        record.get("statistics")
    )


def get_translation(
    record: dict[str, Any],
) -> dict[str, Any]:
    return dictionary_or_empty(
        record.get("clinical_translation")
    )


def get_specialties(
    record: dict[str, Any],
) -> dict[str, Any]:
    return dictionary_or_empty(
        record.get("specialties")
    )


# ===========================================================================
# PAPER IDENTIFIERS
# ===========================================================================

def paper_identifier(
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
        return (
            "paper:doi:"
            + slugify(doi)
        )

    title = clean_text(
        get_metadata(record).get(
            "title"
        )
    )

    return (
        "paper:title:"
        + slugify(title)
    )


# ===========================================================================
# RESULT DIRECTION
# ===========================================================================

def classify_result_direction(
    record: dict[str, Any],
) -> str:
    """
    Convert the Clinical Translator / Evidence Appraiser result language
    into a standardized evidence direction.
    """

    translation = get_translation(
        record
    )

    appraisal = get_appraisal(
        record
    )

    result = clean_text(
        translation.get(
            "result_direction"
        )
        or appraisal.get(
            "result_direction"
        )
    ).lower()

    positive_terms = (
        "favorable",
        "favourable",
        "significantly improved",
        "significant improvement",
        "superior",
        "greater improvement",
        "significantly reduced",
        "was effective",
        "were effective",
    )

    neutral_terms = (
        "no clear between-group advantage",
        "no significant difference",
        "not significantly different",
        "no evidence of a difference",
    )

    negative_terms = (
        "unfavorable",
        "unfavourable",
        "worse outcomes",
        "increased risk",
        "adverse effect",
        "significantly worse",
    )

    if any(
        term in result
        for term in neutral_terms
    ):
        return "neutral"

    if any(
        term in result
        for term in negative_terms
    ):
        return "unfavorable"

    if any(
        term in result
        for term in positive_terms
    ):
        return "favorable"

    return "unclear"


# ===========================================================================
# NODE / EDGE MANAGER
# ===========================================================================

class KnowledgeGraph:
    def __init__(self) -> None:

        self.nodes: dict[
            str,
            dict[str, Any],
        ] = {}

        self.edges: dict[
            tuple[str, str, str],
            dict[str, Any],
        ] = {}


    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        **attributes: Any,
    ) -> None:

        if not node_id or not label:
            return

        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
                **attributes,
            }

            return

        existing = self.nodes[
            node_id
        ]

        for key, value in (
            attributes.items()
        ):
            if (
                value is not None
                and value != ""
                and value != []
            ):
                existing[
                    key
                ] = value


    def add_edge(
        self,
        source: str,
        relationship: str,
        target: str,
        **attributes: Any,
    ) -> None:

        if (
            not source
            or not target
            or source == target
        ):
            return

        key = (
            source,
            relationship,
            target,
        )

        if key not in self.edges:
            self.edges[key] = {
                "source": source,
                "relationship": relationship,
                "target": target,
                **attributes,
            }

            return

        existing = self.edges[
            key
        ]

        existing[
            "weight"
        ] = safe_int(
            existing.get(
                "weight",
                1,
            )
        ) + 1


    def export_nodes(
        self,
    ) -> list[dict[str, Any]]:

        return sorted(
            self.nodes.values(),
            key=lambda node: (
                node.get(
                    "type",
                    "",
                ),
                node.get(
                    "label",
                    "",
                ),
            ),
        )


    def export_edges(
        self,
    ) -> list[dict[str, Any]]:

        return sorted(
            self.edges.values(),
            key=lambda edge: (
                edge.get(
                    "source",
                    "",
                ),
                edge.get(
                    "relationship",
                    "",
                ),
                edge.get(
                    "target",
                    "",
                ),
            ),
        )


# ===========================================================================
# STANDARD NODE HELPERS
# ===========================================================================

def concept_node_id(
    concept_type: str,
    value: str,
) -> str:

    return (
        f"{concept_type}:"
        f"{slugify(value)}"
    )


def connect_values(
    graph: KnowledgeGraph,
    paper_id: str,
    node_type: str,
    relationship: str,
    values: list[Any],
) -> None:

    for value in unique_strings(
        values
    ):
        node_id = concept_node_id(
            node_type,
            value,
        )

        graph.add_node(
            node_id=node_id,
            node_type=node_type,
            label=value,
        )

        graph.add_edge(
            source=paper_id,
            relationship=relationship,
            target=node_id,
        )


# ===========================================================================
# SPECIALTY EXTRACTION
# ===========================================================================

def add_specialty_connections(
    graph: KnowledgeGraph,
    paper_id: str,
    record: dict[str, Any],
) -> None:

    specialties = get_specialties(
        record
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

        specialty_label = (
            specialty_name
            .replace("_", " ")
            .title()
        )

        specialty_id = (
            concept_node_id(
                "specialty",
                specialty_name,
            )
        )

        graph.add_node(
            node_id=specialty_id,
            node_type="specialty",
            label=specialty_label,
        )

        graph.add_edge(
            source=paper_id,
            relationship="belongs_to_specialty",
            target=specialty_id,
        )

        # ---------------------------------------------------------------
        # Regenerative medicine
        # ---------------------------------------------------------------

        if (
            specialty_name
            == "regenerative_medicine"
        ):
            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="intervention",
                relationship="studies_intervention",
                values=list_or_empty(
                    specialty_data.get(
                        "therapy_class"
                    )
                ),
            )

            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="tissue",
                relationship="targets_tissue",
                values=list_or_empty(
                    specialty_data.get(
                        "target_tissue"
                    )
                ),
            )

        # ---------------------------------------------------------------
        # Sports performance
        # ---------------------------------------------------------------

        elif (
            specialty_name
            == "sports_performance"
        ):
            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="performance_outcome",
                relationship="measures_performance",
                values=list_or_empty(
                    specialty_data.get(
                        "performance_outcomes"
                    )
                ),
            )

            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="training_intervention",
                relationship="studies_training",
                values=list_or_empty(
                    specialty_data.get(
                        "training_interventions"
                    )
                ),
            )

        # ---------------------------------------------------------------
        # Biomechanics
        # ---------------------------------------------------------------

        elif (
            specialty_name
            == "biomechanics"
        ):
            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="biomechanical_variable",
                relationship="measures_biomechanics",
                values=list_or_empty(
                    specialty_data.get(
                        "biomechanical_variables"
                    )
                ),
            )

            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="measurement_system",
                relationship="uses_measurement_system",
                values=list_or_empty(
                    specialty_data.get(
                        "measurement_systems"
                    )
                ),
            )

        # ---------------------------------------------------------------
        # Women's athlete health
        # ---------------------------------------------------------------

        elif (
            specialty_name
            == "womens_athlete_health"
        ):
            connect_values(
                graph=graph,
                paper_id=paper_id,
                node_type="health_domain",
                relationship="studies_health_domain",
                values=list_or_empty(
                    specialty_data.get(
                        "health_domains"
                    )
                ),
            )


# ===========================================================================
# BUILD PAPER CONNECTIONS
# ===========================================================================

def add_paper_to_graph(
    graph: KnowledgeGraph,
    record: dict[str, Any],
) -> None:

    metadata = get_metadata(
        record
    )

    appraisal = get_appraisal(
        record
    )

    statistics = get_statistics(
        record
    )

    translation = get_translation(
        record
    )

    paper_id = paper_identifier(
        record
    )

    title = clean_text(
        metadata.get(
            "title"
        )
    )

    if not title:
        return

    appraisal_scores = (
        dictionary_or_empty(
            appraisal.get(
                "scores"
            )
        )
    )

    statistics_scores = (
        dictionary_or_empty(
            statistics.get(
                "scores"
            )
        )
    )

    result_direction = (
        classify_result_direction(
            record
        )
    )

    graph.add_node(
        node_id=paper_id,
        node_type="paper",
        label=title,
        pmid=clean_text(
            record.get(
                "pmid"
            )
        ),
        doi=clean_text(
            record.get(
                "doi"
            )
        ),
        journal=clean_text(
            metadata.get(
                "journal"
            )
        ),
        publication_date=clean_text(
            metadata.get(
                "publication_date"
            )
        ),
        evidence_score=safe_int(
            appraisal_scores.get(
                "overall_evidence"
            )
        ),
        statistics_score=safe_int(
            statistics_scores.get(
                "overall_statistics"
            )
        ),
        practitioner_relevance=safe_int(
            appraisal_scores.get(
                "practitioner_relevance"
            )
        ),
        translation_priority=safe_int(
            translation.get(
                "translation_priority"
            )
        ),
        practice_readiness=clean_text(
            translation.get(
                "practice_readiness"
            )
        ),
        evidence_strength=clean_text(
            appraisal.get(
                "evidence_strength"
            )
        ),
        statistical_confidence=clean_text(
            statistics.get(
                "statistical_confidence"
            )
        ),
        result_direction=result_direction,
        requires_full_text_review=bool(
            translation.get(
                "requires_full_text_review",
                False,
            )
        ),
    )

    # -------------------------------------------------------------------
    # Clinical area
    # -------------------------------------------------------------------

    clinical_area = clean_text(
        translation.get(
            "clinical_area"
        )
    )

    if clinical_area:
        node_id = concept_node_id(
            "clinical_area",
            clinical_area,
        )

        graph.add_node(
            node_id=node_id,
            node_type="clinical_area",
            label=clinical_area,
        )

        graph.add_edge(
            source=paper_id,
            relationship="addresses_clinical_area",
            target=node_id,
        )

    # -------------------------------------------------------------------
    # Study design
    # -------------------------------------------------------------------

    study_design = clean_text(
        appraisal.get(
            "study_design"
        )
        or metadata.get(
            "study_type"
        )
    )

    if study_design:
        design_id = concept_node_id(
            "study_design",
            study_design,
        )

        graph.add_node(
            node_id=design_id,
            node_type="study_design",
            label=study_design,
        )

        graph.add_edge(
            source=paper_id,
            relationship="has_study_design",
            target=design_id,
        )

    # -------------------------------------------------------------------
    # Journal
    # -------------------------------------------------------------------

    journal = clean_text(
        metadata.get(
            "journal"
        )
    )

    if journal:
        journal_id = concept_node_id(
            "journal",
            journal,
        )

        graph.add_node(
            node_id=journal_id,
            node_type="journal",
            label=journal,
        )

        graph.add_edge(
            source=paper_id,
            relationship="published_in",
            target=journal_id,
        )

    # -------------------------------------------------------------------
    # Outcomes
    # -------------------------------------------------------------------

    outcomes = list_or_empty(
        translation.get(
            "clinically_relevant_outcomes"
        )
    )

    if not outcomes:
        outcomes = list_or_empty(
            appraisal.get(
                "identified_outcomes"
            )
        )

    connect_values(
        graph=graph,
        paper_id=paper_id,
        node_type="outcome",
        relationship="measures_outcome",
        values=outcomes,
    )

    # -------------------------------------------------------------------
    # Intervention / exposure
    # -------------------------------------------------------------------

    intervention = clean_text(
        translation.get(
            "intervention_or_exposure"
        )
    )

    if (
        intervention
        and "not clearly" not in intervention.lower()
        and "not reliably" not in intervention.lower()
    ):
        intervention_id = (
            concept_node_id(
                "intervention",
                intervention,
            )
        )

        graph.add_node(
            node_id=intervention_id,
            node_type="intervention",
            label=intervention,
        )

        graph.add_edge(
            source=paper_id,
            relationship="studies_intervention",
            target=intervention_id,
        )

    # -------------------------------------------------------------------
    # Specialty-specific concepts
    # -------------------------------------------------------------------

    add_specialty_connections(
        graph=graph,
        paper_id=paper_id,
        record=record,
    )


# ===========================================================================
# GRAPH STATISTICS
# ===========================================================================

def calculate_graph_statistics(
    graph: KnowledgeGraph,
) -> dict[str, Any]:

    node_types = Counter(
        node.get(
            "type",
            "unknown",
        )
        for node
        in graph.nodes.values()
    )

    relationship_types = Counter(
        edge.get(
            "relationship",
            "unknown",
        )
        for edge
        in graph.edges.values()
    )

    return {
        "total_nodes": len(
            graph.nodes
        ),
        "total_edges": len(
            graph.edges
        ),
        "nodes_by_type": dict(
            sorted(
                node_types.items()
            )
        ),
        "edges_by_relationship": dict(
            sorted(
                relationship_types.items()
            )
        ),
    }


# ===========================================================================
# CONCEPT EVIDENCE SYNTHESIS
# ===========================================================================

def build_concept_synthesis(
    graph: KnowledgeGraph,
) -> list[dict[str, Any]]:
    """
    Aggregate paper-level evidence around connected concept nodes.

    This is not a meta-analysis. It is a structured evidence inventory.
    """

    papers_by_concept: dict[
        str,
        list[str],
    ] = defaultdict(list)

    relevant_relationships = {
        "addresses_clinical_area",
        "studies_intervention",
        "targets_tissue",
        "measures_outcome",
        "measures_performance",
        "studies_training",
        "measures_biomechanics",
        "studies_health_domain",
        "belongs_to_specialty",
    }

    for edge in graph.edges.values():

        if edge.get(
            "relationship"
        ) not in relevant_relationships:
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

        source_node = graph.nodes.get(
            source,
            {},
        )

        if (
            source_node.get(
                "type"
            )
            != "paper"
        ):
            continue

        papers_by_concept[
            target
        ].append(
            source
        )

    syntheses: list[
        dict[str, Any]
    ] = []

    for (
        concept_id,
        paper_ids,
    ) in papers_by_concept.items():

        concept = graph.nodes.get(
            concept_id,
            {},
        )

        unique_papers = sorted(
            set(paper_ids)
        )

        directions = Counter()

        evidence_scores: list[int] = []
        statistics_scores: list[int] = []
        relevance_scores: list[int] = []

        practice_informing = 0
        full_text_needed = 0

        strong_or_moderate = 0

        study_designs = Counter()

        for paper_id in unique_papers:

            paper = graph.nodes.get(
                paper_id,
                {},
            )

            direction = clean_text(
                paper.get(
                    "result_direction"
                )
            )

            if direction:
                directions[
                    direction
                ] += 1

            evidence_score = safe_int(
                paper.get(
                    "evidence_score"
                )
            )

            statistics_score = safe_int(
                paper.get(
                    "statistics_score"
                )
            )

            relevance_score = safe_int(
                paper.get(
                    "practitioner_relevance"
                )
            )

            if evidence_score:
                evidence_scores.append(
                    evidence_score
                )

            if statistics_score:
                statistics_scores.append(
                    statistics_score
                )

            if relevance_score:
                relevance_scores.append(
                    relevance_score
                )

            if (
                clean_text(
                    paper.get(
                        "practice_readiness"
                    )
                )
                == "Practice-informing"
            ):
                practice_informing += 1

            if paper.get(
                "requires_full_text_review",
                False,
            ):
                full_text_needed += 1

            if (
                clean_text(
                    paper.get(
                        "evidence_strength"
                    )
                ).lower()
                in {
                    "strong",
                    "moderate",
                }
            ):
                strong_or_moderate += 1

            # Find connected study design.
            for edge in (
                graph.edges.values()
            ):
                if (
                    edge.get(
                        "source"
                    )
                    == paper_id
                    and edge.get(
                        "relationship"
                    )
                    == "has_study_design"
                ):
                    design_node = (
                        graph.nodes.get(
                            edge.get(
                                "target"
                            ),
                            {},
                        )
                    )

                    design = clean_text(
                        design_node.get(
                            "label"
                        )
                    )

                    if design:
                        study_designs[
                            design
                        ] += 1

        def average(
            values: list[int],
        ) -> float | None:

            if not values:
                return None

            return round(
                sum(values)
                / len(values),
                2,
            )

        syntheses.append(
            {
                "concept_id": concept_id,
                "concept_type": clean_text(
                    concept.get(
                        "type"
                    )
                ),
                "concept": clean_text(
                    concept.get(
                        "label"
                    )
                ),
                "paper_count": len(
                    unique_papers
                ),
                "papers": unique_papers,
                "result_direction": {
                    "favorable": directions.get(
                        "favorable",
                        0,
                    ),
                    "neutral": directions.get(
                        "neutral",
                        0,
                    ),
                    "unfavorable": directions.get(
                        "unfavorable",
                        0,
                    ),
                    "unclear": directions.get(
                        "unclear",
                        0,
                    ),
                },
                "average_evidence_score": (
                    average(
                        evidence_scores
                    )
                ),
                "average_statistics_score": (
                    average(
                        statistics_scores
                    )
                ),
                "average_practitioner_relevance": (
                    average(
                        relevance_scores
                    )
                ),
                "strong_or_moderate_evidence_papers": (
                    strong_or_moderate
                ),
                "practice_informing_papers": (
                    practice_informing
                ),
                "papers_needing_full_text_review": (
                    full_text_needed
                ),
                "study_designs": dict(
                    study_designs.most_common()
                ),
            }
        )

    syntheses.sort(
        key=lambda synthesis: (
            synthesis.get(
                "paper_count",
                0,
            ),
            synthesis.get(
                "average_evidence_score"
            )
            or 0,
        ),
        reverse=True,
    )

    return syntheses


# ===========================================================================
# EVIDENCE GAP DETECTION
# ===========================================================================

def detect_evidence_gaps(
    syntheses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Detect simple evidence gaps using transparent rules.

    These are flags for review, not definitive scientific conclusions.
    """

    gaps: list[
        dict[str, Any]
    ] = []

    for synthesis in syntheses:

        paper_count = safe_int(
            synthesis.get(
                "paper_count"
            )
        )

        evidence_score = (
            synthesis.get(
                "average_evidence_score"
            )
        )

        practice_informing = safe_int(
            synthesis.get(
                "practice_informing_papers"
            )
        )

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

        known_directions = (
            favorable
            + neutral
            + unfavorable
        )

        reasons: list[str] = []

        if paper_count <= 2:
            reasons.append(
                "Very few papers are currently represented."
            )

        if (
            evidence_score is not None
            and evidence_score < 5
        ):
            reasons.append(
                "Average evidence quality is low."
            )

        if (
            paper_count >= 3
            and practice_informing == 0
        ):
            reasons.append(
                "No paper is currently classified as practice-informing."
            )

        if (
            known_directions >= 3
            and favorable > 0
            and (
                neutral > 0
                or unfavorable > 0
            )
        ):
            reasons.append(
                "The available papers contain potentially conflicting result directions."
            )

        if reasons:
            gaps.append(
                {
                    "concept_id": synthesis.get(
                        "concept_id"
                    ),
                    "concept_type": synthesis.get(
                        "concept_type"
                    ),
                    "concept": synthesis.get(
                        "concept"
                    ),
                    "paper_count": paper_count,
                    "reasons": reasons,
                }
            )

    return gaps


# ===========================================================================
# TOP PAPERS
# ===========================================================================

def rank_papers(
    graph: KnowledgeGraph,
) -> list[dict[str, Any]]:
    papers: list[
        dict[str, Any]
    ] = []

    for node in graph.nodes.values():

        if node.get(
            "type"
        ) != "paper":
            continue

        evidence = safe_int(
            node.get(
                "evidence_score"
            )
        )

        statistics = safe_int(
            node.get(
                "statistics_score"
            )
        )

        relevance = safe_int(
            node.get(
                "practitioner_relevance"
            )
        )

        priority = safe_int(
            node.get(
                "translation_priority"
            )
        )

        composite = round(
            evidence * 0.35
            + statistics * 0.25
            + relevance * 0.20
            + priority * 0.20,
            2,
        )

        papers.append(
            {
                "paper_id": node.get(
                    "id"
                ),
                "title": node.get(
                    "label"
                ),
                "evidence_score": evidence,
                "statistics_score": statistics,
                "practitioner_relevance": relevance,
                "translation_priority": priority,
                "composite_priority": composite,
                "result_direction": node.get(
                    "result_direction"
                ),
                "practice_readiness": node.get(
                    "practice_readiness"
                ),
                "requires_full_text_review": node.get(
                    "requires_full_text_review"
                ),
            }
        )

    papers.sort(
        key=lambda paper: (
            paper.get(
                "composite_priority",
                0,
            ),
            paper.get(
                "evidence_score",
                0,
            ),
        ),
        reverse=True,
    )

    return papers


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> int:

    print("=" * 72)
    print(
        "Optimize Evidence Knowledge Graph Builder"
    )
    print("=" * 72)

    records = load_database()

    print(
        f"Evidence records loaded: {len(records)}"
    )
    print()

    graph = KnowledgeGraph()

    for record in records:
        add_paper_to_graph(
            graph=graph,
            record=record,
        )

    graph_statistics = (
        calculate_graph_statistics(
            graph
        )
    )

    syntheses = (
        build_concept_synthesis(
            graph
        )
    )

    evidence_gaps = (
        detect_evidence_gaps(
            syntheses
        )
    )

    ranked_papers = (
        rank_papers(
            graph
        )
    )

    output = {
        "metadata": {
            "graph_version": "1.0",
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "source": str(
                DATABASE_PATH
            ),
            "description": (
                "Derived knowledge graph connecting research papers "
                "to clinical areas, interventions, outcomes, specialties, "
                "study designs, tissues, performance measures, biomechanics, "
                "and women's athlete health domains."
            ),
        },

        "statistics": (
            graph_statistics
        ),

        "nodes": (
            graph.export_nodes()
        ),

        "edges": (
            graph.export_edges()
        ),

        "evidence_synthesis": (
            syntheses
        ),

        "evidence_gaps": (
            evidence_gaps
        ),

        "ranked_papers": (
            ranked_papers
        ),
    }

    save_graph(
        output
    )

    print(
        f"Nodes created: "
        f"{graph_statistics['total_nodes']}"
    )

    print(
        f"Edges created: "
        f"{graph_statistics['total_edges']}"
    )

    print(
        f"Evidence concepts synthesized: "
        f"{len(syntheses)}"
    )

    print(
        f"Potential evidence gaps flagged: "
        f"{len(evidence_gaps)}"
    )

    print()

    print(
        f"Knowledge graph saved to: {GRAPH_PATH}"
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
            "\nKnowledge graph build cancelled.",
            file=sys.stderr,
        )

        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nKnowledge graph builder failed: {error}",
            file=sys.stderr,
        )

        raise SystemExit(1)
