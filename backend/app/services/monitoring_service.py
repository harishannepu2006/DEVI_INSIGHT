"""Continuous monitoring service."""
import logging
from datetime import datetime, timedelta
from app.utils.supabase_client import get_db

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for continuous repository monitoring."""

    def __init__(self):
        self.db = get_db()

    def enable_monitoring(self, repository_id: str, interval_hours: int = 24, notification_enabled: bool = True) -> dict:
        """Enable monitoring for a repository."""
        config = {
            "repository_id": repository_id,
            "is_active": True,
            "interval_hours": interval_hours,
            "notification_enabled": notification_enabled,
            "next_run_at": (datetime.utcnow() + timedelta(hours=interval_hours)).isoformat(),
        }

        # Upsert monitoring config
        result = self.db.table("monitoring_config").upsert(config, on_conflict="repository_id").execute()

        # Update repository flag
        self.db.table("repositories").update(
            {"is_monitoring_enabled": True, "monitoring_interval_hours": interval_hours}
        ).eq("id", repository_id).execute()

        return result.data[0] if result.data else config

    def disable_monitoring(self, repository_id: str) -> bool:
        """Disable monitoring for a repository."""
        self.db.table("monitoring_config").update(
            {"is_active": False}
        ).eq("repository_id", repository_id).execute()

        self.db.table("repositories").update(
            {"is_monitoring_enabled": False}
        ).eq("id", repository_id).execute()

        return True

    def get_monitoring_config(self, repository_id: str) -> dict | None:
        """Get monitoring configuration for a repository."""
        result = self.db.table("monitoring_config").select("*").eq(
            "repository_id", repository_id
        ).execute()
        return result.data[0] if result.data else None

    def get_due_repos(self) -> list[dict]:
        """Get repositories that are due for re-analysis."""
        now = datetime.utcnow().isoformat()
        result = self.db.table("monitoring_config").select(
            "*, repositories(*)"
        ).eq("is_active", True).lte("next_run_at", now).execute()
        return result.data or []

    def update_after_run(self, repository_id: str, commit_sha: str = None):
        """Update monitoring config after a successful run."""
        config = self.get_monitoring_config(repository_id)
        if not config:
            return

        interval = config.get("interval_hours", 24)
        next_run = (datetime.utcnow() + timedelta(hours=interval)).isoformat()

        update_data = {
            "last_run_at": datetime.utcnow().isoformat(),
            "next_run_at": next_run,
        }
        if commit_sha:
            update_data["last_commit_sha"] = commit_sha

        self.db.table("monitoring_config").update(update_data).eq(
            "repository_id", repository_id
        ).execute()

        self.db.table("repositories").update(
            {"last_monitored_at": datetime.utcnow().isoformat()}
        ).eq("id", repository_id).execute()
