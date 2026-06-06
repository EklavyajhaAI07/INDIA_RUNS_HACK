# 🔴 Redrob AI — Candidate Intelligence & Reranking System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/react-19.0-cyan.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/vite-8.0-purple.svg)](https://vite.dev/)
[![TailwindCSS v4](https://img.shields.io/badge/tailwindcss-v4.0-blueviolet.svg)](https://tailwindcss.com/)
[![Three.js](https://img.shields.io/badge/three.js-r184-black.svg)](https://threejs.org/)

An enterprise-grade, explainable candidate ranking and retrieval engine built for the **India.Runs Data & AI Challenge**. Redrob AI replaces opaque, black-box similarity scores and rigid keyword filters with a transparent, 4-stage pipeline that combines lexical search, semantic embeddings, multi-factor deterministic scoring, and natural language explanations.

---

## 🔍 System Data Flow

Below is the conceptual architecture of the Candidate Intelligence pipeline:

![Data Flow Diagram](./ranker/frontend/public/data_flow_explanation.png)

*For a deep technical breakdown of the system pipeline, mathematical formulas, and design tradeoffs, see the [Architecture Documentation](./ARCHITECTURE.md).*

---

## ✨ Key Features

### 1. Hybrid Retrieval Engine (Stage 1 & 2)
- **BM25 Lexical Indexing**: Uses `rank_bm25` for fast, exact matches on mandatory skill terms, acronyms, and tools.
- **Dense Semantic Embeddings**: Utilizes `SentenceTransformers` (`all-MiniLM-L6-v2`) to capture context, synonyms, and conceptual similarities (e.g., matching "Machine Learning" with "ML model development").
- **FAISS Clustering**: Leverages Facebook AI Similarity Search (IVFFlat/FlatL2 indexes) to perform sub-millisecond semantic retrieval across 100,000+ candidates.

### 2. Multi-Factor Reranker (Stage 3)
Instead of relying on a single raw embedding similarity score, candidates are scored using a deterministic, 7-factor equation:

$$\text{FinalScore} = 0.35(\text{SemanticFit}) + 0.20(\text{MustHaveCoverage}) + 0.15(\text{ExperienceFit}) + 0.10(\text{RoleFit}) + 0.10(\text{Recency}) + 0.05(\text{BehavioralSignals}) + 0.05(\text{BonusFit})$$

### 3. Recruiter Trust Explainer (Stage 4)
- Generates precise, evidence-backed explanations from features gathered during the scoring phase.
- Prevents LLM hallucinations by reading strictly from deterministic metadata and metrics.
- Example output: `Knows Python, SQL +2 more; 5.5yr experience; Current: Senior ML Engineer; Strong semantic match`

### 4. Interactive 3D Recruiter Dashboard
- A premium React frontend built with Vite, Tailwind CSS v4, and Three.js (`@react-three/fiber` & `@react-three/drei`).
- Dynamic glassmorphic UI cards, micro-animations via `framer-motion` and `gsap`, and a particle-field background representing candidate node clusters.
- Features detailed score breakdowns, side-by-side strengths and concerns, and full career path visualizers.

---

## 📂 Project Structure

```bash
India.Runs Hack/
├── India_runs_data_and_ai_challenge/   # Challenge datasets & schemas
│   ├── job_description.docx             # Sample input job description
│   ├── candidates.jsonl                 # Full candidates database (100K+ entries)
│   └── validate_submission.py           # Submission file verifier
├── ranker/                              # Core ranking engine codebase
│   ├── main.py                          # E2E pipeline orchestrator
│   ├── data_ingestion/                  # Loader, models & cleaning
│   │   └── loader.py                    # JSONL parser into Candidate objects
│   ├── jd_parser/                       # Job description parser
│   │   └── parser.py                    # Regular expression & rule requirements extractor
│   ├── retrieval/                       # BM25 + FAISS Dense Retriever
│   │   └── retriever.py                 # HybridSearch, index saver/loader
│   ├── reranker/                        # Scoring engine
│   │   └── scorer.py                    # 7-factor CandidateScorer
│   ├── explainability/                  # Reason generator
│   │   └── explainer.py                 # Natural language reasoning formatter
│   └── frontend/                        # Recruiter Dashboard UI
│       ├── src/                         # React components, Three.js backgrounds, hooks
│       ├── index.html                   # HTML Entry point
│       └── package.json                 # Frontend package manifest
├── README.md                            # You are here!
└── ARCHITECTURE.md                      # System design and specifications
```

---

## 🚀 Setup & Execution Guide

### 📋 Prerequisites
- Python 3.9+
- Node.js 18+ & npm

### 🐍 Backend Installation & Pipeline Execution

1. Navigate to the `ranker` directory:
   ```bash
   cd ranker
   ```

2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   # Ensure you have docx, rank_bm25, sentence_transformers, faiss-cpu (or faiss-gpu), and numpy
   ```

3. Run the end-to-end ranking pipeline:
   ```bash
   python main.py --candidates ../India_runs_data_and_ai_challenge/candidates.jsonl --jd ../India_runs_data_and_ai_challenge/job_description.docx --out ../submission.csv
   ```
   *Options:*
   - `--top-k-retrieve`: Number of candidates retrieved in hybrid search phase (default: 1000).
   - `--top-k-output`: Number of top-ranked candidates to output to the CSV (default: 100).

4. Verify submission validity:
   ```bash
   python ../India_runs_data_and_ai_challenge/validate_submission.py --submission ../submission.csv --candidates ../India_runs_data_and_ai_challenge/candidates.jsonl
   ```

---

### 💻 Frontend Installation & Local Server

1. Navigate to the `frontend` directory:
   ```bash
   cd ranker/frontend
   ```

2. Install Node packages:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open the displayed URL (usually `http://localhost:5173`) in your browser to experience the **Redrob AI Candidate Intelligence Dashboard** with real-time searches, sorts, and detail modal visualizations.

---

## ⚙️ Assumptions

1. **Candidate data** is provided as a JSONL file where each line contains a structured candidate profile with `profile`, `career_history`, `education`, `skills`, and `redrob_signals` fields.
2. **Job description** is provided as a `.docx` or `.txt` file with standard formatting (sections for requirements, responsibilities, qualifications).
3. **Experience values** in candidate profiles are numerically accurate (years as floats).
4. **Skills** are normalized to lowercase for matching (e.g., "Python" == "python").
5. **Recency window** defaults to 24 months for evaluating recent relevant experience.
6. **Platform signals** (profile completion, response rate, endorsements) are populated in `redrob_signals` for behavioral scoring; missing values default to neutral scores.
7. **Must-have skills** in the JD are treated as non-negotiable gating criteria; nice-to-have skills provide bonus points only.
8. **Output is deterministic** — running the same inputs through the pipeline produces identical rankings every time (no randomization).

---

## 📊 Sample Output

The pipeline produces a `submission.csv` with the following columns:

```csv
candidate_id,rank,score,top_matched_skills,missing_must_haves,breakdown_scores,reasoning
CAND_0033861,1,0.851310,"embeddings, sentence-transformers, pinecone, faiss, vector-databases, nlp, pytorch, transformers, bert, rag, langchain, openai, llm, fine-tuning, prompt-engineering",,"semantic_fit=0.85, must_have_coverage=0.90, experience_fit=1.00, role_fit=0.80, recency=1.00, behavioral_fit=0.70, bonus_fit=0.75","Knows embeddings, sentence-transformers, pinecone +10 more; 8.0yr experience; Current: senior nlp engineer; Strong semantic match"
CAND_0071974,2,0.801132,"embeddings, pinecone, weaviate, faiss, vector-databases, nlp, pytorch, transformers, bert, rag, langchain",,"semantic_fit=0.82, must_have_coverage=0.85, experience_fit=1.00, role_fit=0.75, recency=1.00, behavioral_fit=0.65, bonus_fit=0.70","Knows embeddings, pinecone, weaviate +6 more; 7.8yr experience; Current: senior ai engineer; Strong semantic match"
CAND_0046064,3,0.779139,"embeddings, faiss, pinecone, sentence-transformers, vector-databases, nlp, pytorch, transformers, bert, rag, langchain, openai",,"semantic_fit=0.80, must_have_coverage=0.80, experience_fit=1.00, role_fit=0.70, recency=1.00, behavioral_fit=0.60, bonus_fit=0.65","Knows embeddings, faiss, pinecone +10 more; 8.9yr experience; Current: senior nlp engineer; Strong semantic match"
```

| Column | Description |
|---|---|
| `candidate_id` | Unique identifier for the candidate |
| `rank` | Final rank (1 = best) |
| `score` | Composite score (0.0 – 1.0) |
| `top_matched_skills` | Must-have skills matched from the candidate profile |
| `missing_must_haves` | Required skills the candidate is missing |
| `breakdown_scores` | Individual 7-factor scores for full explainability |
| `reasoning` | Human-readable explanation of the ranking decision |

---

## ⚖️ Scoring Breakdown Details

| Weight | Feature | Description |
|---|---|---|
| **35%** | **Semantic Fit** | Dense vector similarity of candidate profiles vs. JD text. |
| **20%** | **Must-Have Coverage** | Exact or normalized match rate for required skills/tools. |
| **15%** | **Experience Fit** | Distance between candidate years of experience and JD requirements. |
| **10%** | **Role Fit** | Relevance of candidate's current and past job titles to the target role. |
| **10%** | **Recency** | Weighting based on how recently they used the required stack. |
| **5%** | **Behavioral Signals** | Profile completion rate, responsiveness, and endorsements. |
| **5%** | **Bonus Fit** | Nice-to-have technologies and bonus qualifications. |

---

## 📝 License
This project is licensed under the MIT License. See [LICENSE](./ranker/frontend/LICENSE) for more details.
# Video Presentation

[Watch the Redrob video presentation](Redrob_video_presentation.mp4)
