import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from data_ingestion import load_candidates
from jd_parser import parse_jd_from_file
from retrieval import HybridRetriever
from reranker import CandidateScorer
from explainability import Explainer

# Load candidates
print("Loading candidates...")
candidates = load_candidates(r"..\India_runs_data_and_ai_challenge\candidates.jsonl", limit=100)
print(f"Loaded {len(candidates)} candidates")

# Parse JD
print("\nParsing job description...")
jd = parse_jd_from_file(r"..\India_runs_data_and_ai_challenge\job_description.docx")

# Build retrieval index and search
print("\nBuilding retrieval index...")
retriever = HybridRetriever()
retriever.build_bm25_index(candidates)

results = retriever.bm25_search(
    "embeddings FAISS vector database Python ranking evaluation NDCG machine learning",
    top_k=50
)

# Get candidate objects
candidate_map = {c.candidate_id: c for c in candidates}
top_candidates = []
for cid, score in results:
    if cid in candidate_map:
        c = candidate_map[cid]
        c._retrieval_score = score / 20.0
        top_candidates.append(c)

# Score candidates
print("\nScoring candidates...")
scorer = CandidateScorer()
scored = scorer.score_candidates(top_candidates, jd)

# Convert to dictionaries for explainer
scored_dicts = [sc.to_dict() for sc in scored]

# Add feature scores to dicts
for sc_dict, sc_obj in zip(scored_dicts, scored):
    sc_dict["semantic_fit"] = {"score": sc_obj.semantic_fit.score, "raw_value": sc_obj.semantic_fit.raw_value}
    sc_dict["must_have_coverage"] = {"score": sc_obj.must_have_coverage.score, "raw_value": sc_obj.must_have_coverage.raw_value}
    sc_dict["experience_fit"] = {"score": sc_obj.experience_fit.score, "raw_value": sc_obj.experience_fit.raw_value}
    sc_dict["role_fit"] = {"score": sc_obj.role_fit.score, "raw_value": sc_obj.role_fit.raw_value}
    sc_dict["recency"] = {"score": sc_obj.recency.score, "raw_value": sc_obj.recency.raw_value}
    sc_dict["behavioral_fit"] = {"score": sc_obj.behavioral_fit.score, "raw_value": sc_obj.behavioral_fit.raw_value}
    sc_dict["bonus_fit"] = {"score": sc_obj.bonus_fit.score, "raw_value": sc_obj.bonus_fit.raw_value}

# Generate explanations
print("\nGenerating explanations...")
explainer = Explainer()
scored_dicts = explainer.explain_batch(scored_dicts, candidate_map)

# Show top 10 with reasoning
print(f"\n=== TOP 10 WITH REASONING ===")
for sc in scored_dicts[:10]:
    print(f"\nRank {sc['rank']}: {sc['candidate_id']} (Score: {sc['final_score']:.4f})")
    print(f"  Reasoning: {sc['reasoning']}")
    print(f"  Matched Skills: {sc['matched_skills'][:5]}")
    print(f"  Missing Skills: {sc['missing_skills'][:5]}")
