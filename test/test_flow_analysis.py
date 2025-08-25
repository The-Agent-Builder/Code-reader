import asyncio
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.flows.analysis_flow import analyze_repository

REPO_URL = "https://github.com/The-Pocket/PocketFlow/"


def on_progress(current_file: Optional[str] = None):
    """Simple progress callback used by CodeParsingBatchNode."""
    if current_file:
        print(f"[progress] parsing: {current_file}")


async def run_test_quick():
    """Run the QuickAnalysisFlow (skips vectorization)."""
    shared = await analyze_repository(
        REPO_URL,
        use_vectorization=False,  # quick mode: no vector store required
        batch_size=5,
        progress_callback=on_progress,
    )

    # Minimal, direct console output
    print("=== Analysis Flow (Quick) ===")
    print(f"repo: {REPO_URL}")
    print(f"status: {shared.get('status')}")
    print(f"stage: {shared.get('current_stage')}")
    print(f"files_analyzed: {len(shared.get('code_analysis', []))}")
    print(f"report: {shared.get('analysis_report_path', '')}")
    print(f"result_file: {shared.get('result_filepath', '')}")
    if shared.get("error"):
        print(f"error: {shared.get('error')}")


async def run_test_full():
    """Run the Full GitHubAnalysisFlow (includes vectorization/RAG)."""
    shared = await analyze_repository(
        REPO_URL,
        use_vectorization=True,
        batch_size=5,
        progress_callback=on_progress,
    )

    print("=== Analysis Flow (Full, with RAG) ===")
    print(f"repo: {REPO_URL}")
    print(f"status: {shared.get('status')}")
    print(f"stage: {shared.get('current_stage')}")
    print(f"vector_index: {shared.get('vectorstore_index', '')}")
    print(f"files_analyzed: {len(shared.get('code_analysis', []))}")
    print(f"report: {shared.get('analysis_report_path', '')}")
    print(f"result_file: {shared.get('result_filepath', '')}")
    if shared.get("error"):
        print(f"error: {shared.get('error')}")


if __name__ == "__main__":
    # Default to full flow to perform vectorization (RAG)
    asyncio.run(run_test_full())
