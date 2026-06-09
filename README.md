# 🔴 Redrob AI — Candidate Intelligence & Reranking System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/react-19.0-cyan.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/vite-8.0-purple.svg)](https://vite.dev/)
[![TailwindCSS v4](https://img.shields.io/badge/tailwindcss-v4.0-blueviolet.svg)](https://tailwindcss.com/)
[![Three.js](https://img.shields.io/badge/three.js-r184-black.svg)](https://threejs.org/)

An explainable candidate ranking and retrieval system built for the **India.Runs Data & AI Challenge**.

This repository combines:

- Job description parsing
- Candidate data ingestion from JSONL
- BM25-based candidate retrieval
- Deterministic multi-factor reranking
- Human-readable explanation generation
- A React-based recruiter dashboard demo

## Important Note

The current runnable pipeline in `ranker/main.py` uses BM25 lexical retrieval as the active retrieval step. The repository also contains semantic embedding + FAISS retrieval utilities inside `ranker/retrieval/retriever.py`, but they are not enabled in the default `main.py` flow right now.

---

## 🔍 System Data Flow

Below is the conceptual architecture of the Candidate Intelligence pipeline:

![Data Flow Diagram](./ranker/frontend/public/data_flow_explanation.png)

*For a deep technical breakdown of the system pipeline, mathematical formulas, and design tradeoffs, see the [Architecture Documentation](./ARCHITECTURE.md).*

---

## Overview

Redrob AI is designed to rank candidates in a transparent and recruiter-friendly way.

Instead of relying only on opaque similarity scores, the system separates the ranking process into clear stages:

1. Parse the job description
2. Load and normalize candidate data
3. Retrieve relevant candidates using BM25
4. Score candidates using a deterministic 7-factor reranker
5. Generate short, evidence-based reasoning strings
6. Export a validator-compatible submission CSV

---

## Current Pipeline

The current default pipeline in `ranker/main.py` works as follows:

### Stage 1 — Job Description Parsing

The parser reads a `.docx` or `.txt` job description and extracts:

- role title
- company
- location
- employment type
- min/max experience
- must-have skills
- nice-to-have skills
- explicit exclusions
- domain
- seniority
- remote/location preferences
- hard filters

### Stage 2 — Candidate Loading

The loader reads `candidates.jsonl` and creates structured candidate objects containing:

- profile information
- career history
- education
- skills
- Redrob platform signals

It also generates searchable metadata such as:

- `search_text`
- `skill_names`
- `all_titles`
- `all_industries`
- `all_companies`

### Stage 3 — Retrieval

The active retrieval step in `main.py` is:

- BM25 index build
- BM25 search over candidate search text

The code then applies simple hard filters before scoring, including experience thresholding and minimum matched must-have skills.

### Stage 4 — Scoring

Candidates are reranked using a deterministic weighted formula:

$$
\text{FinalScore} = 0.35(\text{SemanticFit}) + 0.20(\text{MustHaveCoverage}) + 0.15(\text{ExperienceFit}) + 0.10(\text{RoleFit}) + 0.10(\text{Recency}) + 0.05(\text{BehavioralFit}) + 0.05(\text{BonusFit})
$$

### Stage 5 — Explainability

The explainer generates short reasoning strings based on actual evidence collected during scoring.

Example style:

- `Knows Python, SQL, Airflow +2 more; 5.5yr experience; Current: Senior Data Engineer`
- `Knows embeddings, pinecone, faiss +6 more; 7.8yr experience; Current: senior ai engineer`

### Stage 6 — Output

The pipeline writes a validator-compatible CSV with exactly these columns:

- `candidate_id`
- `rank`
- `score`
- `reasoning`

---

## Retrieval Architecture Notes

The repository includes a more advanced retrieval module in `ranker/retrieval/retriever.py` with support for:

- BM25 lexical search
- SentenceTransformers semantic embeddings
- FAISS-based semantic indexing
- Hybrid score combination
- Index save/load utilities

However:

- `main.py` currently uses only BM25 retrieval
- Semantic retrieval and hybrid retrieval are implemented but not called in the default pipeline

So the best way to describe the current system is:

> **Current runnable pipeline**: BM25 retrieval + deterministic reranking + explanation generation  
> **Available extension in repo**: semantic embeddings + FAISS + hybrid retrieval utilities

---

## Key Features

### 1. Explainable Ranking

The scoring system is deterministic and decomposed into named factors, making it easier to inspect and trust.

### 2. Structured JD Parsing

The parser converts unstructured `.docx` / `.txt` job descriptions into machine-readable requirements.

### 3. Searchable Candidate Representation

Candidate profiles are transformed into searchable text plus reusable metadata for retrieval and scoring.

### 4. Evidence-Based Explanations

The reasoning generator produces short recruiter-friendly explanations without inventing unsupported claims.

### 5. Recruiter Dashboard Demo

The frontend provides an interactive UI to visualize ranked candidates.

> **Note**: The current frontend uses a static local JSON dataset (`ranker/frontend/src/data/candidates.json`) for demo purposes. It is not currently wired to a live backend/API in the checked-in code.

---

## Project Structure

```
India.Runs Hack Main Codebase/
├── README.md
├── ARCHITECTURE.md
├── India_runs_data_and_ai_challenge/
│   ├── job_description.docx
│   ├── candidates.jsonl
│   └── validate_submission.py
└── ranker/
    ├── main.py
    ├── api.py
    ├── requirements.txt
    ├── data_ingestion/
    │   └── loader.py
    ├── jd_parser/
    │   └── parser.py
    ├── retrieval/
    │   └── retriever.py
    ├── reranker/
    │   └── scorer.py
    ├── explainability/
    │   └── explainer.py
    ├── feedback/
    │   ├── store.py
    │   └── adapter.py
    └── frontend/
        ├── package.json
        ├── index.html
        ├── LICENSE
        └── src/
            ├── main.jsx
            ├── App.jsx
            ├── index.css
            └── components/
                ├── ThreeBackground.jsx
                ├── CandidateTable.jsx
                ├── CandidateRow.jsx
                ├── CandidateModal.jsx
                ├── Header.jsx
                ├── ScoreBar.jsx
                ├── CursorPhysics.jsx
                └── FailureCasesModal.jsx
```

---

## Backend Setup

### Prerequisites

- Python 3.9+
- pip

### Install dependencies

```bash
cd ranker
pip install -r requirements.txt
```

Current `requirements.txt` includes:

- `numpy`
- `rank-bm25`
- `python-docx`
- `sentence-transformers`
- `faiss-cpu`
- `fastapi`
- `uvicorn`

### Run the Ranking Pipeline

From the `ranker/` directory:

```bash
python main.py \
  --candidates ../India_runs_data_and_ai_challenge/candidates.jsonl \
  --jd ../India_runs_data_and_ai_challenge/job_description.docx \
  --out ../submission.csv
```

#### Optional arguments

```
--top-k-retrieve   # Number of candidates retrieved before reranking (default: 1000)
--top-k-output     # Number of final candidates written to output CSV (default: 100)
--use-feedback     # Use adaptive weights from recruiter feedback if available
```

### Validate Submission

After generating the CSV, validate it with:

```bash
python ../India_runs_data_and_ai_challenge/validate_submission.py ../submission.csv
```

The validator expects:

- a `.csv` file
- exactly 100 data rows
- this exact header order:

```
candidate_id,rank,score,reasoning
```

---

## Sample Output

The current pipeline writes output in this format:

```csv
candidate_id,rank,score,reasoning
CAND_0033861,1,0.85131,"Knows embeddings, sentence-transformers, pinecone +10 more; 8.0yr experience; Current: senior nlp engineer; Strong semantic match"
CAND_0071974,2,0.80113,"Knows embeddings, pinecone, weaviate +6 more; 7.8yr experience; Current: senior ai engineer; Strong semantic match"
CAND_0046064,3,0.77914,"Knows embeddings, faiss, pinecone +9 more; 8.9yr experience; Current: senior nlp engineer; Strong semantic match"
```

### Output Columns

| Column | Description |
|---|---|
| `candidate_id` | Unique candidate identifier |
| `rank` | Final rank from 1 to 100 |
| `score` | Final composite score |
| `reasoning` | Short human-readable explanation |

---

## Scoring Breakdown

The reranker uses the following weights:

| Weight | Factor | Description |
|---|---|---|
| 35% | Semantic Fit | Candidate relevance signal used by scorer |
| 20% | Must-Have Coverage | Match rate on required skills |
| 15% | Experience Fit | Alignment with JD experience range |
| 10% | Role Fit | Relevance of titles and role history |
| 10% | Recency | How recently relevant experience was used |
| 5% | Behavioral Fit | Platform signals such as profile completion / responsiveness |
| 5% | Bonus Fit | Nice-to-have or bonus qualifications |

---

## Frontend Setup

### Prerequisites

- Node.js 18+
- npm

### Install and run

```bash
cd ranker/frontend
npm install
npm run dev
```

### Frontend stack

The frontend uses:

- React 19
- Vite
- Tailwind CSS v4
- Three.js
- `@react-three/fiber`
- `@react-three/drei`
- `framer-motion`
- `gsap`

### What the current frontend does

The checked-in frontend currently provides:

- search by candidate ID or reasoning
- sort by rank or score
- pagination
- modal/detail interactions
- animated visual presentation

### Current limitation

The dashboard currently reads from:

```
ranker/frontend/src/data/candidates.json
```

So it should be described as a static/demo visualization layer, not a live production recruiter console.

---

## Assumptions

This repository currently assumes:

1. Candidate data is available as a JSONL file.
2. Each record contains fields such as `profile`, `career_history`, `education`, `skills`, and `redrob_signals`.
3. Job descriptions are provided as `.docx` or `.txt`.
4. Candidate skills can be normalized to lowercase for matching.
5. The final output must follow the challenge validator schema.
6. The frontend demo visualizes a static exported ranking dataset.

---

## Known Gaps / Future Improvements

The repo already contains building blocks for additional improvements:

- enable semantic retrieval in the main pipeline
- combine BM25 + semantic search in production flow
- expose retrieval/ranking through a proper API
- connect frontend to backend instead of static JSON
- surface richer score breakdowns in exported artifacts
- add benchmarking / evaluation scripts
- add root-level repository license file for clearer distribution

---

## License

This repository includes an MIT license file at:

```
ranker/frontend/LICENSE
```

If you plan to use this as a full repository-level open-source project, it is recommended to also place a `LICENSE` file at the repository root for clarity.

---

## Repository Notes

This README is aligned to the current checked-in code behavior:

- `main.py` → active runnable pipeline
- `retriever.py` → advanced retrieval utilities available in repo
- `validate_submission.py` → authoritative CSV output format
- `frontend/src/data/candidates.json` → current frontend data source

---

# Video Presentation

[![Watch Demo](https://img.youtube.com/vi/yl_nhRdBpJE/maxresdefault.jpg)](https://youtu.be/yl_nhRdBpJE)
