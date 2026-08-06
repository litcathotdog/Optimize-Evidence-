"""
Optimize Evidence: Formula-Based Evidence Appraiser

This script reads research papers collected by research_librarian.py and
applies transparent, rule-based appraisal formulas.

Input:
    data/papers.json

Output:
    data/appraised_papers.json

No AI API or external Python packages are required.
"""

from __future__ import annotations

import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INPUT_PATH = Path("data/papers.json")
OUTPUT_PATH = Path("data/appraised_papers.json")


# ---------------------------------------------------------------------------
# Study-design rules
# ---------------------------------------------------------------------------

STUDY_DESIGN_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "Umbrella review",
        (
            "umbrella review",
            "overview of systematic reviews",
        ),
    ),
    (
        "Systematic review and meta-analysis",
        (
            "systematic review and meta-analysis",
            "systematic review with meta-analysis",
            "systematic review and network meta-analysis",
        ),
    ),
    (
        "Network meta-analysis",
        (
            "network meta-analysis",
        ),
    ),
    (
        "Meta-analysis",
        (
            "meta-analysis",
            "meta analysis",
        ),
    ),
    (
        "Systematic review",
        (
            "systematic review",
        ),
    ),
    (
        "Randomized controlled trial",
        (
            "randomized controlled trial",
            "randomised controlled trial",
            "randomized clinical trial",
            "randomised clinical trial",
            "double-blind randomized",
            "double blind randomized",
            "double-blind randomised",
            "placebo-controlled trial",
            "placebo controlled trial",
        ),
    ),
    (
        "Controlled clinical trial",
        (
            "controlled clinical trial",
            "non-randomized controlled trial",
            "nonrandomized controlled trial",
            "non-randomised controlled trial",
        ),
    ),
    (
        "Prospective cohort study",
        (
            "prospective cohort",
            "prospective observational",
            "prospectively enrolled",
        ),
    ),
    (
        "Retrospective cohort study",
        (
            "retrospective cohort",
            "retrospective observational",
            "medical records were reviewed",
            "chart review",
        ),
    ),
    (
        "Cohort study",
        (
            "cohort study",
            "longitudinal cohort",
            "longitudinal study",
        ),
    ),
    (
        "Case-control study",
        (
            "case-control",
            "case control",
        ),
    ),
    (
        "Cross-sectional study",
        (
            "cross-sectional",
            "cross sectional",
        ),
    ),
    (
        "Diagnostic or validation study",
        (
            "diagnostic accuracy",
            "validation study",
            "method comparison",
            "agreement study",
            "reliability study",
            "validity study",
        ),
    ),
    (
        "Case series",
        (
            "case series",
        ),
    ),
    (
        "Case report",
        (
            "case report",
        ),
    ),
    (
        "Consensus statement or guideline",
        (
            "consensus statement",
            "clinical practice guideline",
            "practice guideline",
            "position statement",
            "expert consensus",
        ),
    ),
    (
        "Narrative review",
        (
            "narrative review",
            "literature review",
            "clinical review",
        ),
    ),
    (
        "Laboratory or preclinical study",
        (
            "in vitro",
            "animal model",
            "murine model",
            "rat model",
            "mouse model",
            "laboratory study",
            "preclinical study",
        ),
    ),
]


BASE_DESIGN_SCORES: dict[str, int] = {
    "Umbrella review": 9,
    "Systematic review and meta-analysis": 9,
    "Network meta-analysis": 9,
    "Meta-analysis": 8,
    "Systematic review": 8,
    "Randomized controlled trial": 8,
    "Controlled clinical trial": 6,
    "Prospective cohort study": 6,
    "Retrospective cohort study": 5,
    "Cohort study": 5,
    "Case-control study": 5,
    "Cross-sectional study": 4,
    "Diagnostic or validation study": 5,
    "Consensus statement or guideline": 6,
    "Narrative review": 3,
    "Case series": 2,
    "Case report": 1,
    "Laboratory or preclinical study": 2,
    "Other research article": 3,
}


# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------

