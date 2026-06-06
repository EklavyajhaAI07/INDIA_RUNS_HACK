"""
Feedback Store — Persists recruiter accept/reject decisions.

Stores feedback entries as JSONL for append-only writes.
Each entry records the candidate, recruiter decision, and feature
values at the time of ranking so weights can be adjusted later.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class FeedbackEntry:
    """A single recruiter feedback record."""
    candidate_id: str
    decision: str  # "accept" or "reject"
    timestamp: str
    final_score: float
    feature_scores: Dict[str, float]
    recruiter_id: str = "default"
    notes: str = ""


class FeedbackStore:
    """
    Append-only JSONL store for recruiter feedback.

    Usage:
        store = FeedbackStore("./feedback_data.jsonl")
        store.record("CAND_001", "accept", feature_scores={...})
        entries = store.load()
    """

    def __init__(self, path: str = "./feedback_data.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def record(self, candidate_id: str, decision: str,
               feature_scores: Dict[str, float],
               final_score: float = 0.0,
               recruiter_id: str = "default",
               notes: str = "") -> FeedbackEntry:
        """Record a recruiter decision."""
        if decision not in ("accept", "reject"):
            raise ValueError(f"Decision must be 'accept' or 'reject', got '{decision}'")

        entry = FeedbackEntry(
            candidate_id=candidate_id,
            decision=decision,
            timestamp=datetime.utcnow().isoformat(),
            final_score=final_score,
            feature_scores=feature_scores,
            recruiter_id=recruiter_id,
            notes=notes,
        )

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

        return entry

    def load(self) -> List[FeedbackEntry]:
        """Load all feedback entries."""
        entries = []
        if not self.path.exists():
            return entries

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        entries.append(FeedbackEntry(**data))
                    except (json.JSONDecodeError, TypeError):
                        continue
        return entries

    def load_recent(self, limit: int = 100) -> List[FeedbackEntry]:
        """Load the most recent N entries."""
        all_entries = self.load()
        return all_entries[-limit:]

    def count(self) -> int:
        """Count total feedback entries."""
        if not self.path.exists():
            return 0
        with open(self.path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def get_acceptance_rate(self) -> float:
        """Calculate overall acceptance rate."""
        entries = self.load()
        if not entries:
            return 0.0
        accepts = sum(1 for e in entries if e.decision == "accept")
        return accepts / len(entries)

    def clear(self):
    """Clear all feedback data."""
        if self.path.exists():
            self.path.unlink()
        self.path.touch()
