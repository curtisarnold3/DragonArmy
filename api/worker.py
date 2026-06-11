"""RQ worker stub — wraps pipeline.run() for async execution.
Per D-007: currently unused (BackgroundTasks used in main.py MVP).
Swap main.py to use this when RQ + Redis are enabled.
"""
import logging

logger = logging.getLogger(__name__)


def run_job(job_id: str, input_path: str, output_dir: str):
    """Run pipeline for a job. Called by RQ worker when RQ is enabled."""
    from pipeline.pipeline import run

    result = run(input_path, output_dir)
    logger.info(f"Job {job_id} complete: {result}")
    return result
