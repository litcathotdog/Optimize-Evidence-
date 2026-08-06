"""
Optimize Evidence Research Librarian

Purpose
-------
Search PubMed for recent, practitioner-relevant research in:
- Orthobiologics and regenerative medicine
- Tendon, ligament, cartilage, and muscle rehabilitation
- Sports medicine and return to sport
- Exercise recovery and performance
- Women's athlete health
- Sleep, stress, and recovery physiology

The script:
1. Searches PubMed using NCBI E-utilities.
2. Downloads PubMed XML records.
3. Extracts useful citation metadata.
4. Excludes irrelevant oncology/transplant stem-cell papers.
5. Applies a second relevance screen using titles and abstracts.
6. Deduplicates articles using PMID and DOI.
7. Saves results to data/papers.json.

Required environment variable:
    NCBI_EMAIL

Optional environment variables:
    NCBI_API_KEY
    DAYS_BACK
    MAX_RESULTS_PER_TOPIC
    MAX_TOTAL_PAPERS
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OUTPUT_PATH = Path("data/papers.json")

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_TOOL_NAME = "optimize_evidence_research_librarian"

NCBI_EMAIL = os.getenv("NCBI_EMAIL", "").strip()
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "").strip()

DAYS_BACK = int(os.getenv("DAYS_BACK", "30"))
MAX_RESULTS_PER_TOPIC = int(os.getenv("MAX_RESULTS_PER_TOPIC", "25"))
MAX_TOTAL_PAPERS = int(os.getenv("MAX_TOTAL_PAPERS", "150"))

REQUEST_TIMEOUT_SECONDS = 30
MAX_REQUEST_RETRIES = 4

# NCBI recommends no more than 3 requests per second without an API key.
REQUEST_DELAY_SECONDS = 0.12 if NCBI_API_KEY else 0.40


# ---------------------------------------------------------------------------
# PubMed topic searches
# ---------------------------------------------------------------------------

TOPIC_QUERIES: dict[str, str] = {
    "Orthobiologics and regenerative medicine": """
        (
            "Platelet-Rich Plasma"[Mesh]
            OR "platelet rich plasma"[Title/Abstract]
            OR PRP[Title/Abstract]
            OR "bone marrow aspirate concentrate"[Title/Abstract]
            OR BMAC[Title/Abstract]
            OR "mesenchymal stromal cell"[Title/Abstract]
            OR "mesenchymal stromal cells"[Title/Abstract]
            OR "mesenchymal stem cell"[Title/Abstract]
            OR "mesenchymal stem cells"[Title/Abstract]
            OR orthobiologic*[Title/Abstract]
            OR exosome*[Title/Abstract]
            OR "extracellular vesicle"[Title/Abstract]
            OR "extracellular vesicles"[Title/Abstract]
        )
        AND
        (
            tendon*[Title/Abstract]
            OR ligament*[Title/Abstract]
            OR cartilage[Title/Abstract]
            OR muscle[Title/Abstract]
            OR musculoskeletal[Title/Abstract]
            OR osteoarthritis[Title/Abstract]
            OR "sports injury"[Title/Abstract]
            OR "sports injuries"[Title/Abstract]
            OR orthopedic*[Title/Abstract]
            OR orthopaedic*[Title/Abstract]
        )
    """,

    "Tendon and ligament rehabilitation": """
        (
            tendinopathy[Title/Abstract]
            OR tendon[Title/Abstract]
            OR tendon rehabilitation[Title/Abstract]
            OR patellar tendon[Title/Abstract]
            OR Achilles tendon[Title/Abstract]
            OR hamstring tendon[Title/Abstract]
            OR ligament rehabilitation[Title/Abstract]
            OR anterior cruciate ligament[Title/Abstract]
            OR ACL[Title/Abstract]
        )
        AND
        (
            rehabilitation[Title/Abstract]
            OR exercise therapy[Title/Abstract]
            OR loading[Title/Abstract]
            OR resistance training[Title/Abstract]
            OR isometric[Title/Abstract]
            OR eccentric[Title/Abstract]
            OR heavy slow resistance[Title/Abstract]
            OR return to sport[Title/Abstract]
        )
    """,

    "Cartilage, osteoarthritis, and joint health": """
        (
            articular cartilage[Title/Abstract]
            OR cartilage injury[Title/Abstract]
            OR osteoarthritis[Title/Abstract]
            OR patellofemoral pain[Title/Abstract]
            OR knee pain[Title/Abstract]
        )
        AND
        (
            athlete*[Title/Abstract]
            OR exercise[Title/Abstract]
            OR rehabilitation[Title/Abstract]
            OR physical therapy[Title/Abstract]
            OR sports medicine[Title/Abstract]
            OR strength training[Title/Abstract]
        )
    """,

    "Muscle injury and recovery": """
        (
            muscle injury[Title/Abstract]
            OR skeletal muscle recovery[Title/Abstract]
            OR muscle damage[Title/Abstract]
            OR hamstring injury[Title/Abstract]
            OR muscle strain[Title/Abstract]
            OR delayed onset muscle soreness[Title/Abstract]
            OR DOMS[Title/Abstract]
        )
        AND
        (
            athlete*[Title/Abstract]
            OR rehabilitation[Title/Abstract]
            OR exercise[Title/Abstract]
            OR recovery[Title/Abstract]
            OR return to sport[Title/Abstract]
        )
    """,

    "Sports performance and recovery": """
        (
            athletic performance[Title/Abstract]
            OR sports performance[Title/Abstract]
            OR sprint performance[Title/Abstract]
            OR speed endurance[Title/Abstract]
            OR neuromuscular performance[Title/Abstract]
            OR training load[Title/Abstract]
            OR overtraining[Title/Abstract]
            OR recovery[Title/Abstract]
        )
        AND
        (
            athlete*[Title/Abstract]
            OR sport*[Title/Abstract]
            OR sprint*[Title/Abstract]
            OR track and field[Title/Abstract]
            OR resistance training[Title/Abstract]
        )
    """,

    "Return to sport and injury prevention": """
        (
            return to sport[Title/Abstract]
            OR return to play[Title/Abstract]
            OR injury prevention[Title/Abstract]
            OR reinjury[Title/Abstract]
            OR rehabilitation outcome[Title/Abstract]
        )
        AND
        (
            athlete*[Title/Abstract]
            OR sports medicine[Title/Abstract]
            OR anterior cruciate ligament[Title/Abstract]
            OR ACL[Title/Abstract]
            OR hamstring[Title/Abstract]
            OR ankle sprain[Title/Abstract]
            OR tendon[Title/Abstract]
        )
    """,

    "Women's athlete health": """
        (
            female athlete[Title/Abstract]
            OR women athletes[Title/Abstract]
            OR female athletes[Title/Abstract]
            OR menstrual cycle[Title/Abstract]
            OR menstrual dysfunction[Title/Abstract]
            OR relative energy deficiency in sport[Title/Abstract]
            OR RED-S[Title/Abstract]
            OR low energy availability[Title/Abstract]
        )
        AND
        (
            performance[Title/Abstract]
            OR recovery[Title/Abstract]
            OR injury[Title/Abstract]
            OR bone health[Title/Abstract]
            OR musculoskeletal[Title/Abstract]
            OR sport*[Title/Abstract]
        )
    """,

    "Sleep, stress, and athlete recovery": """
        (
            sleep[Title/Abstract]
            OR circadian[Title/Abstract]
            OR stress physiology[Title/Abstract]
            OR cortisol[Title/Abstract]
            OR autonomic nervous system[Title/Abstract]
            OR heart rate variability[Title/Abstract]
        )
        AND
        (
            athlete*[Title/Abstract]
            OR athletic performance[Title/Abstract]
            OR sports performance[Title/Abstract]
            OR exercise recovery[Title/Abstract]
            OR training adaptation[Title/Abstract]
        )
    """,
}


# ---------------------------------------------------------------------------
# Relevance screening
# ---------------------------------------------------------------------------

# These terms strongly suggest the paper concerns cancer treatment,
# hematologic transplantation, or unrelated cell biology.
HARD_EXCLUSION_TERMS = {
    "allogeneic hematopoietic stem cell transplantation",
    "autologous hematopoietic stem cell transplantation",
    "hematopoietic stem-cell transplantation",
    "hematopoietic stem cell transplant",
    "hematopoietic stem-cell transplant",
    "bone marrow transplantation",
    "bone marrow transplant",
    "graft-versus-host disease",
    "graft versus host disease",
    "chronic gvhd",
    "acute gvhd",
    "hematologic malignancy",
    "hematological malignancy",
    "leukemia",
    "lymphoma",
    "multiple myeloma",
    "myelodysplastic syndrome",
    "solid tumor",
    "tumour progression",
    "tumor progression",
    "cancer immunotherapy",
    "car-t cell",
    "chimeric antigen receptor",
    "viral reactivation after transplantation",
    "organ transplantation",
    "kidney transplantation",
    "liver transplantation",
    "heart transplantation",
}

# At least one term from this set must appear in the title or abstract.
GENERAL_RELEVANCE_TERMS = {
    "athlete",
    "athletic",
    "sport",
    "sports medicine",
    "exercise",
    "training",
    "performance",
    "recovery",
    "rehabilitation",
    "return to sport",
    "return to play",
    "musculoskeletal",
    "orthopedic",
    "orthopaedic",
    "tendon",
    "tendinopathy",
    "ligament",
    "cartilage",
    "osteoarthritis",
    "joint",
    "muscle",
    "hamstring",
    "patellar",
    "achilles",
    "anterior cruciate ligament",
    "acl",
    "bone health",
    "injury",
    "physical therapy",
    "physiotherapy",
    "platelet-rich plasma",
    "platelet rich plasma",
    "bone marrow aspirate concentrate",
    "orthobiologic",
    "mesenchymal stromal",
    "mesenchymal stem",
    "exosome",
    "extracellular vesicle",
    "sleep",
    "circadian",
    "heart rate variability",
    "cortisol",
    "relative energy deficiency in sport",
    "low energy availability",
    "menstrual",
}

# Regenerative studies need a musculoskeletal context.
REGENERATIVE_TERMS = {
    "platelet-rich plasma",
    "platelet rich plasma",
    "prp",
    "bone marrow aspirate concentrate",
    "bmac",
    "mesenchymal stromal cell",
    "mesenchymal stem cell",
    "exosome",
    "extracellular vesicle",
    "orthobiologic",
}

MUSCULOSKELETAL_CONTEXT_TERMS = {
    "tendon",
    "tendinopathy",
    "ligament",
    "cartilage",
    "osteoarthritis",
    "muscle",
    "musculoskeletal",
    "orthopedic",
    "orthopaedic",
    "joint",
    "knee",
    "hip",
    "shoulder",
    "ankle",
    "elbow",
    "spine",
    "sports injury",
    "athlete",
    "rehabilitation",
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Paper:
    pmid: str
    title: str
    abstract: str
    authors: list[str]
    journal: str
    publication_date: str
    electronic_publication_date: str
    print_publication_date: str
    doi: str
    pubmed_url: str
    topic: str
    study_type: str
    publication_types: list[str]
    relevance_score: int
    retrieved_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "journal": self.journal,
            "publication_date": self.publication_date,
            "electronic_publication_date": self.electronic_publication_date,
            "print_publication_date": self.print_publication_date,
            "doi": self.doi,
            "pubmed_url": self.pubmed_url,
            "topic": self.topic,
            "study_type": self.study_type,
            "publication_types": self.publication_types,
            "relevance_score": self.relevance_score,
            "retrieved_at": self.retrieved_at,
        }


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def clean_text(value: str | None) -> str:
    """Normalize whitespace while preserving readable text."""
    if not value:
        return ""

    value = re.sub(r"\s+", " ", value)
    return value.strip()


def element_text(element: ET.Element | None) -> str:
    """Return all text contained in an XML element."""
    if element is None:
        return ""

    return clean_text("".join(element.itertext()))


def normalize_search_query(query: str) -> str:
    """Remove formatting whitespace from multiline PubMed queries."""
    return clean_text(query)


def contains_term(text: str, term: str) -> bool:
    """
    Match a term in lowercase text.

    For short abbreviations such as PRP, ACL, and BMAC, require word
    boundaries so they are not accidentally matched inside longer words.
    """
    normalized_term = term.lower().strip()

    if len(normalized_term) <= 5 and normalized_term.replace("-", "").isalnum():
        pattern = rf"\b{re.escape(normalized_term)}\b"
        return re.search(pattern, text) is not None

    return normalized_term in text


def contains_any(text: str, terms: Iterable[str]) -> bool:
    return any(contains_term(text, term) for term in terms)


def safe_int(value: str | None, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# NCBI requests
# ---------------------------------------------------------------------------

def ncbi_request(
    endpoint: str,
    parameters: dict[str, str | int],
) -> bytes:
    """Call an NCBI E-utilities endpoint with retries and backoff."""

    request_parameters: dict[str, str | int] = {
        **parameters,
        "tool": NCBI_TOOL_NAME,
        "email": NCBI_EMAIL,
    }

    if NCBI_API_KEY:
        request_parameters["api_key"] = NCBI_API_KEY

    encoded_parameters = urllib.parse.urlencode(request_parameters)
    url = f"{NCBI_BASE_URL}/{endpoint}?{encoded_parameters}"

    headers = {
        "User-Agent": f"{NCBI_TOOL_NAME}/1.0 ({NCBI_EMAIL})",
        "Accept": "application/xml, application/json",
    }

    last_error: Exception | None = None

    for attempt in range(1, MAX_REQUEST_RETRIES + 1):
        try:
            request = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(
                request,
                timeout=REQUEST_TIMEOUT_SECONDS,
            ) as response:
                result = response.read()

            time.sleep(REQUEST_DELAY_SECONDS)
            return result

        except urllib.error.HTTPError as error:
            last_error = error

            # Retry rate-limit and temporary server errors.
            if error.code not in {429, 500, 502, 503, 504}:
                raise

        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error

        wait_seconds = min(2 ** attempt, 20)
        print(
            f"NCBI request failed on attempt {attempt}/"
            f"{MAX_REQUEST_RETRIES}. Retrying in {wait_seconds}s: "
            f"{last_error}"
        )
        time.sleep(wait_seconds)

    raise RuntimeError(
        f"NCBI request failed after {MAX_REQUEST_RETRIES} attempts: "
        f"{last_error}"
    )


def search_pubmed(
    query: str,
    minimum_date: date,
    maximum_date: date,
) -> list[str]:
    """Search PubMed and return matching PMIDs."""

    response_bytes = ncbi_request(
        "esearch.fcgi",
        {
            "db": "pubmed",
            "term": normalize_search_query(query),
            "retmode": "json",
            "retmax": MAX_RESULTS_PER_TOPIC,
            "sort": "pub date",
            "datetype": "edat",
            "mindate": minimum_date.strftime("%Y/%m/%d"),
            "maxdate": maximum_date.strftime("%Y/%m/%d"),
        },
    )

    response = json.loads(response_bytes.decode("utf-8"))
    return response.get("esearchresult", {}).get("idlist", [])


def fetch_pubmed_records(pmids: list[str]) -> ET.Element:
    """Fetch full PubMed XML records for a list of PMIDs."""

    if not pmids:
        return ET.Element("PubmedArticleSet")

    response_bytes = ncbi_request(
        "efetch.fcgi",
        {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        },
    )

    return ET.fromstring(response_bytes)


# ---------------------------------------------------------------------------
# PubMed XML parsing
# ---------------------------------------------------------------------------

def parse_authors(article: ET.Element) -> list[str]:
    authors: list[str] = []

    for author in article.findall(
        "./MedlineCitation/Article/AuthorList/Author"
    ):
        collective_name = element_text(author.find("CollectiveName"))

        if collective_name:
            authors.append(collective_name)
            continue

        first_name = (
            element_text(author.find("ForeName"))
            or element_text(author.find("Initials"))
        )
        last_name = element_text(author.find("LastName"))

        full_name = clean_text(f"{first_name} {last_name}")

        if full_name:
            authors.append(full_name)

    return authors


def parse_abstract(article: ET.Element) -> str:
    sections: list[str] = []

    for abstract_element in article.findall(
        "./MedlineCitation/Article/Abstract/AbstractText"
    ):
        text = element_text(abstract_element)

        if not text:
            continue

        label = clean_text(abstract_element.attrib.get("Label", ""))

        if label:
            sections.append(f"{label}: {text}")
        else:
            sections.append(text)

    return "\n".join(sections)


def parse_article_ids(article: ET.Element) -> dict[str, str]:
    ids: dict[str, str] = {}

    for article_id in article.findall(
        "./PubmedData/ArticleIdList/ArticleId"
    ):
        id_type = article_id.attrib.get("IdType", "").lower()
        value = element_text(article_id)

        if id_type and value:
            ids[id_type] = value

    return ids


def parse_publication_types(article: ET.Element) -> list[str]:
    publication_types: list[str] = []

    for publication_type in article.findall(
        "./MedlineCitation/Article/PublicationTypeList/PublicationType"
    ):
        value = element_text(publication_type)

        if value:
            publication_types.append(value)

    return publication_types


def parse_date_element(element: ET.Element | None) -> str:
    if element is None:
        return ""

    year = element_text(element.find("Year"))
    month = element_text(element.find("Month"))
    day = element_text(element.find("Day"))
    medline_date = element_text(element.find("MedlineDate"))

    if medline_date:
        return medline_date

    return clean_text(" ".join(part for part in (year, month, day) if part))


def parse_electronic_publication_date(article: ET.Element) -> str:
    article_date = article.find(
        "./MedlineCitation/Article/ArticleDate[@DateType='Electronic']"
    )

    return parse_date_element(article_date)


def parse_print_publication_date(article: ET.Element) -> str:
    issue_date = article.find(
        "./MedlineCitation/Article/Journal/JournalIssue/PubDate"
    )

    return parse_date_element(issue_date)


def parse_history_date(article: ET.Element, status: str) -> str:
    history_date = article.find(
        f"./PubmedData/History/PubMedPubDate[@PubStatus='{status}']"
    )
    return parse_date_element(history_date)


def choose_display_publication_date(
    electronic_date: str,
    print_date: str,
    pubmed_date: str,
) -> str:
    """
    Prefer the electronic publication date, then print date, then PubMed date.

    This prevents a future print issue date from hiding an earlier electronic
    publication date when both are available.
    """
    return electronic_date or print_date or pubmed_date


def classify_study_type(
    title: str,
    abstract: str,
    publication_types: list[str],
) -> str:
    """Assign a practical study-type label using metadata and text."""

    combined = (
        f"{title} {abstract} {' '.join(publication_types)}"
    ).lower()

    rules: list[tuple[str, tuple[str, ...]]] = [
        (
            "Systematic review and meta-analysis",
            (
                "systematic review and meta-analysis",
                "systematic review with meta-analysis",
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
                "clinical trial, phase",
            ),
        ),
        (
            "Clinical trial",
            (
                "clinical trial",
                "controlled clinical trial",
            ),
        ),
        (
            "Prospective cohort study",
            (
                "prospective cohort",
                "prospective observational",
            ),
        ),
        (
            "Retrospective cohort study",
            (
                "retrospective cohort",
                "retrospective observational",
            ),
        ),
        (
            "Cohort study",
            (
                "cohort study",
                "cohort studies",
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
                "validation study",
                "diagnostic accuracy",
                "method comparison",
                "reliability study",
            ),
        ),
        (
            "Case series or case report",
            (
                "case reports",
                "case report",
                "case series",
            ),
        ),
        (
            "Consensus or clinical guideline",
            (
                "practice guideline",
                "clinical guideline",
                "consensus statement",
                "position statement",
            ),
        ),
        (
            "Narrative review",
            (
                "review",
            ),
        ),
    ]

    for label, keywords in rules:
        if any(keyword in combined for keyword in keywords):
            return label

    return "Other research article"


def calculate_relevance_score(
    title: str,
    abstract: str,
    topic: str,
) -> int:
    """
    Calculate a transparent relevance score.

    Higher scores indicate stronger practical relevance to sports,
    musculoskeletal health, rehabilitation, or performance.
    """
    title_lower = title.lower()
    text_lower = f"{title} {abstract}".lower()

    score = 0

    high_value_terms = {
        "athlete",
        "sports medicine",
        "return to sport",
        "rehabilitation",
        "tendinopathy",
        "tendon",
        "ligament",
        "cartilage",
        "musculoskeletal",
        "platelet-rich plasma",
        "platelet rich plasma",
        "bone marrow aspirate concentrate",
        "orthobiologic",
        "low energy availability",
        "relative energy deficiency in sport",
    }

    moderate_value_terms = {
        "exercise",
        "training",
        "performance",
        "recovery",
        "injury",
        "muscle",
        "joint",
        "sleep",
        "cortisol",
        "heart rate variability",
    }

    for term in high_value_terms:
        if contains_term(title_lower, term):
            score += 3
        elif contains_term(text_lower, term):
            score += 2

    for term in moderate_value_terms:
        if contains_term(title_lower, term):
            score += 2
        elif contains_term(text_lower, term):
            score += 1

    if topic == "Orthobiologics and regenerative medicine":
        has_regenerative_term = contains_any(
            text_lower,
            REGENERATIVE_TERMS,
        )
        has_musculoskeletal_context = contains_any(
            text_lower,
            MUSCULOSKELETAL_CONTEXT_TERMS,
        )

        if has_regenerative_term and has_musculoskeletal_context:
            score += 5

    return score


def is_relevant_paper(
    title: str,
    abstract: str,
    topic: str,
) -> tuple[bool, str]:
    """Return whether a paper should be kept and an explanatory reason."""

    text = clean_text(f"{title} {abstract}").lower()

    if not title:
        return False, "missing title"

    if not abstract:
        return False, "missing abstract"

    for excluded_term in HARD_EXCLUSION_TERMS:
        if contains_term(text, excluded_term):
            return False, f"excluded term: {excluded_term}"

    if not contains_any(text, GENERAL_RELEVANCE_TERMS):
        return False, "no sports, performance, or musculoskeletal context"

    if topic == "Orthobiologics and regenerative medicine":
        if not contains_any(text, REGENERATIVE_TERMS):
            return False, "no regenerative intervention"

        if not contains_any(text, MUSCULOSKELETAL_CONTEXT_TERMS):
            return False, "regenerative study lacks musculoskeletal context"

    score = calculate_relevance_score(title, abstract, topic)

    if score < 2:
        return False, f"relevance score too low: {score}"

    return True, f"relevance score: {score}"


def parse_pubmed_article(
    article: ET.Element,
    topic: str,
) -> Paper | None:
    pmid = element_text(article.find("./MedlineCitation/PMID"))

    title = element_text(
        article.find("./MedlineCitation/Article/ArticleTitle")
    )

    abstract = parse_abstract(article)

    relevant, reason = is_relevant_paper(
        title=title,
        abstract=abstract,
        topic=topic,
    )

    if not relevant:
        print(
            f"  Skipping PMID {pmid or 'unknown'}: {reason} — "
            f"{title[:100]}"
        )
        return None

    article_ids = parse_article_ids(article)
    doi = article_ids.get("doi", "")

    journal = element_text(
        article.find("./MedlineCitation/Article/Journal/Title")
    )

    electronic_date = parse_electronic_publication_date(article)
    print_date = parse_print_publication_date(article)
    pubmed_date = (
        parse_history_date(article, "pubmed")
        or parse_history_date(article, "entrez")
    )

    publication_date = choose_display_publication_date(
        electronic_date=electronic_date,
        print_date=print_date,
        pubmed_date=pubmed_date,
    )

    publication_types = parse_publication_types(article)

    study_type = classify_study_type(
        title=title,
        abstract=abstract,
        publication_types=publication_types,
    )

    relevance_score = calculate_relevance_score(
        title=title,
        abstract=abstract,
        topic=topic,
    )

    return Paper(
        pmid=pmid,
        title=title,
        abstract=abstract,
        authors=parse_authors(article),
        journal=journal,
        publication_date=publication_date,
        electronic_publication_date=electronic_date,
        print_publication_date=print_date,
        doi=doi,
        pubmed_url=(
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid
            else ""
        ),
        topic=topic,
        study_type=study_type,
        publication_types=publication_types,
        relevance_score=relevance_score,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Existing database handling and deduplication
# ---------------------------------------------------------------------------

def load_existing_papers() -> list[dict[str, Any]]:
    if not OUTPUT_PATH.exists():
        return []

    try:
        with OUTPUT_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("papers.json must contain a JSON list.")

        return [
            paper
            for paper in data
            if isinstance(paper, dict)
        ]

    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"Warning: could not read {OUTPUT_PATH}: {error}")
        print("Starting with an empty database.")
        return []


def normalized_doi(value: Any) -> str:
    doi = clean_text(str(value or "")).lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    return doi


def deduplicate_papers(
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deduplicate by PMID first, DOI second, and normalized title third.

    If the same paper appears in multiple searches, retain one copy and
    combine its topic labels.
    """

    records_by_key: dict[str, dict[str, Any]] = {}

    for paper in papers:
        pmid = clean_text(str(paper.get("pmid", "")))
        doi = normalized_doi(paper.get("doi"))
        title = clean_text(str(paper.get("title", "")))

        normalized_title = re.sub(
            r"[^a-z0-9]+",
            "",
            title.lower(),
        )

        if pmid:
            key = f"pmid:{pmid}"
        elif doi:
            key = f"doi:{doi}"
        else:
            key = f"title:{normalized_title}"

        if key not in records_by_key:
            records_by_key[key] = paper
            continue

        existing = records_by_key[key]

        existing_topics = existing.get("topics")
        if not isinstance(existing_topics, list):
            existing_topics = [
                topic
                for topic in [existing.get("topic")]
                if topic
            ]

        new_topics = paper.get("topics")
        if not isinstance(new_topics, list):
            new_topics = [
                topic
                for topic in [paper.get("topic")]
                if topic
            ]

        combined_topics = sorted(
            set(existing_topics + new_topics)
        )

        existing["topics"] = combined_topics

        if combined_topics:
            existing["topic"] = combined_topics[0]

        existing_score = safe_int(existing.get("relevance_score"))
        new_score = safe_int(paper.get("relevance_score"))

        if new_score > existing_score:
            existing["relevance_score"] = new_score

        # Fill missing fields with values from the duplicate record.
        for field, value in paper.items():
            if not existing.get(field) and value:
                existing[field] = value

    return list(records_by_key.values())


