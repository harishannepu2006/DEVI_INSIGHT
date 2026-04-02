"""Monitoring Celery tasks — periodic repo re-analysis."""
import logging
from app.tasks.celery_app import celery_app
from app.services.monitoring_service import MonitoringService
from app.tasks.analysis_tasks import run_analysis

logger = logging.getLogger(__name__)


@celery_app.task
def check_monitored_repos():
    """Check for repos due for re-analysis and trigger analysis."""
    monitoring_service = MonitoringService()

    due_repos = monitoring_service.get_due_repos()
    logger.info(f"Found {len(due_repos)} repos due for monitoring")

    for config in due_repos:
        repo = config.get("repositories", {})
        if not repo:
            continue

        repo_id = repo.get("id")
        repo_url = repo.get("url")
        user_id = repo.get("user_id")

        if not repo_url:
            continue

        try:
            # Create new analysis record
            from app.utils.supabase_client import get_db
            db = get_db()

            result = db.table("analysis_results").insert({
                "repository_id": repo_id,
                "user_id": user_id,
                "status": "queued",
            }).execute()

            analysis_id = result.data[0]["id"]

            # Trigger analysis
            run_analysis.delay(
                analysis_id=analysis_id,
                repo_url=repo_url,
                user_id=user_id,
                repository_id=repo_id,
            )

            # Update monitoring timestamp
            monitoring_service.update_after_run(repo_id)
            logger.info(f"Triggered re-analysis for repo {repo_id}")

        except Exception as e:
            logger.error(f"Failed to trigger monitoring for repo {repo_id}: {e}")
