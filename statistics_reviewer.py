"""
Optimize Evidence: Formula-Based Statistics Reviewer

Reads:
    data/appraised_papers.json

Writes:
    data/statistically_reviewed_papers.json

This reviewer evaluates statistical reporting from titles and abstracts.
It does not replace full-text statistical review.
"""

from __future__ import annotations

import json
import re
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INPUT_PATH = Path("data/appraised_papers.json")
OUTPUT_PATH = Path("data/statistically_reviewed_papers.json")


# ---------------------------------------------------------------------------
# Statistical terminology
# ---------------------------------------------------------------------------

EFFECT_SIZE_TERMS = {
    "effect size",
    "cohen's d",
    "cohen d",
    "hedges' g",
    "hedges g",
    "standardized mean difference",
    "standardised mean difference",
    "mean difference",
    "risk ratio",
    "relative risk",
    "odds ratio",
    "hazard ratio",
    "rate ratio",
    "correlation coefficient",
    "pearson r",
    "spearman",
    "eta squared",
    "partial eta squared",
    "confidence interval",
}

CONFIDENCE_INTERVAL_TERMS = {
    "confidence interval",
    "95% ci",
    "90% ci",
    "ci:",
    "ci =",
}

P_VALUE_PATTERNS = [
    r"\bp\s*[<=>]\s*0?\.\d+",
    r"\bp\s*[<=>]\s*\.\d+",
    r"\bp-value\s*[<=>]\s*0?\.\d+",
]

MULTIPLE_COMPARISON_TERMS = {
    "bonferroni",
    "holm correction",
    "holm-bonferroni",
    "false discovery rate",
    "fdr correction",
    "multiple comparison correction",
    "adjusted p-value",
    "adjusted p value",
    "tukey",
}

POWER_TERMS = {
    "power analysis",
    "sample size calculation",
    "a priori power",
    "a-priori power",
    "powered to detect",
    "statistical power",
}

MISSING_DATA_TERMS = {
    "multiple imputation",
    "missing data",
    "complete case analysis",
    "last observation carried forward",
    "imputation",
}

MODEL_ADJUSTMENT_TERMS = {
    "adjusted for",
    "multivariable",
    "multivariate",
    "covariate",
    "confounder",
    "regression model",
    "mixed-effects model",
    "mixed effects model",
    "generalized estimating equation",
    "generalised estimating equation",
}

ASSUMPTION_TERMS = {
    "normality",
    "homogeneity of variance",
    "equal variance",
    "sphericity",
    "proportional hazards assumption",
    "model assumptions",
    "residual analysis",
}

CLINICAL_SIGNIFICANCE_TERMS = {
    "clinically meaningful",
    "clinical significance",
    "minimal clinically important difference",
    "minimum clinically important difference",
    "mcid",
    "smallest worthwhile change",
}

PRE_REGISTRATION_TERMS = {
    "preregistered",
    "pre-registered",
    "prospectively registered",
    "trial registration",
    "clinicaltrials.gov",
    "protocol registered",
}

INTENTION_TO_TREAT_TERMS = {
    "intention-to-treat",
    "intention to treat",
    "modified intention-to-treat",
    "modified intention to treat",
}

