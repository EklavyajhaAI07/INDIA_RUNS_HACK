"""
Candidate Scorer — Weighted scoring engine with 7 features.

This module takes candidates from retrieval and scores them using
the 7-factor scoring formula:

FinalScore = 0.35(SemanticFit) + 0.20(MustHaveCoverage) + 0.15(ExperienceFit)
           + 0.10(RoleFit) + 0.10(Recency) + 0.05(BehavioralSignals) + 0.05(BonusFit)

Each feature is decomposed into evidence for explainability.
"""

import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


# Scoring weights
WEIGHTS = {
    "semantic_fit": 0.35,
    "must_have_coverage": 0.20,
    "experience_fit": 0.15,
    "role_fit": 0.10,
    "recency": 0.10,
    "behavioral_fit": 0.05,
    "bonus_fit": 0.05,
}


@dataclass
class FeatureEvidence:
    """Evidence for a single scoring feature."""
    feature_name: str
    score: float  # 0-1
    evidence: List[str] = field(default_factory=list)
    raw_value: Any = None


@dataclass
class ScoredCandidate:
    """A candidate with their final score and feature breakdown."""
    candidate_id: str
    final_score: float
    rank: int = 0
    reasoning: str = ""

    # Feature scores and evidence
    semantic_fit: FeatureEvidence = None
    must_have_coverage: FeatureEvidence = None
    experience_fit: FeatureEvidence = None
    role_fit: FeatureEvidence = None
    recency: FeatureEvidence = None
    behavioral_fit: FeatureEvidence = None
    bonus_fit: FeatureEvidence = None

    # Summary evidence for reasoning
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    key_strengths: List[str] = field(default_factory=list)
    key_concerns: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "final_score": self.final_score,
            "rank": self.rank,
            "reasoning": self.reasoning,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "key_strengths": self.key_strengths,
            "key_concerns": self.key_concerns,
        }


