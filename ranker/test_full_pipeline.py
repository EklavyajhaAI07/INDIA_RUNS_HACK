import sys
import io

# Ensure stdout is UTF-8 before any imports
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main import run_pipeline

# Run with limited candidates for testing
print("Running full pipeline with 100 candidates...")
output = run_pipeline(
    candidates_path=r"..\India_runs_data_and_ai_challenge\candidates.jsonl",
    jd_path=r"..\India_runs_data_and_ai_challenge\job_description.docx",
    output_path=r"test_output.csv",
    top_k_retrieve=50,
    top_k_output=10,
)

# Show the output
print("\n=== OUTPUT CSV CONTENTS ===")
with open(output, "r", encoding="utf-8") as f:
    print(f.read())
