"""
Data Ingestion — Loads and preprocesses candidates from JSONL.

This module reads the candidates.jsonl file and creates structured
Candidate objects that downstream modules can use for retrieval and scoring.

Think of it as: "Read all 100,000 resumes and organize them."
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CareerEntry:
    """A single job in a candidate's career history."""
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: Optional[str] = None
    duration_months: int = 0
    is_current: bool = False
    industry: str = ""
    company_size: str = ""
    description: str = ""


@dataclass
class Education:
    """A single education entry."""
    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_year: int = 0
    end_year: int = 0
    grade: str = ""
    tier: str = ""


@dataclass
class Skill:
    """A single skill with proficiency."""
    name: str = ""
    proficiency: str = ""  # beginner, intermediate, advanced, expert
    endorsements: int = 0
    duration_months: int = 0


@dataclass
class RedrobSignals:
    """Platform engagement signals from Redrob."""
    profile_completion: float = 0.0
    response_rate: float = 0.0
    platform_activity: str = ""
    endorsements_received: int = 0


@dataclass
class Candidate:
    """
    Structured representation of a single candidate.

    This is the core data object that all downstream modules work with.
    """
    candidate_id: str = ""
    name: str = ""
    headline: str = ""
    summary: str = ""
    location: str = ""
    country: str = ""
    years_of_experience: float = 0.0
    current_title: str = ""
    current_company: str = ""
    current_company_size: str = ""
    current_industry: str = ""

    career_history: List[CareerEntry] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    redrob_signals: RedrobSignals = field(default_factory=RedrobSignals)

    # Preprocessed text for search (populated during loading)
    search_text: str = ""
    skill_names: List[str] = field(default_factory=list)
    all_titles: List[str] = field(default_factory=list)
    all_industries: List[str] = field(default_factory=list)
    all_companies: List[str] = field(default_factory=list)
    total_relevant_months: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def parse_career_history(raw_career: List[Dict[str, Any]]) -> List[CareerEntry]:
    """Parse raw career history into CareerEntry objects."""
    entries = []
    for item in raw_career:
        entries.append(CareerEntry(
            company=item.get("company", ""),
            title=item.get("title", ""),
            start_date=item.get("start_date", ""),
            end_date=item.get("end_date"),
            duration_months=item.get("duration_months", 0),
            is_current=item.get("is_current", False),
            industry=item.get("industry", ""),
            company_size=item.get("company_size", ""),
            description=item.get("description", ""),
        ))
    return entries


def parse_education(raw_education: List[Dict[str, Any]]) -> List[Education]:
    """Parse raw education into Education objects."""
    entries = []
    for item in raw_education:
        entries.append(Education(
            institution=item.get("institution", ""),
            degree=item.get("degree", ""),
            field_of_study=item.get("field_of_study", ""),
            start_year=item.get("start_year", 0),
            end_year=item.get("end_year", 0),
            grade=item.get("grade", ""),
            tier=item.get("tier", ""),
        ))
    return entries


def parse_skills(raw_skills: List[Dict[str, Any]]) -> List[Skill]:
    """Parse raw skills into Skill objects."""
    entries = []
    for item in raw_skills:
        entries.append(Skill(
            name=item.get("name", ""),
            proficiency=item.get("proficiency", ""),
            endorsements=item.get("endorsements", 0),
            duration_months=item.get("duration_months", 0),
        ))
    return entries


def parse_redrob_signals(raw_signals: Dict[str, Any]) -> RedrobSignals:
    """Parse raw Redrob signals."""
    if not raw_signals:
        return RedrobSignals()
    return RedrobSignals(
        profile_completion=raw_signals.get("profile_completion", 0.0),
        response_rate=raw_signals.get("response_rate", 0.0),
        platform_activity=raw_signals.get("platform_activity", ""),
        endorsements_received=raw_signals.get("endorsements_received", 0),
    )


