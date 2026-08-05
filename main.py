from __future__ import annotations

import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import requests

try:
    from openai import OpenAI
except ImportError:  # AI analysis is optional during local setup.
    OpenAI = None

ROOT = Path(__file__).resolve().parents[1]
TOPICS_PATH = ROOT / "agent" / "topics.json"
DATA_PATH = ROOT / "data" / "studies.json"
DOCS_DATA_PATH = ROOT / "docs" / "studies.json"
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL = os.getenv("NCBI_EMAIL", "research@example.com")
TOOL = "optimize-evidence-agent"
DAYS_BACK = int(os.getenv("DAYS_BACK", "45"))
MAX_PER_TOPIC = int(os.getenv("MAX_PER_TOPIC", "6"))
PANEL_LIMIT = int(os.getenv("PANEL_LIMIT", "3"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

ROLES = [
    "Research Librarian",
    "Regenerative Medicine Specialist",
    "Sports Performance Scientist",
    "Clinical Evidence Reviewer",
    "Research Director",
]


def request_json(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    params = {**params, "tool": TOOL, "email": EMAIL, "retmode": "json"}
    response = requests.get(f"{BASE}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()
    time.sleep(0.35)
    return response.json()


def search_pubmed(query: str) -> list[str]:
    start = date.today() - timedelta(days=DAYS_BACK)
    dated_query = f'({query}) AND ("{start:%Y/%m/%d}"[Date - Publication] : "3000"[Date - Publication])'
    payload = request_json(
        "esearch.fcgi",
        {"db": "pubmed", "term": dated_query, "sort": "pub date", "retmax": MAX_PER_TOPIC},
    )
    return payload.get("esearchresult", {}).get("idlist", [])


def fetch_records(pmids: list[str]) -> list[dict[str, Any]]:
    if not pmids:
        return []
    response = requests.get(
        f"{BASE}/efetch.fcgi",
        params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml", "tool": TOOL, "email": EMAIL},
        timeout=45,
    )
    response.raise_for_status()
    time.sleep(0.35)
    root = ET.fromstring(response.text)
    return [parse_article(article) for article in root.findall(".//PubmedArticle")]


def text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def parse_article(article: ET.Element) -> dict[str, Any]:
    citation = article.find("MedlineCitation")
    journal_article = citation.find("Article") if citation is not None else None
    pmid = text(citation.find("PMID")) if citation is not None else ""
    title = text(journal_article.find("ArticleTitle")) if journal_article is not None else "Untitled"
    abstract_parts = []
    if journal_article is not None:
        for part in journal_article.findall("Abstract/AbstractText"):
            label = part.attrib.get("Label")
            body = text(part)
            abstract_parts.append(f"{label}: {body}" if label else body)
    abstract = " ".join(abstract_parts)
    journal = text(journal_article.find("Journal/Title")) if journal_article is not None else ""
    pub_date = ""
    if journal_article is not None:
        date_node = journal_article.find("Journal/JournalIssue/PubDate")
        if date_node is not None:
            pub_date = " ".join(filter(None, [text(date_node.find("Year")), text(date_node.find("Month")), text(date_node.find("Day"))]))
            if not pub_date:
                pub_date = text(date_node.find("MedlineDate"))
    publication_types = [text(n) for n in article.findall(".//PublicationType")]
    authors = []
    if journal_article is not None:
        for author in journal_article.findall("AuthorList/Author")[:4]:
            name = " ".join(filter(None, [text(author.find("ForeName")), text(author.find("LastName"))]))
            if name:
                authors.append(name)
    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "publication_date": pub_date,
        "publication_types": publication_types,
        "authors": authors,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
    }


def classify_design(types: list[str], abstract: str) -> tuple[str, str]:
    joined = " ".join(types).lower()
    body = abstract.lower()
    if "meta-analysis" in joined or "systematic review" in joined:
        return "Evidence synthesis", "High"
    if "randomized controlled trial" in joined or "randomised" in body or "randomized" in body:
        return "Randomized trial", "Moderate–high"
    if "clinical trial" in joined:
        return "Clinical trial", "Moderate"
    if "review" in joined:
        return "Review", "Moderate"
    if "case reports" in joined:
        return "Case report", "Low"
    if any(term in body for term in ["mouse", "mice", "rat ", "rats", "in vitro", "cell culture"]):
        return "Preclinical study", "Early-stage"
    return "Observational or other study", "Preliminary"


def fallback_panel(study: dict[str, Any]) -> dict[str, Any]:
    design = study["study_design"]
    preclinical = design == "Preclinical study"
    return {
        "question": f"What, if anything, should a practitioner take from this {design.lower()}?",
        "members": [
            {
                "role": "Research Librarian",
                "stance": "Context",
                "comment": f"This paper was indexed under {', '.join(study.get('categories', []))}. Confirm the full methods, comparator, and outcome definitions before using the abstract as evidence.",
            },
            {
                "role": "Regenerative Medicine Specialist",
                "stance": "Mechanism",
                "comment": "The biological rationale may be relevant, but mechanistic plausibility is not the same as demonstrated tissue regeneration or durable patient benefit.",
            },
            {
                "role": "Sports Performance Scientist",
                "stance": "Performance",
                "comment": "Check whether the outcomes include function, loading tolerance, return to sport, strength, power, or performance—not only pain or biomarkers.",
            },
            {
                "role": "Clinical Evidence Reviewer",
                "stance": "Methods",
                "comment": f"The automated design label is {design}. Evidence confidence is {study['evidence_confidence']}; this must be verified from the full paper, especially sample size, bias, adverse events, and follow-up.",
            },
        ],
        "director": {
            "consensus": "Do not change practice from this record alone." if preclinical else "Potentially discussion-worthy, but applicability depends on full-text appraisal and patient similarity.",
            "disagreement": "The team may agree on relevance while disagreeing about whether the evidence demonstrates regeneration, symptom relief, or performance benefit.",
            "next_question": "What patient population, protocol details, comparator, effect size, and clinically meaningful outcomes were actually reported?",
            "verdict": "Early-stage" if preclinical else "Review full text",
        },
        "generated_by": "rule-based fallback",
    }


def extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def ai_panel(study: dict[str, Any]) -> dict[str, Any]:
    if not os.getenv("OPENAI_API_KEY") or OpenAI is None or not study.get("abstract"):
        return fallback_panel(study)

    client = OpenAI()
    schema_hint = {
        "question": "one clinically useful question",
        "members": [
            {"role": role, "stance": "1-3 words", "comment": "2 concise sentences grounded only in the record"}
            for role in ROLES[:-1]
        ],
        "director": {
            "consensus": "one sentence",
            "disagreement": "one sentence",
            "next_question": "one sentence",
            "verdict": "Practice-relevant | Promising | Preliminary | Early-stage | Low-confidence",
        },
    }
    prompt = f"""
You are producing a cautious, practitioner-facing journal club for regenerative health and sports performance.
Use ONLY the PubMed metadata and abstract below. Do not invent numerical results, sample size, adverse events, protocol details, or conclusions that are absent.
Distinguish symptom improvement from structural regeneration and from performance improvement.
Do not prescribe. Make uncertainty explicit. Return valid JSON only matching this shape:
{json.dumps(schema_hint)}

STUDY RECORD
Title: {study['title']}
Journal: {study['journal']}
Publication date: {study['publication_date']}
Publication types: {', '.join(study['publication_types'])}
Automated design label: {study['study_design']}
Categories: {', '.join(study.get('categories', []))}
Abstract: {study['abstract'][:9000]}
"""
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions="Act as an evidence-disciplined multidisciplinary research team. Output JSON only.",
            input=prompt,
        )
        panel = extract_json(response.output_text)
        panel["generated_by"] = OPENAI_MODEL
        return panel
    except Exception as exc:
        panel = fallback_panel(study)
        panel["ai_error"] = str(exc)
        return panel


def practitioner_takeaway(title: str, abstract: str, design: str) -> str:
    if not abstract:
        return "Abstract unavailable. Review the source before drawing a clinical conclusion."
    lower = abstract.lower()
    if any(term in lower for term in ["mouse", "mice", "rat ", "in vitro"]):
        caution = " This is preclinical evidence and should not be treated as proof of patient benefit."
    elif design == "Randomized trial":
        caution = " Check effect size, comparator, follow-up, adverse events, and patient similarity before applying it."
    else:
        caution = " Treat the finding as decision support rather than a treatment recommendation."
    return f"Potentially relevant because it addresses {title.rstrip('.').lower()}." + caution


def build_feed() -> dict[str, Any]:
    topics = json.loads(TOPICS_PATH.read_text())
    combined: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for topic in topics:
        try:
            records = fetch_records(search_pubmed(topic["query"]))
            for record in records:
                design, confidence = classify_design(record["publication_types"], record["abstract"])
                current = combined.setdefault(record["pmid"], {**record, "categories": []})
                if topic["category"] not in current["categories"]:
                    current["categories"].append(topic["category"])
                current["study_design"] = design
                current["evidence_confidence"] = confidence
                current["clinical_relevance"] = "High" if design not in {"Preclinical study", "Case report"} else "Exploratory"
                current["practitioner_takeaway"] = practitioner_takeaway(record["title"], record["abstract"], design)
        except Exception as exc:
            errors.append(f'{topic["category"]}: {exc}')

    studies = sorted(combined.values(), key=lambda item: item.get("publication_date", ""), reverse=True)
    panel_count = 0
    for study in studies:
        if panel_count < PANEL_LIMIT and study.get("abstract"):
            study["panel"] = ai_panel(study)
            panel_count += 1

    return {
        "generated_on": date.today().isoformat(),
        "days_searched": DAYS_BACK,
        "study_count": len(studies),
        "panel_count": panel_count,
        "team": ROLES,
        "studies": studies,
        "errors": errors,
        "disclaimer": "Literature-monitoring support only; not medical advice or an automated clinical decision system.",
    }


def main() -> None:
    feed = build_feed()
    serialized = json.dumps(feed, indent=2, ensure_ascii=False)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(serialized)
    DOCS_DATA_PATH.write_text(serialized)
    print(f'Wrote {feed["study_count"]} studies and {feed["panel_count"]} panels.')
    if feed["errors"]:
        print("Warnings:", *feed["errors"], sep="\n- ")


if __name__ == "__main__":
    main()
