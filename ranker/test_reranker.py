import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from data_ingestion import load_candidates
from jd_parser import parse_jd_from_file
from retrieval import HybridRetriever
from reranker import CandidateScorer

# Load candidates
print("Loading candidates...")
candidates = load_candidates(r"..\India_runs_data_and_ai_challenge\candidates.jsonl", limit=100)
print(f"Loaded {len(candidates)} candidates")

# Parse JD
print("\nParsing job description...")
jd = parse_jd_from_file(r"..\India_runs_data_and_ai_challenge\job_description.docx")
print(f"Role: {jd.role_title}")
print(f"Must-have skills: {jd.must_have_skills[:5]}...")

# Build retrieval index and search
print("\nBuilding retrieval index...")
retriever = HybridRetriever()
retriever.build_bm25_index(candidates)

# Get top 50 candidates via BM25
results = retriever.bm25_search(
    "embeddings FAISS vector database Python ranking evaluation NDCG machine learning",
    top_k=50
)

# Get candidate objects for top results
candidate_map = {c.candidate_id: c for c in candidates}
top_candidates = []
for cid, score in results:
    if cid in candidate_map:
        c = candidate_map[cid]
        c._retrieval_score = score / 20.0  # Normalize to ~0-1
        top_candidates.append(c)

# Score candidates
print("\nScoring candidates...")
scorer = CandidateScorer()
scored = scorer.score_candidates(top_candidates, jd)

# Show top 10
print(f"\n=== TOP 10 SCORED CANDIDATES ===")
for sc in scored[:10]:
    print(f"\nRank {sc.rank}: {sc.candidate_id}")
    print(f"  Final Score: {sc.final_score:.4f}")
    print(f"  Semantic Fit: {sc.semantic_fit.score:.3f}")
    print(f"  Must-Have Coverage: {sc.must_have_coverage.score:.3f}")
    print(f"  Experience Fit: {sc.experience_fit.score:.3f}")
    print(f"  Role Fit: {sc.role_fit.score:.3f}")
    print(f"  Matched Skills: {sc.matched_skills[:3]}")
    print(f"  Missing Skills: {sc.missing_skills[:3]}")
    print(f"  Strengths: {sc.key_strengths[:2]}")