def build_search_text(candidate: Candidate) -> str:
    """
    Build a single text string from all candidate info for search.

    This combines summary, skills, career descriptions, and education
    into one searchable text blob.
    """
    parts = []

    # Name and headline
    if candidate.name:
        parts.append(candidate.name)
    if candidate.headline:
        parts.append(candidate.headline)

    # Summary
    if candidate.summary:
        parts.append(candidate.summary)

    # Current role
    if candidate.current_title:
        parts.append(f"Current role: {candidate.current_title}")
    if candidate.current_company:
        parts.append(f"Company: {candidate.current_company}")
    if candidate.current_industry:
        parts.append(f"Industry: {candidate.current_industry}")

    # Skills
    for skill in candidate.skills:
        parts.append(skill.name)
        if skill.proficiency:
            parts.append(f"{skill.proficiency} in {skill.name}")

    # Career history
    for entry in candidate.career_history:
        if entry.title:
            parts.append(entry.title)
        if entry.company:
            parts.append(entry.company)
        if entry.industry:
            parts.append(entry.industry)
        if entry.description:
            parts.append(entry.description)

    # Education
    for edu in candidate.education:
        if edu.degree:
            parts.append(f"{edu.degree} in {edu.field_of_study}")
        if edu.institution:
            parts.append(edu.institution)

    # Location
    if candidate.location:
        parts.append(f"Location: {candidate.location}")
    if candidate.country:
        parts.append(f"Country: {candidate.country}")

    return " ".join(parts)


def extract_metadata(candidate: Candidate) -> None:
    """Extract searchable metadata from candidate (populates fields)."""
    # Skill names (lowercase for matching)
    candidate.skill_names = [s.name.lower() for s in candidate.skills]

    # All job titles
    candidate.all_titles = [e.title for e in candidate.career_history if e.title]
    if candidate.current_title:
        candidate.all_titles.append(candidate.current_title)

    # All industries
    candidate.all_industries = list(set(
        [e.industry for e in candidate.career_history if e.industry] +
        ([candidate.current_industry] if candidate.current_industry else [])
    ))

    # All companies
    candidate.all_companies = list(set(
        [e.company for e in candidate.career_history if e.company] +
        ([candidate.current_company] if candidate.current_company else [])
    ))

    # Total months in career
    candidate.total_relevant_months = sum(
        e.duration_months for e in candidate.career_history
    )


def load_candidates(jsonl_path: str, limit: Optional[int] = None) -> List[Candidate]:
    """
    Main entry point: Load candidates from JSONL file.

    Args:
        jsonl_path: Path to candidates.jsonl
        limit: Optional limit on number of candidates to load (for testing)

    Returns:
        List of Candidate objects
    """
    candidates = []
    path = Path(jsonl_path)

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break

            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            # Parse profile
            profile = data.get("profile", {})

            # Parse career history
            career_raw = data.get("career_history", [])
            career = parse_career_history(career_raw)

            # Parse education
            edu_raw = data.get("education", [])
            education = parse_education(edu_raw)

            # Parse skills
            skills_raw = data.get("skills", [])
            skills = parse_skills(skills_raw)

            # Parse Redrob signals
            signals_raw = data.get("redrob_signals", {})
            signals = parse_redrob_signals(signals_raw)

            # Create Candidate object
            candidate = Candidate(
                candidate_id=data.get("candidate_id", ""),
                name=profile.get("anonymized_name", ""),
                headline=profile.get("headline", ""),
                summary=profile.get("summary", ""),
                location=profile.get("location", ""),
                country=profile.get("country", ""),
                years_of_experience=profile.get("years_of_experience", 0.0),
                current_title=profile.get("current_title", ""),
                current_company=profile.get("current_company", ""),
                current_company_size=profile.get("current_company_size", ""),
                current_industry=profile.get("current_industry", ""),
                career_history=career,
                education=education,
                skills=skills,
                redrob_signals=signals,
            )

            # Extract metadata
            extract_metadata(candidate)

            # Build search text
            candidate.search_text = build_search_text(candidate)

            candidates.append(candidate)

    return candidates


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python loader.py <candidates.jsonl> [limit]")
        sys.exit(1)

    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    candidates = load_candidates(sys.argv[1], limit=limit)

    print(f"Loaded {len(candidates)} candidates")
    if candidates:
        c = candidates[0]
        print(f"\nSample candidate: {c.candidate_id}")
        print(f"  Name: {c.name}")
        print(f"  Title: {c.current_title}")
        print(f"  Skills: {c.skill_names[:5]}...")
        print(f"  Search text length: {len(c.search_text)} chars")
