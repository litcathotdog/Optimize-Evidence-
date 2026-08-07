"""
Optimize Evidence: Formula-Based Specialty Router

Reads:
    data/evidence_database.json

Writes:
    data/evidence_database.json

Purpose
-------
Assign each paper to one or more specialty domains without duplicating
the paper.

Current specialties:
- Regenerative Medicine
- Sports Performance
- Biomechanics
- Women's Athlete Health

No AI API is used.
"""

from __future__ import annotations

import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path("data/evidence_database.json")


# ---------------------------------------------------------------------------
# Specialty rules
# ---------------------------------------------------------------------------

SPECIALTY_RULES: dict[str, dict[str, Any]] = {

    "regenerative_medicine": {
        "strong_terms": {
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
            "orthobiologics",
            "regenerative medicine",
            "hyaluronic acid",
            "shockwave therapy",
            "extracorporeal shock wave therapy",
            "eswt",
            "prolotherapy",
        },

        "supporting_terms": {
            "tendon",
            "tendinopathy",
            "ligament",
            "cartilage",
            "osteoarthritis",
            "muscle",
            "musculoskeletal",
            "joint",
            "knee",
            "hip",
            "shoulder",
            "ankle",
            "elbow",
            "spine",
            "sports injury",
        },

        "minimum_score": 3,
    },

    "sports_performance": {
        "strong_terms": {
            "athletic performance",
            "sports performance",
            "sprint performance",
            "sprinting",
            "speed endurance",
            "running performance",
            "jump performance",
            "vertical jump",
            "strength performance",
            "power output",
            "rate of force development",
            "training adaptation",
            "training load",
            "overtraining",
            "fatigue",
            "recovery",
            "vo2max",
            "vo2 max",
            "maximal oxygen uptake",
            "lactate threshold",
            "anaerobic capacity",
            "aerobic capacity",
            "plyometric",
            "resistance training",
            "strength training",
            "endurance training",
        },

        "supporting_terms": {
            "athlete",
            "athletes",
            "sport",
            "sports",
            "exercise",
            "training",
            "competition",
            "return to sport",
            "return to play",
            "performance",
            "strength",
            "power",
            "speed",
            "endurance",
        },

        "minimum_score": 3,
    },

    "biomechanics": {
        "strong_terms": {
            "biomechanics",
            "biomechanical",
            "kinematics",
            "kinematic",
            "kinetics",
            "kinetic",
            "ground reaction force",
            "ground-reaction force",
            "joint moment",
            "joint moments",
            "joint torque",
            "joint loading",
            "force production",
            "rate of force development",
            "tendon stiffness",
            "leg stiffness",
            "running mechanics",
            "running gait",
            "gait analysis",
            "motion analysis",
            "motion capture",
            "landing mechanics",
            "jump mechanics",
            "sprint mechanics",
            "movement asymmetry",
            "force plate",
            "force plates",
            "center of pressure",
            "centre of pressure",
        },

        "supporting_terms": {
            "movement",
            "force",
            "velocity",
            "acceleration",
            "impulse",
            "moment",
            "torque",
            "stiffness",
            "gait",
            "running",
            "sprinting",
            "jumping",
            "landing",
            "tendon",
            "joint",
        },

        "minimum_score": 3,
    },

    "womens_athlete_health": {
        "strong_terms": {
            "female athlete",
            "female athletes",
            "women athletes",
            "relative energy deficiency in sport",
            "red-s",
            "reds",
            "low energy availability",
            "menstrual cycle",
            "menstrual function",
            "menstrual dysfunction",
            "amenorrhea",
            "oligomenorrhea",
            "female athlete triad",
            "bone mineral density",
            "bone health",
            "estradiol",
            "estrogen",
            "oral contraceptive",
            "hormonal contraception",
            "acl injury in women",
            "acl injury in female",
            "pregnancy",
            "postpartum",
        },

        "supporting_terms": {
            "female",
            "women",
            "woman",
            "menstrual",
            "hormone",
            "bone",
            "athlete",
            "sport",
            "injury",
            "performance",
            "recovery",
        },

        "minimum_score": 3,
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def contains_term(
    text: str,
    term: str,
) -> bool:
    term = term.lower().strip()

    if (
        len(term) <= 5
        and term.replace("-", "").isalnum()
    ):
        return re.search(
            rf"\b{re.escape(term)}\b",
            text,
        ) is not None

    return term in text


def load_database() -> list[dict[str, Any]]:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database does not exist: {DATABASE_PATH}"
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


def save_database(
    records: list[dict[str, Any]],
) -> None:
    temporary_path = DATABASE_PATH.with_suffix(
        ".json.tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temporary_path.replace(
        DATABASE_PATH
    )


def build_search_text(
    record: dict[str, Any],
) -> str:
    metadata = record.get(
        "metadata",
        {},
    )

    appraisal = record.get(
        "appraisal",
        {},
    )

    translation = record.get(
        "clinical_translation",
        {},
    )

    if not isinstance(metadata, dict):
        metadata = {}

    if not isinstance(appraisal, dict):
        appraisal = {}

    if not isinstance(translation, dict):
        translation = {}

    topics = metadata.get(
        "topics",
        [],
    )

    if not isinstance(topics, list):
        topics = []

    outcomes = appraisal.get(
        "identified_outcomes",
        [],
    )

    if not isinstance(outcomes, list):
        outcomes = []

    values = [
        metadata.get("title"),
        metadata.get("abstract"),
        metadata.get("topic"),
        " ".join(str(value) for value in topics),
        appraisal.get("intervention_or_exposure"),
        " ".join(str(value) for value in outcomes),
        translation.get("clinical_area"),
        translation.get("intervention_or_exposure"),
        translation.get("clinical_summary"),
        translation.get("practitioner_takeaway"),
    ]

    return clean_text(
        " ".join(
            clean_text(value)
            for value in values
        )
    ).lower()


# ---------------------------------------------------------------------------
# Specialty scoring
# ---------------------------------------------------------------------------

def calculate_specialty_score(
    text: str,
    strong_terms: set[str],
    supporting_terms: set[str],
) -> tuple[int, list[str]]:
    score = 0
    matches: list[str] = []

    for term in strong_terms:
        if contains_term(
            text,
            term,
        ):
            score += 3
            matches.append(term)

    for term in supporting_terms:
        if contains_term(
            text,
            term,
        ):
            score += 1
            matches.append(term)

    return (
        score,
        sorted(set(matches)),
    )


def route_specialty(
    text: str,
    rules: dict[str, Any],
) -> dict[str, Any]:
    strong_terms = rules.get(
        "strong_terms",
        set(),
    )

    supporting_terms = rules.get(
        "supporting_terms",
        set(),
    )

    minimum_score = int(
        rules.get(
            "minimum_score",
            3,
        )
    )

    score, matches = (
        calculate_specialty_score(
            text=text,
            strong_terms=strong_terms,
            supporting_terms=supporting_terms,
        )
    )

    return {
        "routed": True,
        "relevant": score >= minimum_score,
        "routing_score": score,
        "matched_terms": matches,
        "reviewed": False,
        "routed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# ---------------------------------------------------------------------------
# Safeguards
# ---------------------------------------------------------------------------

def apply_safeguards(
    specialty: str,
    result: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    result = dict(result)

    if specialty == "regenerative_medicine":

        strong_terms = (
            SPECIALTY_RULES[
                "regenerative_medicine"
            ]["strong_terms"]
        )

        has_regenerative_intervention = any(
            contains_term(
                text,
                term,
            )
            for term in strong_terms
        )

        if not has_regenerative_intervention:
            result["relevant"] = False
            result["routing_reason"] = (
                "No clearly identified regenerative or "
                "orthobiologic intervention."
            )

    if specialty == "womens_athlete_health":

        strong_terms = (
            SPECIALTY_RULES[
                "womens_athlete_health"
            ]["strong_terms"]
        )

        has_strong_term = any(
            contains_term(
                text,
                term,
            )
            for term in strong_terms
        )

        female_context = any(
            contains_term(
                text,
                term,
            )
            for term in {
                "female",
                "women",
                "woman",
            }
        )

        athlete_context = any(
            contains_term(
                text,
                term,
            )
            for term in {
                "athlete",
                "sport",
                "exercise",
                "performance",
                "injury",
            }
        )

        if not (
            has_strong_term
            or (
                female_context
                and athlete_context
            )
        ):
            result["relevant"] = False
            result["routing_reason"] = (
                "Insufficient female-athlete-specific context."
            )

    return result


# ---------------------------------------------------------------------------
# Route a record
# ---------------------------------------------------------------------------

def route_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    search_text = build_search_text(
        record
    )

    specialties = record.get(
        "specialties",
        {},
    )

    if not isinstance(specialties, dict):
        specialties = {}

    assigned_specialties: list[str] = []

    for specialty_name, rules in (
        SPECIALTY_RULES.items()
    ):
        routing = route_specialty(
            text=search_text,
            rules=rules,
        )

        routing = apply_safeguards(
            specialty=specialty_name,
            result=routing,
            text=search_text,
        )

        existing = specialties.get(
            specialty_name,
            {},
        )

        if not isinstance(existing, dict):
            existing = {}

        # Preserve future specialist-review fields while
        # updating the routing information.
        existing.update(
            routing
        )

        specialties[
            specialty_name
        ] = existing

        if routing.get(
            "relevant",
            False,
        ):
            assigned_specialties.append(
                specialty_name
            )

    record[
        "specialties"
    ] = specialties

    pipeline = record.get(
        "pipeline",
        {},
    )

    if not isinstance(pipeline, dict):
        pipeline = {}

    pipeline[
        "specialty_routing_complete"
    ] = True

    pipeline[
        "specialties_assigned"
    ] = assigned_specialties

    pipeline[
        "specialty_routed_at"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    record[
        "pipeline"
    ] = pipeline

    title = clean_text(
        record.get(
            "metadata",
            {},
        ).get(
            "title",
            "",
        )
    )

    assignments = (
        ", ".join(
            assigned_specialties
        )
        if assigned_specialties
        else "none"
    )

    print(
        f"Routed: {title[:70]} -> {assignments}"
    )

    return record


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 72)
    print(
        "Optimize Evidence Specialty Router"
    )
    print("=" * 72)

    records = load_database()

    print(
        f"Papers loaded: {len(records)}"
    )
    print()

    routed_records = [
        route_record(record)
        for record in records
    ]

    save_database(
        routed_records
    )

    counts = {
        specialty: 0
        for specialty
        in SPECIALTY_RULES
    }

    no_specialty = 0

    for record in routed_records:

        assigned = (
            record.get(
                "pipeline",
                {},
            ).get(
                "specialties_assigned",
                [],
            )
        )

        if not assigned:
            no_specialty += 1

        for specialty in assigned:
            if specialty in counts:
                counts[
                    specialty
                ] += 1

    print()
    print("=" * 72)
    print("Specialty Routing Summary")
    print("=" * 72)

    for specialty, count in counts.items():
        print(
            f"{specialty}: {count}"
        )

    print(
        f"No specialty assigned: {no_specialty}"
    )

    print(
        f"Updated database: {DATABASE_PATH}"
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
            "\nSpecialty routing cancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nSpecialty router failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