POSITIVE_METHOD_TERMS = {
    "randomized": 1,
    "randomised": 1,
    "double-blind": 1,
    "double blind": 1,
    "placebo-controlled": 1,
    "placebo controlled": 1,
    "concealed allocation": 1,
    "intention-to-treat": 1,
    "intention to treat": 1,
    "preregistered": 1,
    "pre-registered": 1,
    "multicenter": 1,
    "multicentre": 1,
    "prospective": 1,
    "blinded assessor": 1,
    "assessor blinded": 1,
}

LIMITATION_RULES: list[tuple[str, str]] = [
    (
        "small sample",
        "The study may have limited statistical power because of its small sample.",
    ),
    (
        "pilot study",
        "This was a pilot study and may not be sufficiently powered for definitive conclusions.",
    ),
    (
        "single-center",
        "The single-center design may limit generalizability.",
    ),
    (
        "single centre",
        "The single-center design may limit generalizability.",
    ),
    (
        "retrospective",
        "The retrospective design increases the risk of selection bias and incomplete data.",
    ),
    (
        "cross-sectional",
        "The cross-sectional design cannot establish causality or temporal direction.",
    ),
    (
        "self-reported",
        "Self-reported outcomes may be affected by recall or response bias.",
    ),
    (
        "self reported",
        "Self-reported outcomes may be affected by recall or response bias.",
    ),
    (
        "short follow-up",
        "The follow-up duration may be too short to evaluate long-term outcomes.",
    ),
    (
        "short-term follow-up",
        "The follow-up duration may be too short to evaluate long-term outcomes.",
    ),
    (
        "lost to follow-up",
        "Loss to follow-up may have introduced attrition bias.",
    ),
    (
        "lack of blinding",
        "Lack of blinding may have influenced treatment or outcome assessment.",
    ),
    (
        "not blinded",
        "Lack of blinding may have influenced treatment or outcome assessment.",
    ),
    (
        "no control group",
        "The absence of a control group makes it difficult to separate treatment effects from natural recovery.",
    ),
    (
        "without a control group",
        "The absence of a control group makes it difficult to separate treatment effects from natural recovery.",
    ),
    (
        "observational",
        "The observational design may be affected by confounding and cannot establish causality.",
    ),
    (
        "heterogeneity",
        "Substantial heterogeneity may reduce confidence in the pooled estimate.",
    ),
]

PRACTITIONER_TERMS = {
    "return to sport": 3,
    "return to play": 3,
    "pain": 1,
    "function": 2,
    "strength": 2,
    "performance": 2,
    "rehabilitation": 3,
    "injury": 2,
    "reinjury": 3,
    "tendon": 2,
    "tendinopathy": 3,
    "ligament": 2,
    "cartilage": 2,
    "osteoarthritis": 2,
    "platelet-rich plasma": 3,
    "platelet rich plasma": 3,
    "prp": 2,
    "bone marrow aspirate concentrate": 3,
    "orthobiologic": 3,
    "athlete": 2,
    "sport": 1,
    "exercise": 1,
    "training": 1,
    "sleep": 1,
    "recovery": 2,
    "low energy availability": 3,
    "relative energy deficiency in sport": 3,
    "red-s": 3,
}

CLINICAL_OUTCOME_TERMS = {
    "pain",
    "function",
    "strength",
    "range of motion",
    "return to sport",
    "return to play",
    "reinjury",
    "quality of life",
    "performance",
    "muscle strength",
    "tendon function",
    "healing",
    "recovery",
    "adverse events",
    "injury rate",
    "symptoms",
    "disability",
}


# ---------------------------------------------------------------------------
# Basic helpers
# ---------------------------------------------------------------------------

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return re.sub(r"\s+", " ", str(value)).strip()


def normalized_text(*values: Any) -> str:
    return clean_text(" ".join(clean_text(value) for value in values)).lower()


def contains_term(text: str, term: str) -> bool:
    normalized_term = term.lower()

    if len(normalized_term) <= 5 and normalized_term.replace("-", "").isalnum():
        return re.search(
            rf"\b{re.escape(normalized_term)}\b",
            text,
        ) is not None

    return normalized_term in text


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


# ---------------------------------------------------------------------------
# Study classification
# ---------------------------------------------------------------------------

