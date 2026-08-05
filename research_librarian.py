import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests


EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

SEARCH_QUERY = """
(
    "platelet-rich plasma"[Title/Abstract]
    OR PRP[Title/Abstract]
    OR orthobiologic*[Title/Abstract]
    OR "regenerative medicine"[Title/Abstract]
    OR "stem cell*"[Title/Abstract]
    OR exosome*[Title/Abstract]
    OR "extracellular vesicle*"[Title/Abstract]
    OR "tissue regeneration"[Title/Abstract]
)
AND
(
    athlete*[Title/Abstract]
    OR sport*[Title/Abstract]
    OR tendon*[Title/Abstract]
    OR ligament*[Title/Abstract]
    OR cartilage[Title/Abstract]
    OR muscle[Title/Abstract]
    OR recovery[Title/Abstract]
    OR performance[Title/Abstract]
    OR wellbeing[Title/Abstract]
    OR "well-being"[Title/Abstract]
)
""".strip()

OUTPUT_PATH = Path("data/papers.json")
MAX_RESULTS = 20


def get_ncbi_email() -> str:
    email = os.getenv("NCBI_EMAIL", "").strip()

    if not email:
        raise RuntimeError(
            "NCBI_EMAIL is missing. Add it as a GitHub Actions repository secret."
        )

    return email


def search_pubmed(email: str) -> list[str]:
    """Search PubMed and return a list of PubMed IDs."""

    response = requests.get(
        f"{EUTILS_BASE_URL}/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": SEARCH_QUERY,
            "retmode": "json",
            "retmax": MAX_RESULTS,
            "sort": "pub date",
            "datetype": "pdat",
            "reldate": 30,
            "tool": "optimize-evidence",
            "email": email,
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    return payload.get("esearchresult", {}).get("idlist", [])


def fetch_pubmed_records(pubmed_ids: list[str], email: str) -> str:
    """Retrieve PubMed records as XML."""

    if not pubmed_ids:
        return ""

    response = requests.get(
        f"{EUTILS_BASE_URL}/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(pubmed_ids),
            "retmode": "xml",
            "tool": "optimize-evidence",
            "email": email,
        },
        timeout=60,
    )
    response.raise_for_status()

    return response.text


def get_text(element: ET.Element | None) -> str:
    if element is None:
        return ""

    return "".join(element.itertext()).strip()


def get_publication_date(article: ET.Element) -> str:
    date_element = article.find(".//PubDate")

    if date_element is None:
        return ""

    year = get_text(date_element.find("Year"))
    month = get_text(date_element.find("Month"))
    day = get_text(date_element.find("Day"))
    medline_date = get_text(date_element.find("MedlineDate"))

    if medline_date:
        return medline_date

    return " ".join(part for part in [year, month, day] if part)


def get_authors(article: ET.Element) -> list[str]:
    authors = []

    for author in article.findall(".//Author"):
        collective_name = get_text(author.find("CollectiveName"))

        if collective_name:
            authors.append(collective_name)
            continue

        first_name = get_text(author.find("ForeName"))
        last_name = get_text(author.find("LastName"))
        full_name = " ".join(part for part in [first_name, last_name] if part)

        if full_name:
            authors.append(full_name)

    return authors


def classify_topic(title: str, abstract: str) -> str:
    combined_text = f"{title} {abstract}".lower()

    topic_rules = {
        "PRP and orthobiologics": [
            "platelet-rich plasma",
            "platelet rich plasma",
            "orthobiologic",
            "prp",
        ],
        "Tendon and ligament": [
            "tendon",
            "tendinopathy",
            "ligament",
        ],
        "Cartilage and joints": [
            "cartilage",
            "osteoarthritis",
            "joint",
        ],
        "Muscle recovery": [
            "muscle",
            "myofiber",
            "muscular",
        ],
        "Stem cells and exosomes": [
            "stem cell",
            "exosome",
            "extracellular vesicle",
        ],
        "Performance and recovery": [
            "athlete",
            "performance",
            "recovery",
            "sport",
        ],
    }

    for topic, keywords in topic_rules.items():
        if any(keyword in combined_text for keyword in keywords):
            return topic

    return "Regenerative medicine"


def classify_study_type(title: str, abstract: str) -> str:
    combined_text = f"{title} {abstract}".lower()

    rules = [
        ("Systematic review or meta-analysis", ["systematic review", "meta-analysis"]),
        (
            "Randomized controlled trial",
            ["randomized controlled trial", "randomised controlled trial"],
        ),
        ("Clinical trial", ["clinical trial"]),
        ("Cohort study", ["cohort study", "prospective cohort", "retrospective cohort"]),
        ("Case report or case series", ["case report", "case series"]),
        ("Preclinical study", ["mouse", "mice", "rat ", "animal model", "in vitro"]),
    ]

    for study_type, keywords in rules:
        if any(keyword in combined_text for keyword in keywords):
            return study_type

    return "Unclassified study"


def parse_pubmed_xml(xml_text: str) -> list[dict]:
    if not xml_text:
        return []

    root = ET.fromstring(xml_text)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        pmid = get_text(article.find(".//PMID"))
        title = get_text(article.find(".//ArticleTitle"))

        abstract_sections = article.findall(".//Abstract/AbstractText")
        abstract = "\n".join(
            get_text(section) for section in abstract_sections if get_text(section)
        )

        journal = get_text(article.find(".//Journal/Title"))
        doi = ""

        for article_id in article.findall(".//ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi = get_text(article_id)
                break

        paper = {
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "authors": get_authors(article),
            "journal": journal,
            "publication_date": get_publication_date(article),
            "doi": doi,
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "topic": classify_topic(title, abstract),
            "study_type": classify_study_type(title, abstract),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

        papers.append(paper)

    return papers


def load_existing_papers() -> list[dict]:
    if not OUTPUT_PATH.exists():
        return []

    try:
        with OUTPUT_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, list):
            return payload

    except (json.JSONDecodeError, OSError):
        pass

    return []


def merge_papers(existing: list[dict], new: list[dict]) -> list[dict]:
    papers_by_pmid = {
        paper["pmid"]: paper
        for paper in existing
        if paper.get("pmid")
    }

    for paper in new:
        papers_by_pmid[paper["pmid"]] = paper

    return list(papers_by_pmid.values())


def save_papers(papers: list[dict]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(papers, file, indent=2, ensure_ascii=False)


def main() -> None:
    email = get_ncbi_email()

    print("Research Librarian is searching PubMed...")
    pubmed_ids = search_pubmed(email)

    print(f"Found {len(pubmed_ids)} PubMed records.")

    time.sleep(0.4)

    xml_text = fetch_pubmed_records(pubmed_ids, email)
    new_papers = parse_pubmed_xml(xml_text)

    existing_papers = load_existing_papers()
    all_papers = merge_papers(existing_papers, new_papers)

    save_papers(all_papers)

    print(f"Saved {len(all_papers)} total papers to {OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
