"""
Main Orchestrator — Ties all modules together.

This is the entry point that runs the full pipeline:
1. Parse job description
2. Load all candidates
3. Retrieve top candidates using hybrid search
4. Score and rank candidates
5. Generate explanations
6. Output top 100 to CSV

Usage:
    python main.py --candidates ./candidates.jsonl --jd ./job_description.docx --out ./submission.csv
"""

import argparse
import csv
import json
import sys
import io
import time
from pathlib import Path


def run_pipeline(candidates_path: str, jd_path: str, output_path: str,
                 top_k_retrieve: int = 1000, top_k_output: int = 100):
    """
    Run the full ranking pipeline.

    Args:
        candidates_path: Path to candidates.jsonl
        jd_path: Path to job description (.docx or .txt)
        output_path: Path to output CSV
        top_k_retrieve: Number of candidates to retrieve (default: 1000)
        top_k_output: Number of candidates to output (default: 100)
    """
    start_time = time.time()

    # ============================================================
    # STAGE 1: Parse Job Description
    # ============================================================
    print("=" * 60)
    print("STAGE 1: Parsing Job Description")
    print("=" * 60)

    from jd_parser import parse_jd_from_file
    jd = parse_jd_from_file(jd_path)

    print(f"  Role: {jd.role_title}")
    print(f"  Company: {jd.company}")
    print(f"  Experience: {jd.min_years}-{jd.max_years} years")
    print(f"  Must-have skills: {len(jd.must_have_skills)}")
    print(f"  Nice-to-have skills: {len(jd.nice_to_have_skills)}")
    print(f"  Location: {jd.location}")

    # ============================================================
    # STAGE 2: Load Candidates
    # ============================================================
    print("\n" + "=" * 60)
    print("STAGE 2: Loading Candidates")
    print("=" * 60)

    from data_ingestion import load_candidates
    candidates = load_candidates(candidates_path)
    print(f"  Loaded {len(candidates)} candidates")

    # ============================================================
    # STAGE 3: Retrieve Top Candidates
    # ============================================================
    print("\n" + "=" * 60)
    print("STAGE 3: Retrieving Top Candidates")
    print("=" * 60)

    from retrieval import HybridRetriever

    # Build search query from JD
    search_query = f"{jd.role_title} "
    search_query += " ".join(jd.must_have_skills[:10])
    search_query += " " + " ".join(jd.nice_to_have_skills[:5])
    search_query += f" {jd.domain} Python machine learning"

    print(f"  Search query: {search_query[:80]}...")

    retriever = HybridRetriever()
    retriever.build_bm25_index(candidates)

    # Retrieve top candidates
    results = retriever.bm25_search(search_query, top_k=top_k_retrieve)
    print(f"  Retrieved {len(results)} candidates")

    # Get candidate objects for top results
    candidate_map = {c.candidate_id: c for c in candidates}
    top_candidates = []

    # Find max retrieval score for proper normalization
    max_retrieval_score = max((score for _, score in results), default=1.0)
    if max_retrieval_score > 0:
        norm_factor = max(max_retrieval_score, 1.0)
    else:
        norm_factor = 1.0

    for cid, score in results:
        if cid in candidate_map:
            c = candidate_map[cid]
            c._retrieval_score = min(1.0, score / norm_factor)  # Normalize to 0-1
            top_candidates.append(c)

    # ============================================================
    # STAGE 4: Score and Rank
    # ============================================================
    print("\n" + "=" * 60)
    print("STAGE 4: Scoring and Ranking")
    print("=" * 60)

    from reranker import CandidateScorer
    scorer = CandidateScorer()
    scored = scorer.score_candidates(top_candidates, jd)

    print(f"  Scored {len(scored)} candidates")
    print(f"  Top score: {scored[0].final_score:.4f}")
    print(f"  Bottom score (top {top_k_output}): {scored[min(top_k_output-1, len(scored)-1)].final_score:.4f}")

    # ============================================================
    # STAGE 5: Generate Explanations
    # ============================================================
    print("\n" + "=" * 60)
    print("STAGE 5: Generating Explanations")
    print("=" * 60)

    from explainability import Explainer
    explainer = Explainer()

    # Convert to dictionaries for explainer
    scored_dicts = []
    for sc in scored[:top_k_output]:
        sc_dict = sc.to_dict()
        sc_dict["semantic_fit"] = {"score": sc.semantic_fit.score, "raw_value": sc.semantic_fit.raw_value}
        sc_dict["must_have_coverage"] = {"score": sc.must_have_coverage.score, "raw_value": sc.must_have_coverage.raw_value}
        sc_dict["experience_fit"] = {"score": sc.experience_fit.score, "raw_value": sc.experience_fit.raw_value}
        sc_dict["role_fit"] = {"score": sc.role_fit.score, "raw_value": sc.role_fit.raw_value}
        sc_dict["recency"] = {"score": sc.recency.score, "raw_value": sc.recency.raw_value}
        sc_dict["behavioral_fit"] = {"score": sc.behavioral_fit.score, "raw_value": sc.behavioral_fit.raw_value}
        sc_dict["bonus_fit"] = {"score": sc.bonus_fit.score, "raw_value": sc.bonus_fit.raw_value}
        scored_dicts.append(sc_dict)

    scored_dicts = explainer.explain_batch(scored_dicts, candidate_map)

    # ============================================================
    # STAGE 6: Output CSV
    # ============================================================
    print("\n" + "=" * 60)
    print("STAGE 6: Writing Output CSV")
    print("=" * 60)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for sc in scored_dicts:
            writer.writerow([
                sc["candidate_id"],
                sc["rank"],
                f"{sc['final_score']:.6f}",
                sc["reasoning"]
            ])

    print(f"  Wrote {len(scored_dicts)} candidates to {output_file}")

    # ============================================================
    # Summary
    # ============================================================
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Total time: {elapsed:.2f} seconds")
    print(f"  Output file: {output_file}")
    print(f"  Top candidate: {scored_dicts[0]['candidate_id']} (score: {scored_dicts[0]['final_score']:.4f})")
    print(f"  Reasoning: {scored_dicts[0]['reasoning']}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Candidate Ranking Pipeline")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--jd", required=True, help="Path to job description (.docx or .txt)")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--top-k-retrieve", type=int, default=1000, help="Number of candidates to retrieve")
    parser.add_argument("--top-k-output", type=int, default=100, help="Number of candidates to output")

    args = parser.parse_args()

    run_pipeline(
        candidates_path=args.candidates,
        jd_path=args.jd,
        output_path=args.out,
        top_k_retrieve=args.top_k_retrieve,
        top_k_output=args.top_k_output,
    )


if __name__ == "__main__":
    # Ensure stdout is UTF-8 only when running as main script
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
