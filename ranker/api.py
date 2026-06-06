from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
import json

from feedback import FeedbackStore, WeightAdapter


app = FastAPI(title="India Runs Ranker API")

# Initialize feedback store
feedback_store = FeedbackStore("./feedback_data.jsonl")
weight_adapter = WeightAdapter(feedback_store)


class FeedbackRequest(BaseModel):
    candidate_id: str
    decision: str  # "accept" or "reject"
    final_score: float = 0.0
    feature_scores: Dict[str, float] = {}
    recruiter_id: str = "default"
    notes: str = ""


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_count: int
    acceptance_rate: float


class WeightResponse(BaseModel):
    weights: Dict[str, float]
    feedback_count: int
    acceptance_rate: float
    adapted: bool


class FeedbackEntryResponse(BaseModel):
    candidate_id: str
    decision: str
    timestamp: str
    final_score: float
    feature_scores: Dict[str, float]
    recruiter_id: str
    notes: str


@app.get("/")
def root():
    return {"status": "ok", "service": "ranker"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(req: FeedbackRequest):
    """Submit recruiter feedback for a candidate."""
    if req.decision not in ("accept", "reject"):
        raise HTTPException(status_code=400, detail="Decision must be 'accept' or 'reject'")

    try:
        feedback_store.record(
            candidate_id=req.candidate_id,
            decision=req.decision,
            feature_scores=req.feature_scores,
            final_score=req.final_score,
            recruiter_id=req.recruiter_id,
            notes=req.notes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FeedbackResponse(
        success=True,
        message=f"Recorded '{req.decision}' for {req.candidate_id}",
        feedback_count=feedback_store.count(),
        acceptance_rate=feedback_store.get_acceptance_rate(),
    )


@app.get("/feedback", response_model=List[FeedbackEntryResponse])
def get_feedback(limit: int = 100):
    """Retrieve recent feedback entries."""
    entries = feedback_store.load_recent(limit=limit)
    return [
        FeedbackEntryResponse(
            candidate_id=e.candidate_id,
            decision=e.decision,
            timestamp=e.timestamp,
            final_score=e.final_score,
            feature_scores=e.feature_scores,
            recruiter_id=e.recruiter_id,
            notes=e.notes,
        )
        for e in entries
    ]


@app.get("/feedback/stats")
def get_feedback_stats():
    """Get feedback statistics."""
    entries = feedback_store.load()
    accepts = sum(1 for e in entries if e.decision == "accept")
    rejects = sum(1 for e in entries if e.decision == "reject")
    return {
        "total": len(entries),
        "accepts": accepts,
        "rejects": rejects,
        "acceptance_rate": feedback_store.get_acceptance_rate(),
    }


@app.get("/weights", response_model=WeightResponse)
def get_weights():
    """Get current adaptive weights."""
    adapted = weight_adapter.adapt()
    return WeightResponse(
        weights=adapted.weights,
        feedback_count=adapted.feedback_count,
        acceptance_rate=adapted.acceptance_rate,
        adapted=adapted.adapted,
    )


@app.post("/weights/reset")
def reset_weights():
    """Reset weights to defaults."""
    weight_adapter.reset()
    return {"status": "ok", "message": "Weights reset to defaults"}