def classify_study_design(paper: dict[str, Any]) -> str:
    title = clean_text(paper.get("title"))
    abstract = clean_text(paper.get("abstract"))
    existing_type = clean_text(paper.get("study_type"))
    publication_types = paper.get("publication_types", [])

    if not isinstance(publication_types, list):
        publication_types = []

    text = normalized_text(
        title,
        abstract,
        existing_type,
        " ".join(str(item) for item in publication_types),
    )

    for design, terms in STUDY_DESIGN_RULES:
        if any(term in text for term in terms):
            return design

    if existing_type:
        return existing_type

    return "Other research article"


# ---------------------------------------------------------------------------
# Sample-size extraction
# ---------------------------------------------------------------------------

def extract_sample_size(abstract: str) -> int | None:
    """
    Extract likely participant sample size.

    The function prioritizes common research phrases and avoids numbers
    associated with years, percentages, and statistical values.
    """

    patterns = [
        r"\b(?:included|enrolled|recruited|studied|analyzed|analysed)\s+"
        r"(?:a total of\s+)?(\d{1,5})\s+"
        r"(?:participants|patients|athletes|subjects|individuals|adults|children)",

        r"\b(?:a total of|totaling)\s+(\d{1,5})\s+"
        r"(?:participants|patients|athletes|subjects|individuals)",

        r"\b(\d{1,5})\s+"
        r"(?:participants|patients|athletes|subjects|individuals)\s+"
        r"(?:were|was)\s+(?:included|enrolled|recruited|randomized|randomised)",

        r"\bsample\s+(?:consisted of|comprised|included)\s+"
        r"(\d{1,5})",

        r"\bn\s*=\s*(\d{1,5})\b",
    ]

    text = clean_text(abstract)

    candidates: list[int] = []

    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = int(match.group(1))

            if 2 <= value <= 100000:
                candidates.append(value)

    if not candidates:
        return None

    return max(candidates)


# ---------------------------------------------------------------------------
# Population and intervention extraction
# ---------------------------------------------------------------------------

def extract_population(abstract: str) -> str:
    patterns = [
        r"(?:included|enrolled|recruited|studied)\s+"
        r"(?:a total of\s+)?\d{1,5}\s+"
        r"([^.;]{5,150})",

        r"(?:participants|patients|athletes)\s+(?:were|with)\s+"
        r"([^.;]{5,150})",

        r"(?:we studied|we recruited|we enrolled)\s+"
        r"([^.;]{5,150})",
    ]

    for pattern in patterns:
        match = re.search(pattern, abstract, flags=re.IGNORECASE)

        if match:
            population = clean_text(match.group(1))
            return population[:200]

    return "Population not reliably extractable from the abstract."


def extract_intervention(abstract: str) -> str:
    patterns = [
        r"(?:received|underwent|were assigned to|were randomized to|"
        r"were randomised to)\s+([^.;]{5,180})",

        r"(?:intervention consisted of|treatment consisted of)\s+"
        r"([^.;]{5,180})",

        r"(?:we evaluated|we investigated|we compared)\s+"
        r"([^.;]{5,180})",
    ]

    for pattern in patterns:
        match = re.search(pattern, abstract, flags=re.IGNORECASE)

        if match:
            intervention = clean_text(match.group(1))
            return intervention[:220]

    return "Intervention or exposure not reliably extractable from the abstract."


def extract_outcomes(abstract: str) -> list[str]:
    text = abstract.lower()

    outcomes = [
        outcome.title()
        for outcome in sorted(CLINICAL_OUTCOME_TERMS)
        if contains_term(text, outcome)
    ]

    return outcomes[:10]


# ---------------------------------------------------------------------------
# Limitation detection
# ---------------------------------------------------------------------------

