"""
Optimize Evidence: Formula-Based Clinical Translator

Reads:
    data/statistically_reviewed_papers.json

Writes:
    data/clinically_translated_papers.json

Purpose
-------
Convert evidence appraisal and statistical review into a conservative,
practitioner-facing interpretation.

This script does not use an AI API.
It relies on transparent, formula-based rules and templates.
"""

from __future__ import annotations

import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INPUT_PATH = Path("data/statistically_reviewed_papers.json")
OUTPUT_PATH = Path("data/clinically_translated_papers.json")


# ---------------------------------------------------------------------------
# Clinical topic rules
# ---------------------------------------------------------------------------

CLINICAL_AREA_RULES: dict[str, tuple[str, ...]] = {
    "Orthobiologics and regenerative medicine": (
        "platelet-rich plasma",
        "platelet rich plasma",
        "prp",
        "bone marrow aspirate concentrate",
        "bmac",
        "mesenchymal stem cell",
        "mesenchymal stromal cell",
        "exosome",
        "extracellular vesicle",
        "orthobiologic",
        "regenerative medicine",
    ),
    "Tendon rehabilitation": (
        "tendinopathy",
        "patellar tendon",
        "achilles tendon",
        "tendon rehabilitation",
        "tendon loading",
    ),
    "Ligament and return-to-sport rehabilitation": (
        "anterior cruciate ligament",
        "acl",
        "ligament rehabilitation",
        "return to sport",
        "return to play",
    ),
    "Cartilage and joint health": (
        "cartilage",
        "osteoarthritis",
        "patellofemoral",
        "joint health",
    ),
    "Muscle injury and recovery": (
        "muscle injury",
        "muscle strain",
        "hamstring injury",
        "muscle damage",
        "doms",
    ),
    "Sports performance": (
        "athletic performance",
        "sports performance",
        "sprint performance",
        "speed endurance",
        "strength performance",
        "power output",
        "training adaptation",
    ),
    "Women's athlete health": (
        "female athlete",
        "women athletes",
        "relative energy deficiency in sport",
        "red-s",
        "low energy availability",
        "menstrual",
        "bone mineral density",
    ),
    "Recovery physiology": (
        "sleep",
        "cortisol",
        "heart rate variability",
        "recovery",
        "circadian",
        "stress physiology",
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def normalized_text(*values: Any) -> str:
    return clean_text(
        " ".join(clean_text(value) for value in values)
    ).lower()


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def paper_identity(paper: dict[str, Any]) -> str:
    pmid = clean_text(paper.get("pmid"))

    if pmid:
        return f"pmid:{pmid}"

    doi = clean_text(paper.get("doi")).lower()

    if doi:
        return f"doi:{doi}"

    title = clean_text(paper.get("title")).lower()
    normalized_title = re.sub(r"[^a-z0-9]+", "", title)

    return f"title:{normalized_title}"


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
        item for item in data
        if isinstance(item, dict)
    ]


def save_json(
    path: Path,
    data: list[dict[str, Any]],
) -> None:
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


# ---------------------------------------------------------------------------
# Extract prior pipeline results
# ---------------------------------------------------------------------------

def get_appraisal(
    paper: dict[str, Any],
) -> dict[str, Any]:
    appraisal = paper.get(
        "formulaic_appraisal",
        {},
    )

    if isinstance(appraisal, dict):
        return appraisal

    return {}


def get_statistics_review(
    paper: dict[str, Any],
) -> dict[str, Any]:
    review = paper.get(
        "statistics_review",
        {},
    )

    if isinstance(review, dict):
        return review

    return {}


# ---------------------------------------------------------------------------
# Clinical-area classification
# ---------------------------------------------------------------------------

def identify_clinical_area(
    paper: dict[str, Any],
) -> str:
    text = normalized_text(
        paper.get("title"),
        paper.get("abstract"),
        paper.get("topic"),
    )

    best_area = ""
    best_score = 0

    for area, terms in CLINICAL_AREA_RULES.items():
        score = sum(
            1
            for term in terms
            if term in text
        )

        if score > best_score:
            best_score = score
            best_area = area

    if best_area:
        return best_area

    topic = clean_text(
        paper.get("topic")
    )

    if topic:
        return topic

    return "Sports and performance medicine"


# ---------------------------------------------------------------------------
# Population, intervention, outcomes
# ---------------------------------------------------------------------------

def get_population(
    paper: dict[str, Any],
) -> str:
    appraisal = get_appraisal(paper)

    population = clean_text(
        appraisal.get("population")
    )

    if (
        population
        and "not reliably extractable"
        not in population.lower()
    ):
        return population

    return (
        "Population not clearly extractable from the abstract."
    )


def get_intervention(
    paper: dict[str, Any],
) -> str:
    appraisal = get_appraisal(paper)

    intervention = clean_text(
        appraisal.get(
            "intervention_or_exposure"
        )
    )

    if (
        intervention
        and "not reliably extractable"
        not in intervention.lower()
    ):
        return intervention

    return (
        "Intervention or exposure not clearly extractable from the abstract."
    )


def get_outcomes(
    paper: dict[str, Any],
) -> list[str]:
    appraisal = get_appraisal(paper)

    outcomes = appraisal.get(
        "identified_outcomes",
        [],
    )

    if not isinstance(outcomes, list):
        return []

    cleaned = []

    for outcome in outcomes:
        value = clean_text(outcome)

        if value and value not in cleaned:
            cleaned.append(value)

    return cleaned[:8]


# ---------------------------------------------------------------------------
# Evidence interpretation
# ---------------------------------------------------------------------------

def get_evidence_strength(
    paper: dict[str, Any],
) -> str:
    appraisal = get_appraisal(paper)

    return clean_text(
        appraisal.get(
            "evidence_strength"
        )
    ) or "Unclear"


def get_risk_of_bias(
    paper: dict[str, Any],
) -> str:
    appraisal = get_appraisal(paper)

    return clean_text(
        appraisal.get(
            "risk_of_bias"
        )
    ) or "Unclear"


def get_statistical_confidence(
    paper: dict[str, Any],
) -> str:
    review = get_statistics_review(paper)

    return clean_text(
        review.get(
            "statistical_confidence"
        )
    ) or "Unclear"


def get_result_direction(
    paper: dict[str, Any],
) -> str:
    appraisal = get_appraisal(paper)

    result = clean_text(
        appraisal.get(
            "result_direction"
        )
    )

    if result:
        return result

    return (
        "The direction and clinical magnitude of the findings are not "
        "reliably extractable from the abstract."
    )


def get_scores(
    paper: dict[str, Any],
) -> dict[str, int]:
    appraisal = get_appraisal(paper)
    statistics = get_statistics_review(paper)

    appraisal_scores = appraisal.get(
        "scores",
        {},
    )

    statistics_scores = statistics.get(
        "scores",
        {},
    )

    if not isinstance(appraisal_scores, dict):
        appraisal_scores = {}

    if not isinstance(statistics_scores, dict):
        statistics_scores = {}

    return {
        "overall_evidence": int(
            appraisal_scores.get(
                "overall_evidence",
                0,
            )
            or 0
        ),
        "practitioner_relevance": int(
            appraisal_scores.get(
                "practitioner_relevance",
                0,
            )
            or 0
        ),
        "overall_statistics": int(
            statistics_scores.get(
                "overall_statistics",
                0,
            )
            or 0
        ),
    }


# ---------------------------------------------------------------------------
# Practice readiness
# ---------------------------------------------------------------------------

def assign_practice_readiness(
    evidence_strength: str,
    statistical_confidence: str,
    risk_of_bias: str,
    scores: dict[str, int],
) -> str:
    evidence = evidence_strength.lower()
    stats = statistical_confidence.lower()
    bias = risk_of_bias.lower()

    if (
        evidence in {"strong", "moderate"}
        and stats in {"high", "moderate"}
        and "high" not in bias
        and scores["overall_evidence"] >= 7
        and scores["overall_statistics"] >= 7
        and scores["practitioner_relevance"] >= 7
    ):
        return "Practice-informing"

    if (
        scores["overall_evidence"] >= 5
        and scores["overall_statistics"] >= 5
        and scores["practitioner_relevance"] >= 5
    ):
        return "Promising but preliminary"

    return "Research-generating"


def assign_action_level(
    practice_readiness: str,
    study_design: str,
) -> str:
    design = study_design.lower()

    if (
        "preclinical" in design
        or "laboratory" in design
    ):
        return (
            "Do not apply directly to clinical care."
        )

    if practice_readiness == "Practice-informing":
        return (
            "May inform shared clinical decision-making when consistent "
            "with guidelines, patient goals, risks, and feasibility."
        )

    if practice_readiness == "Promising but preliminary":
        return (
            "May support clinical reasoning, but should not independently "
            "drive a major treatment change."
        )

    return (
        "Use primarily to generate questions or identify research priorities."
    )


# ---------------------------------------------------------------------------
# Cautions
# ---------------------------------------------------------------------------

def collect_cautions(
    paper: dict[str, Any],
) -> list[str]:
    appraisal = get_appraisal(paper)
    statistics = get_statistics_review(paper)

    limitations = appraisal.get(
        "limitations",
        [],
    )

    flags = statistics.get(
        "reporting_flags",
        [],
    )

    if not isinstance(limitations, list):
        limitations = []

    if not isinstance(flags, list):
        flags = []

    cautions: list[str] = []

    for item in limitations + flags:
        text = clean_text(item)

        if text and text not in cautions:
            cautions.append(text)

    return cautions[:8]


# ---------------------------------------------------------------------------
# Clinical summaries
# ---------------------------------------------------------------------------

def generate_clinical_summary(
    clinical_area: str,
    study_design: str,
    population: str,
    intervention: str,
    result_direction: str,
) -> str:
    return (
        f"This {study_design.lower()} addresses {clinical_area}. "
        f"The reported population was: {population} "
        f"The intervention or exposure was: {intervention} "
        f"{result_direction}"
    )


def generate_practitioner_takeaway(
    practice_readiness: str,
    clinical_area: str,
    result_direction: str,
) -> str:
    if practice_readiness == "Practice-informing":
        return (
            f"This study may meaningfully inform practice in {clinical_area}. "
            f"{result_direction} Full-text review should still confirm the "
            "methods, intervention details, comparator, effect magnitude, "
            "adverse events, and applicability to the patient population."
        )

    if practice_readiness == "Promising but preliminary":
        return (
            f"This paper provides potentially useful evidence in "
            f"{clinical_area}, but the findings should be treated as "
            f"preliminary. {result_direction} It should support rather than "
            "replace established clinical reasoning and guidelines."
        )

    return (
        f"This paper currently provides limited practice-changing evidence "
        f"in {clinical_area}. {result_direction} It is more useful for "
        "hypothesis generation or identifying future research needs."
    )


def generate_research_takeaway(
    paper: dict[str, Any],
) -> str:
    statistics = get_statistics_review(paper)

    flags = statistics.get(
        "reporting_flags",
        [],
    )

    if not isinstance(flags, list):
        flags = []

    if flags:
        return (
            "Future studies should address the identified reporting and "
            "methodological limitations, particularly around effect estimates, "
            "precision, confounding, and clinical importance where applicable."
        )

    return (
        "The abstract does not reveal major statistical reporting concerns, "
        "but full-text methodological review is still needed before drawing "
        "firm conclusions."
    )


# ---------------------------------------------------------------------------
# Translation priority
# ---------------------------------------------------------------------------

def calculate_translation_priority(
    scores: dict[str, int],
    practice_readiness: str,
    requires_full_text: bool,
) -> int:
    score = (
        scores["overall_evidence"] * 0.40
        + scores["practitioner_relevance"] * 0.35
        + scores["overall_statistics"] * 0.25
    )

    if practice_readiness == "Practice-informing":
        score += 1

    if requires_full_text:
        score -= 0.5

    return clamp(
        round(score),
        1,
        10,
    )


# ---------------------------------------------------------------------------
# Translate one paper
# ---------------------------------------------------------------------------

def translate_paper(
    paper: dict[str, Any],
) -> dict[str, Any]:
    appraisal = get_appraisal(paper)
    statistics = get_statistics_review(paper)

    study_design = clean_text(
        appraisal.get(
            "study_design"
        )
    )

    if not study_design:
        study_design = clean_text(
            paper.get(
                "study_type"
            )
        ) or "research article"

    clinical_area = identify_clinical_area(
        paper
    )

    population = get_population(
        paper
    )

    intervention = get_intervention(
        paper
    )

    outcomes = get_outcomes(
        paper
    )

    evidence_strength = get_evidence_strength(
        paper
    )

    risk_of_bias = get_risk_of_bias(
        paper
    )

    statistical_confidence = (
        get_statistical_confidence(
            paper
        )
    )

    result_direction = get_result_direction(
        paper
    )

    scores = get_scores(
        paper
    )

    practice_readiness = assign_practice_readiness(
        evidence_strength=evidence_strength,
        statistical_confidence=statistical_confidence,
        risk_of_bias=risk_of_bias,
        scores=scores,
    )

    requires_full_text = bool(
        appraisal.get(
            "needs_full_text_review",
            False,
        )
        or statistics.get(
            "requires_full_text_statistical_review",
            False,
        )
    )

    priority = calculate_translation_priority(
        scores=scores,
        practice_readiness=practice_readiness,
        requires_full_text=requires_full_text,
    )

    translation = {
        "clinical_area": clinical_area,
        "study_design": study_design,
        "population": population,
        "intervention_or_exposure": intervention,
        "clinically_relevant_outcomes": outcomes,
        "result_direction": result_direction,
        "evidence_strength": evidence_strength,
        "statistical_confidence": statistical_confidence,
        "risk_of_bias": risk_of_bias,
        "practice_readiness": practice_readiness,
        "action_level": assign_action_level(
            practice_readiness=practice_readiness,
            study_design=study_design,
        ),
        "clinical_summary": generate_clinical_summary(
            clinical_area=clinical_area,
            study_design=study_design,
            population=population,
            intervention=intervention,
            result_direction=result_direction,
        ),
        "practitioner_takeaway": generate_practitioner_takeaway(
            practice_readiness=practice_readiness,
            clinical_area=clinical_area,
            result_direction=result_direction,
        ),
        "research_takeaway": generate_research_takeaway(
            paper
        ),
        "major_cautions": collect_cautions(
            paper
        ),
        "translation_priority": priority,
        "requires_full_text_review": requires_full_text,
        "translation_method": (
            "Conservative rule-based clinical translation from abstract-level "
            "metadata, evidence appraisal, and statistical review. This is not "
            "a substitute for full-text review or individualized medical guidance."
        ),
        "translated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    title = clean_text(
        paper.get(
            "title"
        )
    )

    print(
        f"Translated: {title[:70]} | "
        f"{practice_readiness} | "
        f"priority={priority}/10"
    )

    return {
        **paper,
        "clinical_translation": translation,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    papers = load_json_list(
        INPUT_PATH
    )

    existing_translations: list[
        dict[str, Any]
    ] = []

    if OUTPUT_PATH.exists():
        existing_translations = (
            load_json_list(
                OUTPUT_PATH
            )
        )

    existing_by_id = {
        paper_identity(paper): paper
        for paper in existing_translations
    }

    translated_papers: list[
        dict[str, Any]
    ] = []

    new_translations = 0
    reused_translations = 0

    for paper in papers:
        identity = paper_identity(
            paper
        )

        existing = existing_by_id.get(
            identity
        )

        current_statistics = (
            get_statistics_review(
                paper
            )
        )

        existing_statistics = (
            get_statistics_review(
                existing
            )
            if existing
            else {}
        )

        if (
            existing
            and existing.get(
                "clinical_translation"
            )
            and clean_text(
                existing.get("abstract")
            )
            == clean_text(
                paper.get("abstract")
            )
            and clean_text(
                existing_statistics.get(
                    "reviewed_at"
                )
            )
            == clean_text(
                current_statistics.get(
                    "reviewed_at"
                )
            )
        ):
            translated_papers.append(
                existing
            )
            reused_translations += 1
            continue

        translated_papers.append(
            translate_paper(
                paper
            )
        )

        new_translations += 1

    translated_papers.sort(
        key=lambda paper: (
            paper.get(
                "clinical_translation",
                {},
            ).get(
                "translation_priority",
                0,
            )
        ),
        reverse=True,
    )

    save_json(
        OUTPUT_PATH,
        translated_papers,
    )

    print()
    print("=" * 72)
    print(
        f"Papers received: {len(papers)}"
    )
    print(
        f"New clinical translations: {new_translations}"
    )
    print(
        f"Existing translations reused: {reused_translations}"
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
            "\nClinical translation cancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nClinical translator failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