class CandidateScorer:
    """
    Scores candidates against job requirements using 7 weighted features.

    Usage:
        scorer = CandidateScorer()
        scored = scorer.score_candidates(candidates, jd_requirements)

        # With adaptive weights from feedback:
        scorer = CandidateScorer(weights=adapted_weights)
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or WEIGHTS

    def _compute_semantic_fit(self, candidate, jd_requirements) -> FeatureEvidence:
        """
        Compute semantic fit between candidate profile and JD.

        This uses pre-computed retrieval scores if available,
        or falls back to text similarity heuristics.
        """
        evidence = []

        # Use retrieval score if available (from hybrid search)
        if hasattr(candidate, '_retrieval_score'):
            score = candidate._retrieval_score
            evidence.append(f"Retrieval similarity: {score:.3f}")
            return FeatureEvidence("semantic_fit", score, evidence, score)

        # Fallback: heuristic based on skills and summary overlap
        jd_skills = set(s.lower() for s in jd_requirements.must_have_skills)
        candidate_skills = set(s.lower() for s in candidate.skill_names)

        overlap = jd_skills & candidate_skills
        if jd_skills:
            skill_overlap = len(overlap) / len(jd_skills)
        else:
            skill_overlap = 0.0

        # Summary keyword match
        jd_keywords = set(jd_requirements.full_text.lower().split())
        candidate_words = set(candidate.summary.lower().split())
        keyword_overlap = len(jd_keywords & candidate_words) / max(len(jd_keywords), 1)

        score = 0.6 * skill_overlap + 0.4 * keyword_overlap
        evidence.append(f"Skill overlap: {len(overlap)}/{len(jd_skills)} required skills")
        if overlap:
            evidence.append(f"Matched: {', '.join(list(overlap)[:5])}")

        return FeatureEvidence("semantic_fit", min(score, 1.0), evidence, skill_overlap)

    def _compute_must_have_coverage(self, candidate, jd_requirements) -> FeatureEvidence:
        """Compute coverage of must-have skills."""
        evidence = []
        must_haves = [s.lower() for s in jd_requirements.must_have_skills]
        candidate_skills = set(s.lower() for s in candidate.skill_names)

        # Also check career descriptions for skill mentions
        career_text = " ".join(e.description.lower() for e in candidate.career_history)
        summary_text = candidate.summary.lower()
        all_text = career_text + " " + summary_text

        matched = []
        missing = []

        for skill in must_haves:
            # Check in skills list or text
            if skill in candidate_skills or skill in all_text:
                matched.append(skill)
            else:
                missing.append(skill)

        if must_haves:
            score = len(matched) / len(must_haves)
        else:
            score = 1.0

        evidence.append(f"Matched {len(matched)}/{len(must_haves)} must-have skills")
        if matched:
            evidence.append(f"Found: {', '.join(matched[:5])}")
        if missing:
            evidence.append(f"Missing: {', '.join(missing[:3])}")

        return FeatureEvidence("must_have_coverage", score, evidence,
                              {"matched": matched, "missing": missing})

    def _compute_experience_fit(self, candidate, jd_requirements) -> FeatureEvidence:
        """Compute fit based on years of experience."""
        evidence = []
        years = candidate.years_of_experience
        min_years = jd_requirements.min_years
        max_years = jd_requirements.max_years

        if min_years <= years <= max_years:
            # Perfect fit
            score = 1.0
            evidence.append(f"{years} years is within {min_years}-{max_years} range")
        elif years < min_years:
            # Under-experienced
            ratio = years / min_years if min_years > 0 else 0
            score = max(0.3, ratio)  # Minimum 0.3 if they have some experience
            evidence.append(f"{years} years is below minimum {min_years}")
        else:
            # Over-experienced (small penalty)
            over_ratio = (years - max_years) / max_years if max_years > 0 else 0
            score = max(0.5, 1.0 - over_ratio * 0.2)  # Gentle penalty
            evidence.append(f"{years} years exceeds preferred {max_years}")

        return FeatureEvidence("experience_fit", score, evidence, years)

    def _compute_role_fit(self, candidate, jd_requirements) -> FeatureEvidence:
        """Compute fit based on job title similarity."""
        evidence = []
        role_title = jd_requirements.role_title.lower()

        # Key title keywords to match
        role_keywords = set(re.findall(r'\b\w+\b', role_title))
        # Remove common words
        stop_words = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        role_keywords -= stop_words

        # Check candidate's titles
        all_titles = [t.lower() for t in candidate.all_titles]
        title_text = " ".join(all_titles)

        # Count matching keywords
        matches = [kw for kw in role_keywords if kw in title_text]
        if role_keywords:
            score = len(matches) / len(role_keywords)
        else:
            score = 0.5

        # Bonus for "engineer" or "senior" in title
        if any("engineer" in t for t in all_titles):
            score = min(1.0, score + 0.2)
            evidence.append("Has 'Engineer' in title")
        if any("senior" in t or "sr" in t for t in all_titles):
            score = min(1.0, score + 0.1)
            evidence.append("Has 'Senior' level title")

        evidence.append(f"Title match: {len(matches)}/{len(role_keywords)} keywords")
        if matches:
            evidence.append(f"Matched: {', '.join(matches[:5])}")

        return FeatureEvidence("role_fit", min(score, 1.0), evidence, all_titles)

    def _compute_recency(self, candidate, jd_requirements) -> FeatureEvidence:
        """Compute recency of relevant experience."""
        evidence = []

        # Check if current role is relevant
        current_title = candidate.current_title.lower()
        relevant_keywords = ["ai", "ml", "engineer", "data", "backend", "full stack"]
        is_current_relevant = any(kw in current_title for kw in relevant_keywords)

        # Check career history for recent roles
        recent_roles = []
        for entry in candidate.career_history:
            if entry.is_current:
                recent_roles.append(entry)
            elif entry.start_date:
                # Parse date and check if recent (within 2 years)
                try:
                    start = datetime.strptime(entry.start_date, "%Y-%m-%d")
                    if (datetime.now() - start).days < 730:  # 2 years
                        recent_roles.append(entry)
                except:
                    pass

        if is_current_relevant:
            score = 1.0
            evidence.append("Current role is relevant")
        elif recent_roles:
            score = 0.7
            evidence.append(f"{len(recent_roles)} recent relevant roles")
        else:
            score = 0.4
            evidence.append("No recent relevant roles found")

        return FeatureEvidence("recency", score, evidence, len(recent_roles))

    def _compute_behavioral_fit(self, candidate, jd_requirements) -> FeatureEvidence:
        """Compute fit based on behavioral/cultural signals."""
        evidence = []
        signals = jd_requirements.behavioral_signals

        if not signals:
            return FeatureEvidence("behavioral_fit", 0.5, ["No behavioral signals in JD"], None)

        # Check Redrob signals
        signals_found = []

        if candidate.redrob_signals.profile_completion > 0.7:
            signals_found.append("high_profile_completion")
            evidence.append(f"Profile completion: {candidate.redrob_signals.profile_completion:.0%}")

        if candidate.redrob_signals.response_rate > 0.5:
            signals_found.append("responsive")
            evidence.append(f"Response rate: {candidate.redrob_signals.response_rate:.0%}")

        if candidate.redrob_signals.endorsements_received > 5:
            signals_found.append("endorsed")
            evidence.append(f"Endorsements: {candidate.redrob_signals.endorsements_received}")

        # Check career history for product company experience
        product_companies = ["product", "saas", "platform"]
        service_companies = ["consulting", "services", "outsourcing"]
        is_product = any(any(pc in e.description.lower() for pc in product_companies)
                        for e in candidate.career_history)
        is_services = any(any(sc in e.company.lower() for sc in service_companies)
                         for e in candidate.career_history)

        if is_product:
            signals_found.append("product_company")
            evidence.append("Product company experience")
        if is_services and not is_product:
            evidence.append("Primarily services/consulting background")

        # Score based on signals found
        if signals:
            score = len(signals_found) / len(signals) if signals else 0.5
        else:
            score = 0.5

        return FeatureEvidence("behavioral_fit", min(score, 1.0), evidence, signals_found)

    def _compute_bonus_fit(self, candidate, jd_requirements) -> FeatureEvidence:
        """Compute bonus points for nice-to-have skills."""
        evidence = []
        nice_haves = [s.lower() for s in jd_requirements.nice_to_have_skills]

        if not nice_haves:
            return FeatureEvidence("bonus_fit", 0.5, ["No nice-to-have skills in JD"], None)

        candidate_skills = set(s.lower() for s in candidate.skill_names)
        career_text = " ".join(e.description.lower() for e in candidate.career_history)
        all_text = career_text + " " + candidate.summary.lower()

        matched = []
        for skill in nice_haves:
            if skill in candidate_skills or skill in all_text:
                matched.append(skill)

        if nice_haves:
            score = len(matched) / len(nice_haves)
        else:
            score = 0.5

        evidence.append(f"Matched {len(matched)}/{len(nice_haves)} nice-to-have skills")
        if matched:
            evidence.append(f"Found: {', '.join(matched[:5])}")

        return FeatureEvidence("bonus_fit", min(score, 1.0), evidence, matched)

    def score_candidate(self, candidate, jd_requirements) -> ScoredCandidate:
        """Score a single candidate against JD requirements."""
        # Compute all features
        semantic = self._compute_semantic_fit(candidate, jd_requirements)
        must_have = self._compute_must_have_coverage(candidate, jd_requirements)
        experience = self._compute_experience_fit(candidate, jd_requirements)
        role = self._compute_role_fit(candidate, jd_requirements)
        recency = self._compute_recency(candidate, jd_requirements)
        behavioral = self._compute_behavioral_fit(candidate, jd_requirements)
        bonus = self._compute_bonus_fit(candidate, jd_requirements)

        # Compute weighted final score
        final_score = (
            self.weights["semantic_fit"] * semantic.score +
            self.weights["must_have_coverage"] * must_have.score +
            self.weights["experience_fit"] * experience.score +
            self.weights["role_fit"] * role.score +
            self.weights["recency"] * recency.score +
            self.weights["behavioral_fit"] * behavioral.score +
            self.weights["bonus_fit"] * bonus.score
        )

        # Normalize to 0-1 range
        final_score = max(0.0, min(1.0, final_score))

        # Collect matched/missing skills
        must_have_data = must_have.raw_value if isinstance(must_have.raw_value, dict) else {}
        matched_skills = must_have_data.get("matched", [])
        missing_skills = must_have_data.get("missing", [])

        # Key strengths and concerns
        key_strengths = []
        key_concerns = []

        if semantic.score > 0.7:
            key_strengths.append("Strong semantic match")
        if must_have.score > 0.5:
            key_strengths.append(f"Knows {len(matched_skills)} required skills")
        if experience.score >= 0.9:
            key_strengths.append("Experience level is ideal")
        if role.score > 0.6:
            key_strengths.append("Relevant job titles")

        if must_have.score < 0.3:
            key_concerns.append(f"Missing {len(missing_skills)} required skills")
        if experience.score < 0.5:
            key_concerns.append("Experience level mismatch")
        if behavioral.score < 0.3:
            key_concerns.append("Low platform engagement")

        return ScoredCandidate(
            candidate_id=candidate.candidate_id,
            final_score=round(final_score, 6),
            semantic_fit=semantic,
            must_have_coverage=must_have,
            experience_fit=experience,
            role_fit=role,
            recency=recency,
            behavioral_fit=behavioral,
            bonus_fit=bonus,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            key_strengths=key_strengths,
            key_concerns=key_concerns,
        )

    def score_candidates(self, candidates, jd_requirements) -> List[ScoredCandidate]:
        """
        Score and rank all candidates.

        Args:
            candidates: List of Candidate objects (from retrieval)
            jd_requirements: JDRequirements object (from jd_parser)

        Returns:
            List of ScoredCandidate objects, sorted by score (best first)
        """
        scored = []
        for candidate in candidates:
            scored_candidate = self.score_candidate(candidate, jd_requirements)
            scored.append(scored_candidate)

        # Sort by score (descending)
        scored.sort(key=lambda x: x.final_score, reverse=True)

        # Assign ranks
        for i, sc in enumerate(scored, 1):
            sc.rank = i

        return scored