def detect_limitations(
    paper: dict[str, Any],
    study_design: str,
    sample_size: int | None,
) -> list[str]:
    abstract = clean_text(paper.get("abstract"))
    text = abstract.lower()

    limitations: list[str] = []

    for trigger, explanation in LIMITATION_RULES:
        if trigger in text and explanation not in limitations:
            limitations.append(explanation)

    if sample_size is not None:
        if sample_size < 20:
            limitations.append(
                "The very small sample substantially limits precision and generalizability."
            )
        elif sample_size < 50:
            limitations.append(
                "The modest sample size may limit statistical power and subgroup analysis."
            )

    design_limitations = {
        "Case report": (
            "A single case cannot establish effectiveness or generalize to a broader population."
        ),
        "Case series": (
            "The uncontrolled case-series design cannot establish comparative effectiveness."
        ),
        "Cross-sectional study": (
            "The cross-sectional design cannot determine whether the exposure preceded the outcome."
        ),
        "Retrospective cohort study": (
            "Retrospective data may contain selection bias, missing data, and uncontrolled confounding."
        ),
        "Cohort study": (
            "As an observational study, the findings may reflect confounding rather than causation."
        ),
        "Narrative review": (
            "The review may not have used a systematic search or formal risk-of-bias assessment."
        ),
        "Laboratory or preclinical study": (
            "Laboratory or animal findings may not translate directly to human clinical practice."
        ),
    }

    design_limitation = design_limitations.get(study_design)

    if design_limitation and design_limitation not in limitations:
        limitations.append(design_limitation)

    if not limitations:
        limitations.append(
            "The abstract does not provide enough information for a complete risk-of-bias assessment."
        )

    return limitations[:6]


# ---------------------------------------------------------------------------
# Scoring formulas
# ---------------------------------------------------------------------------

def calculate_methodology_score(
    paper: dict[str, Any],
    study_design: str,
    sample_size: int | None,
) -> int:
    abstract = clean_text(paper.get("abstract"))
    text = abstract.lower()

    score = BASE_DESIGN_SCORES.get(study_design, 3)

    for term, points in POSITIVE_METHOD_TERMS.items():
        if term in text:
            score += points

    if sample_size is not None:
        if sample_size >= 1000:
            score += 2
        elif sample_size >= 200:
            score += 1
        elif sample_size < 20:
            score -= 2
        elif sample_size < 50:
            score -= 1

    penalty_terms = {
        "no control group": 2,
        "without a control group": 2,
        "convenience sample": 1,
        "high risk of bias": 2,
        "substantial heterogeneity": 1,
        "lost to follow-up": 1,
        "single-center": 1,
        "single centre": 1,
    }

    for term, penalty in penalty_terms.items():
        if term in text:
            score -= penalty

    return clamp(score, 1, 10)


def calculate_practitioner_relevance(
    paper: dict[str, Any],
    study_design: str,
) -> int:
    title = clean_text(paper.get("title"))
    abstract = clean_text(paper.get("abstract"))
    topic = clean_text(paper.get("topic"))

    text = normalized_text(title, abstract, topic)

    raw_score = 1

    for term, points in PRACTITIONER_TERMS.items():
        if contains_term(text, term):
            raw_score += points

    human_clinical_designs = {
        "Umbrella review",
        "Systematic review and meta-analysis",
        "Network meta-analysis",
        "Meta-analysis",
        "Systematic review",
        "Randomized controlled trial",
        "Controlled clinical trial",
        "Prospective cohort study",
        "Retrospective cohort study",
        "Cohort study",
        "Diagnostic or validation study",
        "Consensus statement or guideline",
    }

    if study_design in human_clinical_designs:
        raw_score += 2

    if study_design == "Laboratory or preclinical study":
        raw_score -= 3

    # Convert the accumulated score into a 1–10 rating.
    if raw_score >= 18:
        return 10
    if raw_score >= 15:
        return 9
    if raw_score >= 12:
        return 8
    if raw_score >= 10:
        return 7
    if raw_score >= 8:
        return 6
    if raw_score >= 6:
        return 5
    if raw_score >= 4:
        return 4

    return clamp(raw_score, 1, 3)


def calculate_reporting_completeness(
    paper: dict[str, Any],
    sample_size: int | None,
) -> int:
    abstract = clean_text(paper.get("abstract"))
    text = abstract.lower()

    score = 0

    if sample_size is not None:
        score += 2

    reporting_features = [
        "methods",
        "results",
        "conclusion",
        "confidence interval",
        "95% ci",
        "p=",
        "p<",
        "primary outcome",
        "follow-up",
    ]

    for feature in reporting_features:
        if feature in text:
            score += 1

    if len(abstract) >= 1000:
        score += 1

    return clamp(score, 1, 10)


