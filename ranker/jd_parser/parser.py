"""
JD Parser — Extracts structured requirements from a job description.

This module reads a job description (text or .docx) and converts it into
a structured dictionary that downstream retrieval and reranking stages use.

Think of it as: "What does this job ACTUALLY need?"
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class JDRequirements:
    """Structured representation of what a job needs."""

    # Basic info
    role_title: str = ""
    company: str = ""
    location: str = ""
    employment_type: str = ""

    # Experience
    min_years: float = 0.0
    max_years: float = 99.0

    # Skills — the core of matching
    must_have_skills: List[str] = field(default_factory=list)
    nice_to_have_skills: List[str] = field(default_factory=list)
    explicit_do_not_want: List[str] = field(default_factory=list)

    # Domain & seniority
    domain: str = ""
    seniority_level: str = ""

    # Behavioral signals (what kind of person fits)
    behavioral_signals: List[str] = field(default_factory=list)

    # Location constraints
    preferred_locations: List[str] = field(default_factory=list)
    remote_ok: bool = False

    # Hard filters (non-negotiable)
    hard_filters: List[str] = field(default_factory=list)

    # Full text for embedding
    full_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def read_docx(path: str) -> str:
    """Read a .docx file and return its text content."""
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        raise ImportError("python-docx is required to read .docx files. Install with: pip install python-docx")


def read_jd_file(path: str) -> str:
    """Read a JD file (.txt or .docx) and return text content."""
    path = Path(path)
    if path.suffix == ".docx":
        return read_docx(str(path))
    elif path.suffix == ".txt":
        return path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .txt or .docx")


def extract_must_have_skills(text: str) -> List[str]:
    """Extract skills explicitly listed as required/absolute needs."""
    skills = []

    # Common skill patterns in JDs
    skill_keywords = [
        # ML/AI
        "embeddings", "sentence-transformers", "FAISS", "Pinecone", "Weaviate",
        "Qdrant", "Milvus", "OpenSearch", "Elasticsearch", "vector database",
        "vector search", "hybrid search", "retrieval", "ranking", "LLM",
        "fine-tuning", "LoRA", "QLoRA", "PEFT", "NLP", "transformers",
        "machine learning", "deep learning", "neural networks",
        # Programming
        "Python", "SQL", "Java", "Scala", "Go", "Rust",
        # ML frameworks
        "PyTorch", "TensorFlow", "scikit-learn", "XGBoost", "LightGBM",
        # Evaluation
        "NDCG", "MRR", "MAP", "A/B test", "evaluation framework",
        "offline evaluation", "online evaluation",
        # Infrastructure
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "distributed systems",
        "large-scale inference",
        # Data
        "Spark", "Airflow", "Kafka", "data pipeline",
        # Specific to this JD
        "RAG", "retrieval-augmented generation",
    ]

    text_lower = text.lower()

    # Look for "Things you absolutely need" section
    abs_need_match = re.search(
        r"things you absolutely need(.*?)(?=things we'd like|things we explicitly|on location|the vibe)",
        text, re.DOTALL | re.IGNORECASE
    )

    if abs_need_match:
        section = abs_need_match.group(1)
        for skill in skill_keywords:
            if skill.lower() in section.lower():
                skills.append(skill)

    # Also check for explicit "required" mentions
    required_patterns = [
        r"required[:\s]+(.*?)(?:\.|$)",
        r"must have[:\s]+(.*?)(?:\.|$)",
        r"essential[:\s]+(.*?)(?:\.|$)",
    ]

    for pattern in required_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            for skill in skill_keywords:
                if skill.lower() in match.lower() and skill not in skills:
                    skills.append(skill)

    return skills


def extract_nice_to_have_skills(text: str) -> List[str]:
    """Extract skills listed as nice-to-have / bonus."""
    skills = []

    nice_to_have_keywords = [
        "LoRA", "QLoRA", "PEFT", "fine-tuning",
        "learning-to-rank", "XGBoost", "LightGBM",
        "HR-tech", "recruiting tech", "marketplace",
        "distributed systems", "large-scale inference",
        "open-source", "NLP", "information retrieval",
    ]

    # Look for "Things we'd like you to have" section
    nice_match = re.search(
        r"things we'd like you to have(.*?)(?=things we explicitly|on location|the vibe)",
        text, re.DOTALL | re.IGNORECASE
    )

    if nice_match:
        section = nice_match.group(1)
        for skill in nice_to_have_keywords:
            if skill.lower() in section.lower():
                skills.append(skill)

    return skills


def extract_do_not_want(text: str) -> List[str]:
    """Extract explicit disqualifiers from the JD."""
    disqualifiers = []

    # Look for "Things we explicitly do NOT want" section
    not_want_match = re.search(
        r"things we explicitly do not want(.*?)(?=on location|the vibe|final note|$)",
        text, re.DOTALL | re.IGNORECASE
    )

    if not_want_match:
        section = not_want_match.group(1)
        # Extract bullet points or sentences
        lines = [l.strip() for l in section.split("\n") if l.strip()]
        for line in lines:
            if len(line) > 10:  # Skip very short lines
                disqualifiers.append(line)

    return disqualifiers


def extract_experience_range(text: str) -> tuple:
    """Extract min/max years of experience."""
    min_years = 0.0
    max_years = 99.0

    # Pattern: "5-9 years" or "5–9 years"
    match = re.search(r"(\d+)[-–](\d+)\s*years?", text, re.IGNORECASE)
    if match:
        min_years = float(match.group(1))
        max_years = float(match.group(2))
    else:
        # Pattern: "at least X years"
        match = re.search(r"at least (\d+)\s*years?", text, re.IGNORECASE)
        if match:
            min_years = float(match.group(1))

    return min_years, max_years


def extract_location(text: str) -> tuple:
    """Extract location preferences and remote status."""
    locations = []
    remote_ok = False

    # Common Indian cities
    indian_cities = [
        "Pune", "Noida", "Bangalore", "Bengaluru", "Hyderabad",
        "Mumbai", "Delhi", "Gurgaon", "Chennai", "Kolkata"
    ]

    for city in indian_cities:
        if city.lower() in text.lower():
            locations.append(city)

    # Check for remote
    remote_patterns = ["remote", "work from home", "wfh", "distributed"]
    for pattern in remote_patterns:
        if pattern in text.lower():
            remote_ok = True
            break

    return locations, remote_ok


def extract_domain(text: str) -> str:
    """Extract the primary domain/industry."""
    domain_keywords = {
        "AI/ML": ["ai", "machine learning", "artificial intelligence", "ml"],
        "HR-Tech": ["hr-tech", "recruiting", "talent", "hiring"],
        "Fintech": ["fintech", "finance", "banking"],
        "E-commerce": ["e-commerce", "ecommerce", "marketplace"],
        "Healthcare": ["healthcare", "health", "medical"],
    }

    text_lower = text.lower()
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                return domain

    return "Technology"


def extract_seniority(text: str) -> str:
    """Extract seniority level."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["staff", "principal", "distinguished"]):
        return "Staff+"
    elif any(w in text_lower for w in ["senior", "sr."]):
        return "Senior"
    elif any(w in text_lower for w in ["mid-level", "mid level", "intermediate"]):
        return "Mid-Level"
    elif any(w in text_lower for w in ["junior", "jr.", "entry level"]):
        return "Junior"
    return "Senior"  # Default for this JD


