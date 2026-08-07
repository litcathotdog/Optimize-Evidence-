"""
Optimize Evidence: Unified Specialty Reviewer

Reads:
    data/evidence_database.json

Writes:
    data/evidence_database.json

Purpose
-------
Review each paper only within the specialties assigned by
specialty_router.py.

Current specialties:
- Regenerative Medicine
- Sports Performance
- Biomechanics
- Women's Athlete Health

No external AI API is used.
All reviews are formula-based and transparent.
"""

from __future__ import annotations

import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path("data/evidence_database.json")


# ===========================================================================
# GENERAL HELPERS
# ===========================================================================

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
        return (
            re.search(
                rf"\b{re.escape(term)}\b",
                text,
            )
            is not None
        )

    return term in text


def contains_any(
    text: str,
    terms: set[str] | tuple[str, ...],
) -> bool:
    return any(
        contains_term(text, term)
        for term in terms
    )


def clamp(
    value: int,
    minimum: int,
    maximum: int,
) -> int:
    return max(
        minimum,
        min(value, maximum),
    )


def load_database() -> list[dict[str, Any]]:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
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


def get_metadata(
    record: dict[str, Any],
) -> dict[str, Any]:
    value = record.get(
        "metadata",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_appraisal(
    record: dict[str, Any],
) -> dict[str, Any]:
    value = record.get(
        "appraisal",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_statistics(
    record: dict[str, Any],
) -> dict[str, Any]:
    value = record.get(
        "statistics",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_translation(
    record: dict[str, Any],
) -> dict[str, Any]:
    value = record.get(
        "clinical_translation",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def get_specialties(
    record: dict[str, Any],
) -> dict[str, Any]:
    value = record.get(
        "specialties",
        {},
    )

    return (
        value
        if isinstance(value, dict)
        else {}
    )


def build_search_text(
    record: dict[str, Any],
) -> str:
    metadata = get_metadata(record)
    appraisal = get_appraisal(record)
    translation = get_translation(record)

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
        " ".join(
            clean_text(value)
            for value in topics
        ),
        appraisal.get(
            "intervention_or_exposure"
        ),
        " ".join(
            clean_text(value)
            for value in outcomes
        ),
        translation.get(
            "clinical_area"
        ),
        translation.get(
            "intervention_or_exposure"
        ),
        translation.get(
            "clinical_summary"
        ),
        translation.get(
            "practitioner_takeaway"
        ),
    ]

    return clean_text(
        " ".join(
            clean_text(value)
            for value in values
        )
    ).lower()


def base_quality_score(
    record: dict[str, Any],
) -> int:
    """
    Combine evidence and statistics scores into a simple 1–10 prior.
    """

    appraisal = get_appraisal(record)
    statistics = get_statistics(record)

    appraisal_scores = appraisal.get(
        "scores",
        {},
    )

    statistics_scores = statistics.get(
        "scores",
        {},
    )

    if not isinstance(
        appraisal_scores,
        dict,
    ):
        appraisal_scores = {}

    if not isinstance(
        statistics_scores,
        dict,
    ):
        statistics_scores = {}

    evidence_score = int(
        appraisal_scores.get(
            "overall_evidence",
            0,
        )
        or 0
    )

    stats_score = int(
        statistics_scores.get(
            "overall_statistics",
            0,
        )
        or 0
    )

    if evidence_score == 0 and stats_score == 0:
        return 3

    if evidence_score == 0:
        return clamp(
            stats_score,
            1,
            10,
        )

    if stats_score == 0:
        return clamp(
            evidence_score,
            1,
            10,
        )

    return clamp(
        round(
            evidence_score * 0.60
            + stats_score * 0.40
        ),
        1,
        10,
    )


def should_review(
    record: dict[str, Any],
    specialty_name: str,
) -> bool:
    specialties = get_specialties(record)

    specialty = specialties.get(
        specialty_name,
        {},
    )

    if not isinstance(
        specialty,
        dict,
    ):
        return False

    return bool(
        specialty.get(
            "relevant",
            False,
        )
    )


def update_specialty_section(
    record: dict[str, Any],
    specialty_name: str,
    review_data: dict[str, Any],
) -> dict[str, Any]:
    specialties = get_specialties(record)

    current = specialties.get(
        specialty_name,
        {},
    )

    if not isinstance(
        current,
        dict,
    ):
        current = {}

    current.update(
        review_data
    )

    specialties[
        specialty_name
    ] = current

    record[
        "specialties"
    ] = specialties

    return record


# ===========================================================================
# REGENERATIVE MEDICINE REVIEWER
# ===========================================================================

REGENERATIVE_THERAPIES: dict[
    str,
    tuple[str, ...],
] = {
    "Platelet-rich plasma": (
        "platelet-rich plasma",
        "platelet rich plasma",
        "prp",
    ),
    "Bone marrow aspirate concentrate": (
        "bone marrow aspirate concentrate",
        "bmac",
    ),
    "Mesenchymal cell therapy": (
        "mesenchymal stem cell",
        "mesenchymal stromal cell",
        "mesenchymal stem cells",
        "mesenchymal stromal cells",
    ),
    "Exosome / extracellular vesicle therapy": (
        "exosome",
        "exosomes",
        "extracellular vesicle",
        "extracellular vesicles",
    ),
    "Hyaluronic acid": (
        "hyaluronic acid",
        "hyaluronan",
    ),
    "Shockwave therapy": (
        "shockwave",
        "shock wave",
        "extracorporeal shock wave",
        "eswt",
    ),
    "Prolotherapy": (
        "prolotherapy",
        "dextrose injection",
    ),
}


REGENERATIVE_TISSUES: dict[
    str,
    tuple[str, ...],
] = {
    "Tendon": (
        "tendon",
        "tendinopathy",
        "achilles",
        "patellar tendon",
        "rotator cuff",
    ),
    "Ligament": (
        "ligament",
        "acl",
        "mcl",
        "anterior cruciate ligament",
    ),
    "Cartilage": (
        "cartilage",
        "chondral",
        "osteochondral",
    ),
    "Joint / osteoarthritis": (
        "osteoarthritis",
        "joint",
        "knee osteoarthritis",
        "hip osteoarthritis",
    ),
    "Muscle": (
        "muscle injury",
        "skeletal muscle",
        "muscle strain",
    ),
    "Bone": (
        "bone healing",
        "fracture",
        "bone regeneration",
    ),
}


PREPARATION_TERMS = {
    "leukocyte-rich",
    "leukocyte rich",
    "leukocyte-poor",
    "leukocyte poor",
    "platelet concentration",
    "platelet count",
    "centrifugation",
    "single spin",
    "double spin",
    "activation",
    "cell count",
    "cell dose",
    "viability",
    "injection volume",
}


SAFETY_TERMS = {
    "adverse event",
    "adverse events",
    "complication",
    "complications",
    "infection",
    "safety",
    "tolerability",
}


def identify_labels(
    text: str,
    rules: dict[str, tuple[str, ...]],
) -> list[str]:
    labels: list[str] = []

    for label, terms in rules.items():
        if contains_any(
            text,
            terms,
        ):
            labels.append(label)

    return labels


def review_regenerative(
    record: dict[str, Any],
) -> dict[str, Any]:
    text = build_search_text(
        record
    )

    therapies = identify_labels(
        text,
        REGENERATIVE_THERAPIES,
    )

    tissues = identify_labels(
        text,
        REGENERATIVE_TISSUES,
    )

    preparation = [
        term
        for term in sorted(
            PREPARATION_TERMS
        )
        if contains_term(
            text,
            term,
        )
    ]

    safety = [
        term
        for term in sorted(
            SAFETY_TERMS
        )
        if contains_term(
            text,
            term,
        )
    ]

    preclinical_terms = {
        "in vitro",
        "animal model",
        "mouse",
        "mice",
        "rat",
        "rats",
        "murine",
        "preclinical",
    }

    human_terms = {
        "participants",
        "patients",
        "athletes",
        "clinical trial",
        "randomized controlled trial",
        "cohort",
    }

    preclinical = contains_any(
        text,
        preclinical_terms,
    )

    human = contains_any(
        text,
        human_terms,
    )

    if preclinical and not human:
        evidence_stage = "Preclinical"
    elif human:
        evidence_stage = "Human clinical"
    else:
        evidence_stage = "Unclear"

    flags: list[str] = []

    if therapies and not preparation:
        flags.append(
            "Preparation or biologic characterization is not clearly reported."
        )

    if not safety:
        flags.append(
            "Safety or adverse-event reporting is not clearly identifiable."
        )

    if evidence_stage == "Preclinical":
        flags.append(
            "Preclinical findings should not be interpreted as direct evidence of clinical effectiveness."
        )

    if (
        "Platelet-rich plasma"
        in therapies
        and not any(
            term in text
            for term in {
                "leukocyte-rich",
                "leukocyte-poor",
                "platelet concentration",
                "platelet count",
            }
        )
    ):
        flags.append(
            "PRP formulation appears incompletely characterized."
        )

    score = base_quality_score(
        record
    )

    if therapies:
        score += 1

    if tissues:
        score += 1

    if preparation:
        score += 1

    if safety:
        score += 1

    if evidence_stage == "Preclinical":
        score -= 3

    score = clamp(
        score,
        1,
        10,
    )

    if evidence_stage == "Preclinical":
        confidence = "Very low"
    elif score >= 8:
        confidence = "High"
    elif score >= 6:
        confidence = "Moderate"
    elif score >= 4:
        confidence = "Low"
    else:
        confidence = "Very low"

    therapy_text = (
        ", ".join(therapies)
        if therapies
        else "regenerative intervention"
    )

    tissue_text = (
        ", ".join(tissues)
        if tissues
        else "target condition"
    )

    takeaway = (
        f"This paper evaluates {therapy_text} in relation to "
        f"{tissue_text}. Domain confidence is {confidence.lower()}. "
        "Full-text review should verify preparation, dose, comparator, "
        "safety, and clinical applicability before treatment decisions."
    )

    return update_specialty_section(
        record,
        "regenerative_medicine",
        {
            "reviewed": True,
            "therapy_class": therapies,
            "target_tissue": tissues,
            "evidence_stage": evidence_stage,
            "preparation_details_identified": preparation,
            "safety_reporting_identified": safety,
            "domain_flags": flags[:8],
            "domain_score": score,
            "specialist_confidence": confidence,
            "specialist_takeaway": takeaway,
            "reviewed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


# ===========================================================================
# SPORTS PERFORMANCE REVIEWER
# ===========================================================================

PERFORMANCE_OUTCOMES: dict[
    str,
    tuple[str, ...],
] = {
    "Sprint speed": (
        "sprint time",
        "sprint speed",
        "sprint performance",
        "acceleration",
        "maximal velocity",
        "maximum velocity",
    ),
    "Jump performance": (
        "vertical jump",
        "countermovement jump",
        "cmj",
        "jump height",
        "jump performance",
    ),
    "Strength": (
        "maximal strength",
        "one repetition maximum",
        "1rm",
        "strength",
    ),
    "Power": (
        "peak power",
        "power output",
        "explosive power",
        "rate of force development",
    ),
    "Aerobic performance": (
        "vo2max",
        "vo2 max",
        "maximal oxygen uptake",
        "aerobic capacity",
        "running economy",
    ),
    "Anaerobic performance": (
        "anaerobic capacity",
        "wingate",
        "lactate threshold",
        "repeated sprint",
    ),
    "Recovery": (
        "recovery",
        "fatigue",
        "muscle soreness",
        "doms",
        "heart rate variability",
    ),
    "Return to sport": (
        "return to sport",
        "return to play",
        "reinjury",
    ),
}


TRAINING_INTERVENTIONS = {
    "resistance training",
    "strength training",
    "plyometric",
    "sprint training",
    "speed training",
    "endurance training",
    "interval training",
    "high intensity interval training",
    "hiit",
    "eccentric training",
    "isometric training",
    "power training",
}


def review_sports_performance(
    record: dict[str, Any],
) -> dict[str, Any]:
    text = build_search_text(
        record
    )

    outcomes = identify_labels(
        text,
        PERFORMANCE_OUTCOMES,
    )

    interventions = [
        term
        for term in sorted(
            TRAINING_INTERVENTIONS
        )
        if contains_term(
            text,
            term,
        )
    ]

    athlete_specific = contains_any(
        text,
        {
            "athlete",
            "athletes",
            "elite athlete",
            "competitive athlete",
            "trained",
            "sport",
        },
    )

    performance_specific = bool(
        outcomes
    )

    flags: list[str] = []

    if not athlete_specific:
        flags.append(
            "The study population may not represent trained or competitive athletes."
        )

    if not performance_specific:
        flags.append(
            "Direct athletic-performance outcomes are not clearly identified."
        )

    if (
        "performance" in text
        and not outcomes
    ):
        flags.append(
            "The paper uses performance-related terminology without a clearly identified objective performance outcome."
        )

    score = base_quality_score(
        record
    )

    if athlete_specific:
        score += 1

    if performance_specific:
        score += 2

    if interventions:
        score += 1

    score = clamp(
        score,
        1,
        10,
    )

    if score >= 8:
        confidence = "High"
    elif score >= 6:
        confidence = "Moderate"
    elif score >= 4:
        confidence = "Low"
    else:
        confidence = "Very low"

    if outcomes:
        outcome_text = ", ".join(
            outcomes
        )
    else:
        outcome_text = (
            "no clearly identified direct performance outcome"
        )

    takeaway = (
        f"The study is relevant to {outcome_text}. "
        f"Sports-performance confidence is {confidence.lower()}. "
        "Transfer to competitive athletes depends on training status, "
        "intervention specificity, outcome validity, and similarity to "
        "real competition demands."
    )

    return update_specialty_section(
        record,
        "sports_performance",
        {
            "reviewed": True,
            "performance_outcomes": outcomes,
            "training_interventions": interventions,
            "athlete_specific_population": athlete_specific,
            "direct_performance_outcomes": performance_specific,
            "domain_flags": flags[:8],
            "domain_score": score,
            "specialist_confidence": confidence,
            "specialist_takeaway": takeaway,
            "reviewed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


# ===========================================================================
# BIOMECHANICS REVIEWER
# ===========================================================================

BIOMECHANICS_VARIABLES: dict[
    str,
    tuple[str, ...],
] = {
    "Kinematics": (
        "kinematics",
        "joint angle",
        "angular velocity",
        "range of motion",
        "stride length",
        "step length",
        "contact time",
    ),
    "Kinetics": (
        "kinetics",
        "joint moment",
        "joint torque",
        "joint power",
        "ground reaction force",
        "ground-reaction force",
        "impulse",
    ),
    "Force production": (
        "force production",
        "peak force",
        "rate of force development",
        "force-time",
        "force plate",
    ),
    "Stiffness": (
        "tendon stiffness",
        "leg stiffness",
        "joint stiffness",
        "muscle stiffness",
    ),
    "Running mechanics": (
        "running mechanics",
        "running gait",
        "sprint mechanics",
        "stride frequency",
        "step frequency",
    ),
    "Landing mechanics": (
        "landing mechanics",
        "landing",
        "drop jump",
        "valgus",
    ),
}


MEASUREMENT_SYSTEMS = {
    "motion capture",
    "force plate",
    "force plates",
    "inertial measurement unit",
    "imu",
    "wearable sensor",
    "electromyography",
    "emg",
    "3d motion",
    "three-dimensional motion",
}


def review_biomechanics(
    record: dict[str, Any],
) -> dict[str, Any]:
    text = build_search_text(
        record
    )

    variables = identify_labels(
        text,
        BIOMECHANICS_VARIABLES,
    )

    measurement_systems = [
        term
        for term in sorted(
            MEASUREMENT_SYSTEMS
        )
        if contains_term(
            text,
            term,
        )
    ]

    links_to_clinical_outcome = contains_any(
        text,
        {
            "pain",
            "injury",
            "return to sport",
            "performance",
            "function",
            "reinjury",
        },
    )

    flags: list[str] = []

    if not variables:
        flags.append(
            "No specific biomechanical outcome is clearly identifiable."
        )

    if not measurement_systems:
        flags.append(
            "The measurement system is not clearly identifiable from the abstract."
        )

    if not links_to_clinical_outcome:
        flags.append(
            "The biomechanical finding is not clearly linked to a clinical or performance outcome."
        )

    if (
        variables
        and not links_to_clinical_outcome
    ):
        flags.append(
            "A biomechanical difference should not automatically be interpreted as a meaningful clinical benefit."
        )

    score = base_quality_score(
        record
    )

    if variables:
        score += 2

    if measurement_systems:
        score += 1

    if links_to_clinical_outcome:
        score += 1

    score = clamp(
        score,
        1,
        10,
    )

    if score >= 8:
        confidence = "High"
    elif score >= 6:
        confidence = "Moderate"
    elif score >= 4:
        confidence = "Low"
    else:
        confidence = "Very low"

    variable_text = (
        ", ".join(variables)
        if variables
        else "biomechanical outcomes"
    )

    takeaway = (
        f"This study evaluates {variable_text}. "
        f"Biomechanics confidence is {confidence.lower()}. "
        "Interpret mechanical changes separately from clinical significance; "
        "changes in joint angles, forces, or stiffness do not necessarily "
        "translate into better performance or lower injury risk."
    )

    return update_specialty_section(
        record,
        "biomechanics",
        {
            "reviewed": True,
            "biomechanical_variables": variables,
            "measurement_systems": measurement_systems,
            "linked_to_clinical_or_performance_outcome": (
                links_to_clinical_outcome
            ),
            "domain_flags": flags[:8],
            "domain_score": score,
            "specialist_confidence": confidence,
            "specialist_takeaway": takeaway,
            "reviewed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


# ===========================================================================
# WOMEN'S ATHLETE HEALTH REVIEWER
# ===========================================================================

WOMENS_HEALTH_DOMAINS: dict[
    str,
    tuple[str, ...],
] = {
    "Energy availability / RED-S": (
        "relative energy deficiency in sport",
        "red-s",
        "reds",
        "low energy availability",
        "energy availability",
        "female athlete triad",
    ),
    "Menstrual health": (
        "menstrual cycle",
        "menstrual function",
        "menstrual dysfunction",
        "amenorrhea",
        "oligomenorrhea",
    ),
    "Bone health": (
        "bone mineral density",
        "bone health",
        "bone mineral content",
        "stress fracture",
        "bone stress injury",
    ),
    "Hormonal physiology": (
        "estradiol",
        "estrogen",
        "progesterone",
        "hormonal contraception",
        "oral contraceptive",
    ),
    "Female injury risk": (
        "female acl",
        "acl injury",
        "anterior cruciate ligament",
        "injury risk",
    ),
    "Pregnancy / postpartum": (
        "pregnancy",
        "pregnant athlete",
        "postpartum",
        "post-partum",
    ),
}


SEX_SPECIFIC_ANALYSIS_TERMS = {
    "sex-specific",
    "sex specific",
    "female-specific",
    "female specific",
    "interaction by sex",
    "sex interaction",
    "stratified by sex",
    "women only",
    "female participants",
}


def review_womens_athlete_health(
    record: dict[str, Any],
) -> dict[str, Any]:
    text = build_search_text(
        record
    )

    domains = identify_labels(
        text,
        WOMENS_HEALTH_DOMAINS,
    )

    female_population = contains_any(
        text,
        {
            "female athlete",
            "female athletes",
            "women athletes",
            "female participants",
            "women participants",
            "women",
            "female",
        },
    )

    sex_specific_analysis = contains_any(
        text,
        SEX_SPECIFIC_ANALYSIS_TERMS,
    )

    athlete_context = contains_any(
        text,
        {
            "athlete",
            "athletes",
            "sport",
            "sports",
            "training",
            "performance",
            "competition",
        },
    )

    flags: list[str] = []

    if not female_population:
        flags.append(
            "A clearly defined female participant population is not identifiable."
        )

    if not sex_specific_analysis:
        flags.append(
            "Sex-specific analysis is not clearly reported in the abstract."
        )

    if not athlete_context:
        flags.append(
            "The findings may not be specific to athletic populations."
        )

    if (
        "menstrual cycle" in text
        and not any(
            term in text
            for term in {
                "cycle phase",
                "menstrual phase",
                "ovulation",
                "hormone concentration",
                "estradiol",
                "progesterone",
            }
        )
    ):
        flags.append(
            "Menstrual-cycle phase or hormonal verification is not clearly described."
        )

    score = base_quality_score(
        record
    )

    if female_population:
        score += 1

    if domains:
        score += 2

    if sex_specific_analysis:
        score += 1

    if athlete_context:
        score += 1

    score = clamp(
        score,
        1,
        10,
    )

    if score >= 8:
        confidence = "High"
    elif score >= 6:
        confidence = "Moderate"
    elif score >= 4:
        confidence = "Low"
    else:
        confidence = "Very low"

    domain_text = (
        ", ".join(domains)
        if domains
        else "female-athlete health"
    )

    takeaway = (
        f"This paper addresses {domain_text}. "
        f"Women's-athlete-health confidence is {confidence.lower()}. "
        "Interpretation should consider whether female participants were "
        "adequately represented, whether sex-specific analyses were performed, "
        "and whether menstrual, hormonal, bone-health, and training variables "
        "were measured appropriately."
    )

    return update_specialty_section(
        record,
        "womens_athlete_health",
        {
            "reviewed": True,
            "health_domains": domains,
            "female_population_identified": female_population,
            "athlete_context_identified": athlete_context,
            "sex_specific_analysis_identified": (
                sex_specific_analysis
            ),
            "domain_flags": flags[:8],
            "domain_score": score,
            "specialist_confidence": confidence,
            "specialist_takeaway": takeaway,
            "reviewed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


# ===========================================================================
# RUN ALL RELEVANT SPECIALISTS
# ===========================================================================

def review_record(
    record: dict[str, Any],
) -> dict[str, Any]:
    title = clean_text(
        get_metadata(record).get(
            "title"
        )
    )

    reviewed: list[str] = []

    if should_review(
        record,
        "regenerative_medicine",
    ):
        record = review_regenerative(
            record
        )
        reviewed.append(
            "regenerative_medicine"
        )

    if should_review(
        record,
        "sports_performance",
    ):
        record = review_sports_performance(
            record
        )
        reviewed.append(
            "sports_performance"
        )

    if should_review(
        record,
        "biomechanics",
    ):
        record = review_biomechanics(
            record
        )
        reviewed.append(
            "biomechanics"
        )

    if should_review(
        record,
        "womens_athlete_health",
    ):
        record = review_womens_athlete_health(
            record
        )
        reviewed.append(
            "womens_athlete_health"
        )

    pipeline = record.get(
        "pipeline",
        {},
    )

    if not isinstance(
        pipeline,
        dict,
    ):
        pipeline = {}

    pipeline[
        "specialty_review_complete"
    ] = True

    pipeline[
        "specialties_reviewed"
    ] = reviewed

    pipeline[
        "specialty_reviewed_at"
    ] = datetime.now(
        timezone.utc
    ).isoformat()

    record[
        "pipeline"
    ] = pipeline

    print(
        f"Specialty review: {title[:65]} -> "
        f"{', '.join(reviewed) if reviewed else 'no specialist needed'}"
    )

    return record


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> int:
    print("=" * 72)
    print(
        "Optimize Evidence Unified Specialty Reviewer"
    )
    print("=" * 72)

    records = load_database()

    print(
        f"Papers loaded: {len(records)}"
    )
    print()

    updated_records: list[
        dict[str, Any]
    ] = []

    counts = {
        "regenerative_medicine": 0,
        "sports_performance": 0,
        "biomechanics": 0,
        "womens_athlete_health": 0,
    }

    for record in records:
        before = get_specialties(
            record
        )

        for specialty in counts:
            specialty_data = before.get(
                specialty,
                {},
            )

            if (
                isinstance(
                    specialty_data,
                    dict,
                )
                and specialty_data.get(
                    "relevant",
                    False,
                )
            ):
                counts[
                    specialty
                ] += 1

        record = review_record(
            record
        )

        updated_records.append(
            record
        )

    save_database(
        updated_records
    )

    print()
    print("=" * 72)
    print("Specialty Review Summary")
    print("=" * 72)

    for specialty, count in (
        counts.items()
    ):
        print(
            f"{specialty}: {count}"
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
            "\nSpecialty review cancelled.",
            file=sys.stderr,
        )
        raise SystemExit(130)

    except Exception as error:
        print(
            f"\nSpecialty reviewer failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