def rescreen_existing_papers(
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove older database entries that no longer pass the filters."""

    screened: list[dict[str, Any]] = []

    for paper in papers:
        title = clean_text(str(paper.get("title", "")))
        abstract = clean_text(str(paper.get("abstract", "")))
        topic = clean_text(
            str(
                paper.get(
                    "topic",
                    "Sports performance and recovery",
                )
            )
        )

        relevant, reason = is_relevant_paper(
            title=title,
            abstract=abstract,
            topic=topic,
        )

        if not relevant:
            print(
                "Removing previously saved paper: "
                f"{reason} — {title[:100]}"
            )
            continue

        paper["relevance_score"] = calculate_relevance_score(
            title=title,
            abstract=abstract,
            topic=topic,
        )

        screened.append(paper)

    return screened


def publication_sort_key(paper: dict[str, Any]) -> tuple[str, int, str]:
    """
    Sort by retrieval date, relevance score, and PMID.

    ISO retrieval timestamps sort correctly as strings.
    """
    return (
        str(paper.get("retrieved_at", "")),
        safe_int(paper.get("relevance_score")),
        str(paper.get("pmid", "")),
    )


def save_papers(papers: list[dict[str, Any]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    papers = sorted(
        papers,
        key=publication_sort_key,
        reverse=True,
    )

    papers = papers[:MAX_TOTAL_PAPERS]

    temporary_path = OUTPUT_PATH.with_suffix(".json.tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            papers,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temporary_path.replace(OUTPUT_PATH)


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def validate_configuration() -> None:
    if not NCBI_EMAIL:
        raise RuntimeError(
            "NCBI_EMAIL is missing. Add NCBI_EMAIL as a GitHub "
            "Actions repository secret and expose it in the workflow."
        )

    if DAYS_BACK < 1:
        raise ValueError("DAYS_BACK must be at least 1.")

    if MAX_RESULTS_PER_TOPIC < 1:
        raise ValueError("MAX_RESULTS_PER_TOPIC must be at least 1.")

    if MAX_TOTAL_PAPERS < 1:
        raise ValueError("MAX_TOTAL_PAPERS must be at least 1.")


def main() -> int:
    validate_configuration()

    today = datetime.now(timezone.utc).date()
    minimum_date = today - timedelta(days=DAYS_BACK)

    print("=" * 72)
    print("Optimize Evidence Research Librarian")
    print("=" * 72)
    print(f"Search window: {minimum_date} through {today}")
    print(f"Topics: {len(TOPIC_QUERIES)}")
    print(f"Maximum results per topic: {MAX_RESULTS_PER_TOPIC}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    existing_papers = load_existing_papers()

    print(f"Loaded {len(existing_papers)} previously saved papers.")

    existing_papers = rescreen_existing_papers(existing_papers)

    print(
        f"{len(existing_papers)} previously saved papers remain "
        "after relevance screening."
    )
    print()

    fetched_papers: list[dict[str, Any]] = []

    for topic, query in TOPIC_QUERIES.items():
        print(f"Searching: {topic}")

        try:
            pmids = search_pubmed(
                query=query,
                minimum_date=minimum_date,
                maximum_date=today,
            )

            print(f"  PubMed returned {len(pmids)} PMIDs.")

            if not pmids:
                print()
                continue

            root = fetch_pubmed_records(pmids)

            kept_for_topic = 0

            for article in root.findall("./PubmedArticle"):
                parsed_paper = parse_pubmed_article(
                    article=article,
                    topic=topic,
                )

                if parsed_paper is None:
                    continue

                paper_dict = parsed_paper.to_dict()
                paper_dict["topics"] = [topic]

                fetched_papers.append(paper_dict)
                kept_for_topic += 1

            print(
                f"  Kept {kept_for_topic} relevant papers "
                f"for {topic}."
            )

        except Exception as error:
            # Continue processing other topics if one PubMed query fails.
            print(f"  ERROR while processing {topic}: {error}")

        print()

    combined_papers = existing_papers + fetched_papers
    final_papers = deduplicate_papers(combined_papers)

    save_papers(final_papers)

    print("=" * 72)
    print(f"New relevant records collected: {len(fetched_papers)}")
    print(f"Final unique database size: {len(final_papers)}")
    print(f"Saved research library to {OUTPUT_PATH}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nResearch refresh cancelled.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        print(f"\nFatal error: {error}", file=sys.stderr)
        raise SystemExit(1)
