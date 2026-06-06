"""
Weight Adapter — Adjusts scoring weights from recruiter feedback.

Uses exponential moving average (EMA) to update weights based on
accepted/rejected candidate feature vectors. Accepted candidates
pull weights toward their feature profiles; rejected candidates
push weights away.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from .store import FeedbackStore, FeedbackEntry


DEFAULT_WEIGHTS = {
    "semantic_fit": 0.35,
    "must_have_coverage": 0.20,
    "experience_fit": 0.15,
    "role_fit": 0.10,
    "recency": 0.10,
    "behavioral_fit": 0.05,
    "bonus_fit": 0.05,
}

FEATURE_NAMES = list(DEFAULT_WEIGHTS.keys())


@dataclass
class AdaptedWeights:
    """Result of weight adaptation."""
    weights: Dict[str, float]
    feedback_count: int
    acceptance_rate: float
    adjustment_magnitude: float
    adapted: bool


class WeightAdapter:
    """
    Adjusts scoring weights based on recruiter feedback.

    Uses exponential moving average:
        new_weight = old_weight + alpha * (target - old_weight)

    Where target is the normalized feature vector of accepted candidates.
    Rejected candidates contribute negatively (push weights away).

    Usage:
        adapter = WeightAdapter()
        adapted = adapter.adapt()
        print(adapted.weights)  # Updated weights
    """

    def __init__(self, feedback_store: Optional[FeedbackStore] = None,
                 weights_path: str = "./adaptive_weights.json",
                 learning_rate: float = 0.05,
                 min_feedback: int = 10):
        """
        Args:
            feedback_store: FeedbackStore instance for reading feedback
            weights_path: Path to persist adapted weights
            learning_rate: EMA alpha (0.01 = slow, 0.1 = fast)
            min_feedback: Minimum feedback entries before adapting
        """
        self.store = feedback_store or FeedbackStore()
        self.weights_path = Path(weights_path)
        self.learning_rate = learning_rate
        self.min_feedback = min_feedback
        self._current_weights = self._load_weights()

    def _load_weights(self) -> Dict[str, float]:
        """Load adapted weights from disk or use defaults."""
        if self.weights_path.exists():
            try:
                with open(self.weights_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if all(k in data for k in FEATURE_NAMES):
                        return data
            except (json.JSONDecodeError, KeyError):
                pass
        return DEFAULT_WEIGHTS.copy()

    def _save_weights(self, weights: Dict[str, float]):
        """Persist weights to disk."""
        with open(self.weights_path, "w", encoding="utf-8") as f:
            json.dump(weights, f, indent=2)

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights sum to 1.0 and are non-negative."""
        total = sum(max(0.0, v) for v in weights.values())
        if total <= 0:
            return DEFAULT_WEIGHTS.copy()
        return {k: max(0.0, v) / total for k, v in weights.items()}

    def _compute_target_vector(self, entries: List[FeedbackEntry]) -> Dict[str, float]:
        """
        Compute the target feature vector from feedback.

        For accepted candidates: their feature scores are the target.
        For rejected candidates: their feature scores are inverted (push away).
        """
        if not entries:
            return {k: 1.0 / len(FEATURE_NAMES) for k in FEATURE_NAMES}

        weighted_sums = {k: 0.0 for k in FEATURE_NAMES}
        total_weight = 0.0

        for entry in entries:
            if entry.decision == "accept":
                sign = 1.0
                weight = 1.0 + entry.final_score  # Higher-scoring accepts are stronger signals
            else:
                sign = -1.0
                weight = 1.0 + (1.0 - entry.final_score)  # Lower-scoring rejects are stronger signals

            for feature in FEATURE_NAMES:
                value = entry.feature_scores.get(feature, 0.5)
                weighted_sums[feature] += sign * value * weight

            total_weight += weight

        if total_weight <= 0:
            return {k: 1.0 / len(FEATURE_NAMES) for k in FEATURE_NAMES}

        # Normalize to [0, 1] range
        target = {}
        for feature in FEATURE_NAMES:
            raw = weighted_sums[feature] / total_weight
            target[feature] = max(0.01, min(0.99, (raw + 1.0) / 2.0))

        return target

    def adapt(self, use_recruiter_id: Optional[str] = None) -> AdaptedWeights:
        """
        Run weight adaptation based on all feedback.

        Args:
            use_recruiter_id: If set, only use feedback from this recruiter

        Returns:
            AdaptedWeights with updated weights and metadata
        """
        entries = self.store.load()
        if use_recruiter_id:
            entries = [e for e in entries if e.recruiter_id == use_recruiter_id]

        feedback_count = len(entries)
        if feedback_count < self.min_feedback:
            return AdaptedWeights(
                weights=self._current_weights.copy(),
                feedback_count=feedback_count,
                acceptance_rate=self.store.get_acceptance_rate(),
                adjustment_magnitude=0.0,
                adapted=False,
            )

        # Compute target feature vector
        target = self._compute_target_vector(entries)

        # Apply EMA update
        old_weights = self._current_weights.copy()
        new_weights = {}
        for feature in FEATURE_NAMES:
            old_val = old_weights.get(feature, 0.1)
            target_val = target.get(feature, 0.1)
            new_val = old_val + self.learning_rate * (target_val - old_val)
            new_weights[feature] = new_val

        # Normalize
        new_weights = self._normalize_weights(new_weights)

        # Compute adjustment magnitude
        magnitude = sum(abs(new_weights[k] - old_weights[k]) for k in FEATURE_NAMES)

        # Save
        self._current_weights = new_weights
        self._save_weights(new_weights)

        return AdaptedWeights(
            weights=new_weights,
            feedback_count=feedback_count,
            acceptance_rate=self.store.get_acceptance_rate(),
            adjustment_magnitude=magnitude,
            adapted=True,
        )

    def get_weights(self) -> Dict[str, float]:
        """Get current weights (load from disk if needed)."""
        return self._load_weights()

    def reset(self):
        """Reset weights to defaults."""
        self._current_weights = DEFAULT_WEIGHTS.copy()
        self._save_weights(self._current_weights)

    def get_weight_history(self) -> List[Dict]:
        """Get weight evolution from feedback history."""
        entries = self.store.load()
        history = []
        temp_weights = DEFAULT_WEIGHTS.copy()

        for i, entry in enumerate(entries):
            for feature in FEATURE_NAMES:
                val = entry.feature_scores.get(feature, 0.5)
                if entry.decision == "accept":
                    temp_weights[feature] += self.learning_rate * (val - temp_weights[feature])
                else:
                    temp_weights[feature] -= self.learning_rate * (val - temp_weights[feature])

            # Normalize
            total = sum(temp_weights.values())
            normalized = {k: v / total for k, v in temp_weights.items()}

            history.append({
                "entry_index": i,
                "candidate_id": entry.candidate_id,
                "decision": entry.decision,
                "weights_after": normalized.copy(),
            })

        return history
