import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from data_ingestion import load_candidates
from retrieval import HybridRetriever

# Load 100 candidates for testing
print("Loading candidates...")
candidates = load_candidates(r"..\India_runs_data_and_ai_challenge\candidates.jsonl", limit=100)
print(f"Loaded {len(candidates)} candidates")

# Build BM25 index
retriever = HybridRetriever()
retriever.build_bm25_index(candidates)

# Test search
jd_query = "embeddings FAISS vector database Python ranking evaluation NDCG machine learning"
results = retriever.bm25_search(jd_query, top_k=10)

print(f"\n=== TOP 10 BM25 RESULTS ===")
print(f"Query: {jd_query}")
print()

for rank, (cid, score) in enumerate(results, 1):
    c = next((c for c in candidates if c.candidate_id == cid), None)
    if c:
        print(f"{rank}. {cid} (score: {score:.3f})")
        print(f"   Title: {c.current_title} @ {c.current_company}")
        print(f"   Skills: {', '.join(c.skill_names[:5])}")
        print()