COMMON_TESTS: dict[str, tuple[str, ...]] = {
    "t test": (
        "t-test",
        "t test",
        "student's t",
        "welch",
    ),
    "ANOVA": (
        "anova",
        "analysis of variance",
    ),
    "ANCOVA": (
        "ancova",
        "analysis of covariance",
    ),
    "Chi-square test": (
        "chi-square",
        "chi square",
        "χ2",
    ),
    "Nonparametric test": (
        "mann-whitney",
        "mann whitney",
        "wilcoxon",
        "kruskal-wallis",
        "kruskal wallis",
        "friedman test",
    ),
    "Linear regression": (
        "linear regression",
        "multiple regression",
    ),
    "Logistic regression": (
        "logistic regression",
    ),
    "Cox regression": (
        "cox regression",
        "cox proportional hazards",
    ),
    "Mixed-effects model": (
        "mixed-effects",
        "mixed effects",
        "multilevel model",
        "hierarchical model",
    ),
    "Correlation": (
        "pearson correlation",
        "spearman correlation",
        "correlation coefficient",
    ),
    "Bland-Altman analysis": (
        "bland-altman",
        "bland altman",
        "limits of agreement",
    ),
    "Intraclass correlation": (
        "intraclass correlation",
        "icc",
    ),
    "Meta-analysis": (
        "meta-analysis",
        "meta analysis",
        "pooled effect",
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


def contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


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
# Extraction
# ---------------------------------------------------------------------------

def extract_sample_size(paper: dict[str, Any]) -> int | None:
    appraisal = paper.get("formulaic_appraisal", {})

    if isinstance(appraisal, dict):
        sample_size = appraisal.get("sample_size")

        if isinstance(sample_size, int):
            return sample_size

    abstract = clean_text(paper.get("abstract"))

    patterns = [
        r"\bn\s*=\s*(\d{1,6})\b",
        r"\b(\d{1,6})\s+participants\b",
        r"\b(\d{1,6})\s+patients\b",
        r"\b(\d{1,6})\s+athletes\b",
        r"\b(\d{1,6})\s+subjects\b",
    ]

    candidates: list[int] = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            abstract,
            flags=re.IGNORECASE,
        ):
            number = int(match.group(1))

            if 2 <= number <= 1_000_000:
                candidates.append(number)

    if not candidates:
        return None

    return max(candidates)


def extract_study_design(paper: dict[str, Any]) -> str:
    appraisal = paper.get("formulaic_appraisal", {})

    if isinstance(appraisal, dict):
        design = clean_text(appraisal.get("study_design"))

        if design:
            return design

    return clean_text(
        paper.get("study_type")
    ) or "Other research article"


def identify_statistical_tests(text: str) -> list[str]:
    tests: list[str] = []

    for test_name, terms in COMMON_TESTS.items():
        if any(term in text for term in terms):
            tests.append(test_name)

    return tests


def extract_reported_effects(text: str) -> list[str]:
    patterns = [
        r"\b(?:OR|RR|HR)\s*[=:]\s*"
        r"-?\d+(?:\.\d+)?"
        r"(?:\s*,?\s*95%\s*CI\s*[:=]?\s*"
        r"-?\d+(?:\.\d+)?\s*[-–to]+\s*"
        r"-?\d+(?:\.\d+)?)?",

        r"\b(?:mean difference|MD|SMD)\s*[=:]\s*"
        r"-?\d+(?:\.\d+)?",

        r"\b(?:r|ρ)\s*[=:]\s*-?0?\.\d+",

        r"\b(?:Cohen'?s?\s*d|Hedges'?s?\s*g)\s*[=:]\s*"
        r"-?\d+(?:\.\d+)?",
    ]

    effects: list[str] = []

    for pattern in patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            value = clean_text(match.group(0))

            if value not in effects:
                effects.append(value)

    return effects[:10]


# ---------------------------------------------------------------------------
# Design-aware checks
# ---------------------------------------------------------------------------

def expected_features_for_design(
    study_design: str,
) -> list[str]:
    design = study_design.lower()

    if "randomized" in design or "randomised" in design:
        return [
            "sample-size or power calculation",
            "effect estimate",
            "confidence interval",
            "intention-to-treat analysis",
            "missing-data or attrition handling",
        ]

    if "cohort" in design or "case-control" in design:
        return [
            "effect estimate",
            "confidence interval",
            "confounder adjustment",
            "missing-data handling",
        ]

    if "cross-sectional" in design:
        return [
            "effect estimate",
            "confidence interval",
            "confounder adjustment",
        ]

    if "meta-analysis" in design:
        return [
            "pooled effect estimate",
            "confidence interval",
            "heterogeneity assessment",
            "publication-bias assessment",
        ]

    if "diagnostic" in design or "validation" in design:
        return [
            "agreement, reliability, or accuracy statistic",
            "confidence interval",
            "prespecified performance metric",
        ]

    return [
        "effect estimate",
        "confidence interval",
        "clear statistical methods",
    ]


def detect_warnings(
    text: str,
    study_design: str,
    sample_size: int | None,
    tests: list[str],
) -> list[str]:
    warnings: list[str] = []

    has_p_value = any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in P_VALUE_PATTERNS
    )

    has_effect_size = contains_any(
        text,
        EFFECT_SIZE_TERMS,
    )

    has_confidence_interval = contains_any(
        text,
        CONFIDENCE_INTERVAL_TERMS,
    )

    if has_p_value and not has_effect_size:
        warnings.append(
            "P-values are reported without a clearly identified effect-size estimate."
        )

    if has_p_value and not has_confidence_interval:
        warnings.append(
            "Statistical significance is reported without a clearly identified confidence interval."
        )

    if not tests:
        warnings.append(
            "The statistical test or model is not clearly identifiable from the abstract."
        )

    if sample_size is None:
        warnings.append(
            "The total analyzed sample size could not be reliably identified."
        )
    elif sample_size < 20:
        warnings.append(
            "The very small sample raises serious concerns about imprecision and unstable estimates."
        )
    elif sample_size < 50:
        warnings.append(
            "The modest sample may provide limited power for small effects or subgroup analyses."
        )

    if (
        "randomized" in study_design.lower()
        or "randomised" in study_design.lower()
    ):
        if not contains_any(text, POWER_TERMS):
            warnings.append(
                "The abstract does not report an a priori power or sample-size calculation."
            )

        if not contains_any(text, INTENTION_TO_TREAT_TERMS):
            warnings.append(
                "The abstract does not identify an intention-to-treat analysis."
            )

    if (
        "cohort" in study_design.lower()
        or "case-control" in study_design.lower()
        or "cross-sectional" in study_design.lower()
    ):
        if not contains_any(text, MODEL_ADJUSTMENT_TERMS):
            warnings.append(
                "The abstract does not clearly describe adjustment for confounding variables."
            )

    if "meta-analysis" in study_design.lower():
        if "heterogeneity" not in text and "i²" not in text and "i2" not in text:
            warnings.append(
                "The abstract does not clearly report statistical heterogeneity."
            )

        if (
            "publication bias" not in text
            and "funnel plot" not in text
            and "egger" not in text
        ):
            warnings.append(
                "The abstract does not clearly report an assessment of publication bias."
            )

    if (
        "multiple outcomes" in text
        or "multiple comparisons" in text
        or "subgroup analyses" in text
    ):
        if not contains_any(text, MULTIPLE_COMPARISON_TERMS):
            warnings.append(
                "Multiple testing may have occurred without a clearly reported correction."
            )

    if not contains_any(text, CLINICAL_SIGNIFICANCE_TERMS):
        warnings.append(
            "Clinical importance or a minimally important difference is not clearly discussed."
        )

    return warnings[:10]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def calculate_reporting_score(
    text: str,
    sample_size: int | None,
    tests: list[str],
) -> int:
    score = 0

    if sample_size is not None:
        score += 1

    if tests:
        score += 1

    if any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in P_VALUE_PATTERNS
    ):
        score += 1

    if contains_any(text, EFFECT_SIZE_TERMS):
        score += 2

    if contains_any(text, CONFIDENCE_INTERVAL_TERMS):
        score += 2

    if contains_any(text, POWER_TERMS):
        score += 1

    if contains_any(text, MISSING_DATA_TERMS):
        score += 1

    if contains_any(text, PRE_REGISTRATION_TERMS):
        score += 1

    return clamp(score, 1, 10)