def calculate_overall_evidence_score(
    methodology_score: int,
    practitioner_relevance: int,
    reporting_completeness: int,
) -> int:
    """
    Weighted evidence score.

    Methodology:            60%
    Practitioner relevance: 25%
    Reporting completeness: 15%
    """

    weighted_score = (
        methodology_score * 0.60
        + practitioner_relevance * 0.25
        + reporting_completeness * 0.15
    )

    return clamp(round(weighted_score), 1, 10)


def assign_evidence_strength(
    overall_score: int,
    study_design: str,
) -> str:
    # Preclinical and anecdotal evidence cannot receive a strong rating.
    if study_design in {
        "Case report",
        "Case series",
        "Laboratory or preclinical study",
    }:
        if overall_score >= 5:
            return "Low"
        return "Very low"

    if overall_score >= 9:
        return "Strong"
    if overall_score >= 7:
        return "Moderate"
    if overall_score >= 5:
        return "Low"

    return "Very low"


def assign_risk_of_bias(
    methodology_score: int,
    study_design: str,
) -> str:
    if study_design in {
        "Case report",
        "Case series",
        "Narrative review",
    }:
        return "High"

    if methodology_score >= 8:
        return "Low or unclear"
    if methodology_score >= 5:
        return "Moderate"

    return "High"


# ---------------------------------------------------------------------------
# Formulaic clinical interpretation
# ---------------------------------------------------------------------------

def detect_result_direction(abstract: str) -> str:
    text = abstract.lower()

    no_difference_terms = [
        "no significant difference",
        "not significantly different",
        "did not differ significantly",
        "no between-group difference",
        "no evidence of a difference",
    ]

    positive_terms = [
        "significantly improved",
        "significant improvement",
        "superior to",
        "greater improvement",
        "significantly reduced",
        "was effective",
        "were effective",
    ]

    negative_terms = [
        "worse outcomes",
        "increased risk",
        "adverse effect",
        "higher injury risk",
        "significantly worse",
    ]

    if any(term in text for term in no_difference_terms):
        return "No clear between-group advantage was reported."

    if any(term in text for term in positive_terms):
        return "The abstract reports a favorable association or treatment effect."

    if any(term in text for term in negative_terms):
        return "The abstract reports a potentially unfavorable effect or increased risk."

    return "The direction and clinical magnitude of the findings are not reliably extractable."


def generate_practice_takeaway(
    paper: dict[str, Any],
    study_design: str,
    evidence_strength: str,
    result_direction: str,
) -> str:
    topic = clean_text(paper.get("topic")) or "this clinical area"

    if study_design == "Laboratory or preclinical study":
        return (
            "This study is hypothesis-generating. It should not directly change "
            "patient care until its findings are confirmed in human clinical studies."
        )

    if evidence_strength == "Strong":
        return (
            f"This paper provides relatively strong evidence relevant to {topic}. "
            f"{result_direction} Consider it alongside clinical guidelines, patient "
            "characteristics, treatment risks, and feasibility."
        )

    if evidence_strength == "Moderate":
        return (
            f"This study may inform practice in {topic}, but it should not be treated "
            f"as definitive evidence. {result_direction} Confirm that the study "
            "population and intervention resemble the patients being treated."
        )

    if evidence_strength == "Low":
        return (
            f"This paper offers preliminary information about {topic}. "
            f"{result_direction} It should support clinical reasoning rather than "
            "serve as the sole basis for changing treatment."
        )

    return (
        f"This paper provides very limited evidence for practice in {topic}. "
        "Use it primarily to generate questions or guide further research."
    )


def determine_full_text_need(
    evidence_strength: str,
    practitioner_relevance: int,
    abstract: str,
) -> bool:
    if practitioner_relevance >= 7:
        return True

    if evidence_strength in {"Strong", "Moderate"}:
        return True

    if len(abstract) < 700:
        return True

    return False


# ---------------------------------------------------------------------------
# Individual paper appraisal
# ---------------------------------------------------------------------------