def extract_behavioral_signals(text: str) -> List[str]:
    """Extract behavioral/cultural signals from the JD."""
    signals = []

    signal_patterns = [
        (r"ship(?:per|ping|ped)?", "shipper mentality"),
        (r"production.*deploy", "production deployment experience"),
        (r"eval.*framework", "evaluation mindset"),
        (r"async[- ]first", "async-first communicator"),
        (r"write.*a lot", "strong writer"),
        (r"disagree.*openly", "open communicator"),
        (r"move fast", "fast mover"),
        (r"product.*company", "product company background"),
        (r"not.*consulting", "not pure consulting"),
    ]

    for pattern, signal in signal_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            signals.append(signal)

    return signals


def parse_jd(source, is_file: bool = False) -> JDRequirements:
    """
    Main entry point: Parse a job description into structured requirements.

    Args:
        source: Either a file path (str) or raw JD text (str)
        is_file: If True, source is a file path; if False, source is raw text

    Returns:
        JDRequirements object with all extracted fields
    """
    if is_file:
        text = read_jd_file(source)
    else:
        text = source

    # Extract all components
    must_haves = extract_must_have_skills(text)
    nice_to_haves = extract_nice_to_have_skills(text)
    do_not_want = extract_do_not_want(text)
    min_years, max_years = extract_experience_range(text)
    locations, remote_ok = extract_location(text)
    domain = extract_domain(text)
    seniority = extract_seniority(text)
    behavioral = extract_behavioral_signals(text)

    # Extract role title (first line usually)
    first_line = text.split("\n")[0].strip()
    role_title = first_line.replace("Job Description:", "").strip()

    # Extract company
    company_match = re.search(r"Company:\s*(.*?)(?:\n|$)", text)
    company = company_match.group(1).strip() if company_match else ""

    return JDRequirements(
        role_title=role_title,
        company=company,
        location=", ".join(locations) if locations else "",
        employment_type="Full-time",
        min_years=min_years,
        max_years=max_years,
        must_have_skills=must_haves,
        nice_to_have_skills=nice_to_haves,
        explicit_do_not_want=do_not_want,
        domain=domain,
        seniority_level=seniority,
        behavioral_signals=behavioral,
        preferred_locations=locations,
        remote_ok=remote_ok,
        hard_filters=[
            f"Minimum {min_years} years experience",
            f"Location: {', '.join(locations)}" if locations else "",
        ],
        full_text=text,
    )


def parse_jd_from_file(path: str) -> JDRequirements:
    """Convenience function to parse JD from a file."""
    return parse_jd(path, is_file=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <jd_file_path>")
        sys.exit(1)

    jd = parse_jd_from_file(sys.argv[1])
    print(json.dumps(jd.to_dict(), indent=2, default=str))