def calculate_precision_score(
    text: str,
    sample_size: int | None,
) -> int:
    score = 3

    if sample_size is None:
        score -= 1
    elif sample_size >= 1000:
        score += 4
    elif sample_size >= 300:
        score += 3
    elif sample_size >= 100:
        score += 2
    elif sample_size >= 50:
        score += 1
    elif sample_size < 20:
        score -= 2

    if contains_any(text, CONFIDENCE_INTERVAL_TERMS):
        score += 2

    if "wide confidence interval" in text:
        score -= 2

    return clamp(score, 1, 10)


def calculate_analysis_rigor_score(
    text: str,
    study_design: str,
    tests: list[str],
) -> int:
    score = 3

    if tests:
        score += 1

    if contains_any(text, MODEL_ADJUSTMENT_TERMS):
        score += 2

    if contains_any(text, ASSUMPTION_TERMS):
        score += 1

    if contains_any(text, MULTIPLE_COMPARISON_TERMS):
        score += 1

    if contains_any(text, MISSING_DATA_TERMS):
        score += 1

    if contains_any(text, PRE_REGISTRATION_TERMS):
        score += 1

    if (
        "randomized" in study_design.lower()
        or "randomised" in study_design.lower()
    ) and contains_any(text, INTENTION_TO_TREAT_TERMS):
        score += 1

    return clamp(score, 1, 10)


def calculate_interpretation_score(text: str) -> int:
    score = 2

    if contains_any(text, EFFECT_SIZE_TERMS):
        score += 3

    if contains_any(text, CONFIDENCE_INTERVAL_TERMS):
        score += 2

    if contains_any(text, CLINICAL_SIGNIFICANCE_TERMS):
        score += 2

    if (
        "causes" in text
        and (
            "observational" in text
            or "cross-sectional" in text
        )
    ):
        score -= 2

    return clamp(score, 1, 10)


def calculate_overall_score(
    reporting_score: int,
    precision_score: int,
    rigor_score: int,
    interpretation_score: int,
) -> int:
    weighted = (
        reporting_score * 0.30
        + precision_score * 0.20
        + rigor_score * 0.30
        + interpretation_score * 0.20
    )

    return clamp(round(weighted), 1, 10)


def assign_statistical_confidence(
    overall_score: int,
) -> str:
    if overall_score >= 9:
        return "High"
    if overall_score >= 7:
        return "Moderate"
    if overall_score >= 5:
        return "Low"

    return "Very low"


# ---------------------------------------------------------------------------
# Review generation
# ---------------------------------------------------------------------------

