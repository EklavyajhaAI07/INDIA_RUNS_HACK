"""
Explainer — Generates human-readable reasoning for candidate scores.

This module takes scored candidates with feature evidence and generates
concise, honest reasoning strings that explain why a candidate ranked
where they did.

Key principle: Don't invent reasons. Read from the evidence collected
during scoring.
"""

from typing import List, Optional, Any


class Explainer:
    """
    Generates human-readable reasoning for candidate rankings.

    Usage:
        explainer = Explainer()
        reasoning = explainer.explain(scored_dict)
    """

    def __init__(self, max_length: int = 200):
        self.max_length = max_length

    def explain(self, scored: dict, candidate: Any = None) -> str:
        """
        Generate a reasoning string for a scored candidate.

        Args:
            scored: Dictionary with scoring results
            candidate: Optional Candidate object for additional context

        Returns:
            Reasoning string (≤max_length chars)
        """
        parts = []

        # Start with strongest signal - matched skills
        matched_skills = scored.get("matched_skills", [])
        if matched_skills:
            skill_count = len(matched_skills)
            top_skills = ", ".join(matched_skills[:3])
            if skill_count <= 3:
                parts.append(f"Knows {top_skills}")
            else:
                parts.append(f"Knows {top_skills} +{skill_count-3} more")

        # Experience
        experience_fit = scored.get("experience_fit", {})
        if experience_fit:
            years = experience_fit.get("raw_value")
            score = experience_fit.get("score", 0)
            if years and score >= 0.8:
                parts.append(f"{years}yr experience")
            elif years:
                parts.append(f"{years}yr exp (outside preferred range)")

        # Role fit
        role_fit = scored.get("role_fit", {})
        if role_fit and role_fit.get("score", 0) > 0.5:
            titles = role_fit.get("raw_value", [])
            if titles:
                recent_title = titles[0] if titles else ""
                if recent_title:
                    parts.append(f"Current: {recent_title}")

        # Key strengths
        key_strengths = scored.get("key_strengths", [])
        if key_strengths:
            parts.append(key_strengths[0])

        # Key concerns (if significant)
        key_concerns = scored.get("key_concerns", [])
        must_have_coverage = scored.get("must_have_coverage", {})
        if key_concerns and must_have_coverage.get("score", 1) < 0.3:
            missing_skills = scored.get("missing_skills", [])
            missing_count = len(missing_skills)
            if missing_count > 0:
                parts.append(f"Missing {missing_count} required skills")

        # Combine and truncate
        reasoning = "; ".join(parts)

        # Truncate if too long
        if len(reasoning) > self.max_length:
            reasoning = reasoning[:self.max_length - 3] + "..."

        return reasoning

    def explain_batch(self, scored_candidates: List[dict],
                      candidates: dict = None) -> List[dict]:
        """
        Generate reasoning for a batch of scored candidates.

        Args:
            scored_candidates: List of scored candidate dictionaries
            candidates: Optional dict mapping candidate_id to Candidate object

        Returns:
            Same list with reasoning populated
        """
        for sc in scored_candidates:
            candidate = candidates.get(sc.get("candidate_id")) if candidates else None
            sc["reasoning"] = self.explain(sc, candidate)

        return scored_candidates