def appraise_paper(paper: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(paper.get("title"))
    abstract = clean_text(paper.get("abstract"))

    study_design = classify_study_design(paper)
    sample_size = extract_sample_size(abstract)

    methodology_score = calculate_methodology_score(
        paper=paper,
        study_design=study_design,
        sample_size=sample_size,
    )

    practitioner_relevance = calculate_practitioner_relevance(
        paper=paper,
        study_design=study_design,
    )

    reporting_completeness = calculate_reporting_completeness(
        paper=paper,
        sample_size=sample_size,
    )

    overall_evidence_score = calculate_overall_evidence_score(
        methodology_score=methodology_score,
        practitioner_relevance=practitioner_relevance,
        reporting_completeness=reporting_completeness,
    )

    evidence_strength = assign_evidence_strength(
        overall_score=overall_evidence_score,
        study_design=study_design,
    )

    risk_of_bias = assign_risk_of_bias(
        methodology_score=methodology_score,
        study_design=study_design,
    )

    limitations = detect_limitations(
        paper=paper,
        study_design=study_design,
        sample_size=sample_size,
    )

    result_direction = detect_result_direction(abstract)

    practice_takeaway = generate_practice_takeaway(
        paper=paper,
        study_design=study_design,
        evidence_strength=evidence_strength,
        result_direction=result_direction,
    )

    appraisal = {
        **paper,
        "formulaic_appraisal": {
            "study_design": study_design,
            "sample_size": sample_size,
            "population": extract_population(abstract),
            "intervention_or_exposure": extract_intervention(abstract),
            "identified_outcomes": extract_outcomes(abstract),
            "result_direction": result_direction,
            "limitations": limitations,
            "risk_of_bias": risk_of_bias,
            "evidence_strength": evidence_strength,
            "scores": {
                "methodology": methodology_score,
                "practitioner_relevance": practitioner_relevance,
                "reporting_completeness": reporting_completeness,
                "overall_evidence": overall_evidence_score,
            },
            "practice_takeaway": practice_takeaway,
            "needs_full_text_review": determine_full_text_need(
                evidence_strength=evidence_strength,
                practitioner_relevance=practitioner_relevance,
                abstract=abstract,
            ),
            "appraisal_method": (
                "Transparent rule-based abstract appraisal; not a formal "
                "validated risk-of-bias instrument."
            ),
            "appraised_at": datetime.now(timezone.utc).isoformat(),
        },
    }

    print(
        f"Appraised: {title[:80]} | "
        f"{study_design} | "
        f"score={overall_evidence_score}/10"
    )

    return appraisal


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------

def load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file does not exist: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list.")

    return [item for item in data if isinstance(item, dict)]


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


def save_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(".json.tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temporary_path.replace(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    papers = load_json_list(INPUT_PATH)

    existing_appraisals: list[dict[str, Any]] = []

    if OUTPUT_PATH.exists():
        existing_appraisals = load_json_list(OUTPUT_PATH)

    existing_by_id = {
        paper_identity(paper): paper
        for paper in existing_appraisals
    }

    updated_appraisals: list[dict[str, Any]] = []

    newly_appraised = 0
    previously_appraised = 0

    for paper in papers:
        identity = paper_identity(paper)

        existing = existing_by_id.get(identity)

        # Reuse an appraisal when the stored abstract has not changed.
        if (
            existing
            and clean_text(existing.get("abstract"))
            == clean_text(paper.get("abstract"))
            and existing.get("formulaic_appraisal")
        ):
            updated_appraisals.append(existing)
            previously_appraised += 1
            continue

        appraised = appraise_paper(paper)
        updated_appraisals.append(appraised)
        newly_appraised += 1

    updated_appraisals.sort(
        key=lambda paper: (
            paper.get("formulaic_appraisal", {})
            .get("scores", {})
            .get("overall_evidence", 0),
            paper.get("formulaic_appraisal", {})
            .get("scores", {})
            .get("practitioner_relevance", 0),
        ),
        reverse=True,
    )

    save_json(OUTPUT_PATH, updated_appraisals)

    print()
    print("=" * 72)
    print(f"Research papers found: {len(papers)}")
    print(f"New or updated appraisals: {newly_appraised}")
    print(f"Existing appraisals reused: {previously_appraised}")
    print(f"Saved to: {OUTPUT_PATH}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Evidence appraiser failed: {error}", file=sys.stderr)
        raise SystemExit(1)