def generate_summary(
    tests: list[str],
    sample_size: int | None,
    confidence: str,
    warnings: list[str],
) -> str:
    test_text = (
        ", ".join(tests)
        if tests
        else "no clearly identifiable statistical procedure"
    )

    sample_text = (
        str(sample_size)
        if sample_size is not None
        else "an unconfirmed sample size"
    )

    return (
        f"The abstract describes {test_text} with {sample_text}. "
        f"Statistical confidence from abstract-level reporting is "
        f"{confidence.lower()}. "
        f"{len(warnings)} reporting or interpretation concern(s) were flagged."
    )


def review_paper(
    paper: dict[str, Any],
) -> dict[str, Any]:
    title = clean_text(paper.get("title"))
    abstract = clean_text(paper.get("abstract"))
    study_design = extract_study_design(paper)

    text = normalized_text(
        title,
        abstract,
        study_design,
    )

    sample_size = extract_sample_size(paper)
    statistical_tests = identify_statistical_tests(text)
    reported_effects = extract_reported_effects(
        clean_text(f"{title} {abstract}")
    )

    warnings = detect_warnings(
        text=text,
        study_design=study_design,
        sample_size=sample_size,
        tests=statistical_tests,
    )

    reporting_score = calculate_reporting_score(
        text=text,
        sample_size=sample_size,
        tests=statistical_tests,
    )

    precision_score = calculate_precision_score(
        text=text,
        sample_size=sample_size,
    )

    rigor_score = calculate_analysis_rigor_score(
        text=text,
        study_design=study_design,
        tests=statistical_tests,
    )

    interpretation_score = calculate_interpretation_score(
        text=text,
    )

    overall_score = calculate_overall_score(
        reporting_score=reporting_score,
        precision_score=precision_score,
        rigor_score=rigor_score,
        interpretation_score=interpretation_score,
    )

    statistical_confidence = assign_statistical_confidence(
        overall_score
    )

    review = {
        "study_design": study_design,
        "sample_size": sample_size,
        "identified_statistical_tests": statistical_tests,
        "reported_effect_estimates": reported_effects,
        "expected_reporting_features": (
            expected_features_for_design(study_design)
        ),
        "reporting_flags": warnings,
        "scores": {
            "statistical_reporting": reporting_score,
            "precision_and_power": precision_score,
            "analysis_rigor": rigor_score,
            "interpretation_quality": interpretation_score,
            "overall_statistics": overall_score,
        },
        "statistical_confidence": statistical_confidence,
        "review_summary": generate_summary(
            tests=statistical_tests,
            sample_size=sample_size,
            confidence=statistical_confidence,
            warnings=warnings,
        ),
        "requires_full_text_statistical_review": (
            overall_score < 8
            or len(warnings) >= 2
            or not reported_effects
        ),
        "review_method": (
            "Transparent rule-based statistical review of title and "
            "abstract only; not a substitute for review of the full "
            "methods, results, protocol, or statistical analysis plan."
        ),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
    }

    print(
        f"Reviewed statistics: {title[:75]} | "
        f"{statistical_confidence} | "
        f"{overall_score}/10"
    )

    return {
        **paper,
        "statistics_review": review,
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> int:
    papers = load_json_list(INPUT_PATH)

    existing_reviews: list[dict[str, Any]] = []

    if OUTPUT_PATH.exists():
        existing_reviews = load_json_list(OUTPUT_PATH)

    existing_by_id = {
        paper_identity(paper): paper
        for paper in existing_reviews
    }

    reviewed_papers: list[dict[str, Any]] = []

    new_reviews = 0
    reused_reviews = 0

    for paper in papers:
        identity = paper_identity(paper)
        existing = existing_by_id.get(identity)

        if (
            existing
            and clean_text(existing.get("abstract"))
            == clean_text(paper.get("abstract"))
            and existing.get("statistics_review")
        ):
            reviewed_papers.append(existing)
            reused_reviews += 1
            continue

        reviewed_papers.append(
            review_paper(paper)
        )
        new_reviews += 1

    reviewed_papers.sort(
        key=lambda paper: (
            paper.get("statistics_review", {})
            .get("scores", {})
            .get("overall_statistics", 0),
            paper.get("formulaic_appraisal", {})
            .get("scores", {})
            .get("overall_evidence", 0),
        ),
        reverse=True,
    )

    save_json(
        OUTPUT_PATH,
        reviewed_papers,
    )

    print()
    print("=" * 72)
    print(f"Papers received: {len(papers)}")
    print(f"New statistical reviews: {new_reviews}")
    print(f"Existing reviews reused: {reused_reviews}")
    print(f"Saved to: {OUTPUT_PATH}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(
            f"Statistics reviewer failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
