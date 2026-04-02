"""Analysis Celery tasks — async repository analysis pipeline."""
import logging
from datetime import datetime
from app.tasks.celery_app import celery_app
from app.services.github_service import GitHubService
from app.services.analysis_service import AnalysisService
from app.services.bug_detection import BugDetector
from app.services.ai_engine import AIEngine
from app.utils.supabase_client import get_db

logger = logging.getLogger(__name__)


def calculate_perfect_health_score(analysis_result, bugs):
    """Calculate a strict, comprehensive Health Score based on bugs and metrics."""
    avg_complexity = analysis_result.get("avg_complexity", 0)
    total_issues = analysis_result.get("total_issues", 0)
    debt_hours = analysis_result.get("technical_debt_hours", 0)
    total_lines = analysis_result.get("total_lines", 1)  # avoid div by zero
    total_lines = max(1, total_lines)
    avg_maintainability = analysis_result.get("avg_maintainability", 100.0)
    duplication = analysis_result.get("duplication_percentage", 0.0)
    
    # Normalize
    norm_complexity = min(avg_complexity / 20.0, 1.0)
    
    smells_per_1000 = (total_issues / total_lines) * 1000.0
    norm_smells = min(smells_per_1000 / 25.0, 1.0)
    
    debt_per_1000 = (debt_hours / total_lines) * 1000.0
    norm_debt = min(debt_per_1000 / 10.0, 1.0)
    
    bugs_per_1000 = (len(bugs) / total_lines) * 1000.0
    norm_bugs = min(bugs_per_1000 / 5.0, 1.0)
    
    norm_duplication = min(duplication / 100.0, 1.0)
    norm_maintainability = max(0.0, min(avg_maintainability / 100.0, 1.0))
    
    penalty = (
        (norm_complexity * 0.20) +
        (norm_smells * 0.20) +
        (norm_debt * 0.20) +
        (norm_bugs * 0.15) +
        (norm_duplication * 0.15) +
        ((1.0 - norm_maintainability) * 0.10)
    )
    
    health_score = 100.0 - (penalty * 100.0)
    health_score = max(0.0, min(100.0, health_score))
    
    if health_score >= 85:
        risk_level = "low"
    elif health_score >= 60:
        risk_level = "medium"
    elif health_score >= 30:
        risk_level = "high"
    else:
        risk_level = "critical"
        
    return round(health_score, 1), risk_level


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_analysis(self, analysis_id: str, repo_url: str, branch: str = "main",
                 user_id: str = None, repository_id: str = None):
    """Run full analysis pipeline on a repository."""
    db = get_db()
    github_service = GitHubService()
    analysis_service = AnalysisService()
    bug_detector = BugDetector()
    ai_engine = AIEngine()

    try:
        # Update status to running
        db.table("analysis_results").update({
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }).eq("id", analysis_id).execute()

        # Step 1: Clone repository
        logger.info(f"Cloning repository: {repo_url}")
        repo_path = github_service.clone_repo(repo_url, branch)

        # Step 2: Scan files
        logger.info(f"Scanning files in {repo_path}")
        files = github_service.scan_files(repo_path)

        if not files:
            raise ValueError("No supported source files found in repository")

        # Step 3: Analyze code
        logger.info(f"Analyzing {len(files)} files")
        analysis_result = analysis_service.analyze_files(files)

        # Step 4: Detect bugs
        logger.info("Running bug detection")
        bugs = bug_detector.detect_bugs(files)

        # Recalculate Health Score
        health_score, risk_level = calculate_perfect_health_score(analysis_result, bugs)
        analysis_result["risk_score"] = health_score
        analysis_result["risk_level"] = risk_level

        # Step 5: Generate AI insights
        logger.info("Generating AI insights")
        insights = ai_engine.generate_insights(analysis_result)

        # Step 6: Store results
        # Update analysis record
        db.table("analysis_results").update({
            "status": "completed",
            "total_files": analysis_result["total_files"],
            "total_lines": analysis_result["total_lines"],
            "avg_complexity": analysis_result["avg_complexity"],
            "max_complexity": analysis_result["max_complexity"],
            "technical_debt_hours": analysis_result["technical_debt_hours"],
            "risk_level": analysis_result["risk_level"],
            "risk_score": analysis_result["risk_score"],
            "file_metrics": analysis_result["file_metrics"],
            "language_breakdown": analysis_result["language_breakdown"],
            "hotspot_files": analysis_result["hotspot_files"],
            "summary": f"Analyzed {analysis_result['total_files']} files, "
                       f"{analysis_result['total_lines']} lines. "
                       f"Found {len(bugs)} bugs. Risk: {analysis_result['risk_level']}.",
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", analysis_id).execute()

        # Store bugs
        for bug in bugs:
            bug_record = {
                "analysis_id": analysis_id,
                "repository_id": repository_id,
                "file_path": bug["file_path"],
                "line_number": bug.get("line_number"),
                "bug_type": bug["bug_type"],
                "severity": bug["severity"],
                "title": bug["title"],
                "description": bug.get("description", ""),
                "buggy_code": bug.get("buggy_code", ""),
                "fixed_code": bug.get("fixed_code", ""),
                "explanation": bug.get("explanation", ""),
                "category": bug.get("category", ""),
            }
            db.table("bugs").insert(bug_record).execute()

        # Store insights
        for insight in insights:
            insight_record = {
                "analysis_id": analysis_id,
                "repository_id": repository_id,
                "insight_type": insight.get("insight_type", "suggestion"),
                "severity": insight.get("severity", "medium"),
                "title": insight["title"],
                "description": insight["description"],
                "file_path": insight.get("file_path", ""),
                "recommendation": insight.get("recommendation", ""),
                "estimated_effort": insight.get("estimated_effort", ""),
            }
            db.table("insights").insert(insight_record).execute()

        # Cleanup cloned repo
        github_service.cleanup_repo(repo_path)

        logger.info(f"Analysis {analysis_id} completed successfully")
        return {"status": "completed", "analysis_id": analysis_id, "bugs": len(bugs), "insights": len(insights)}

    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        db.table("analysis_results").update({
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", analysis_id).execute()

        raise self.retry(exc=e)


@celery_app.task
def run_snippet_analysis(analysis_id: str, code: str, language: str, filename: str,
                         user_id: str = None, repository_id: str = None):
    """Run analysis on a code snippet."""
    db = get_db()
    analysis_service = AnalysisService()
    bug_detector = BugDetector()
    ai_engine = AIEngine()

    try:
        db.table("analysis_results").update({
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }).eq("id", analysis_id).execute()

        # Create file info
        files = [{
            "path": filename,
            "content": code,
            "extension": f".{language}" if not filename.endswith(f".{language}") else "",
            "language": language,
            "size": len(code.encode()),
            "lines": code.count('\n') + 1,
        }]

        # Analyze
        analysis_result = analysis_service.analyze_files(files)
        # Detect bugs
        bugs = bug_detector.detect_bugs(files)

        # Recalculate Health Score
        health_score, risk_level = calculate_perfect_health_score(analysis_result, bugs)
        analysis_result["risk_score"] = health_score
        analysis_result["risk_level"] = risk_level

        # Generate insights
        insights = ai_engine.generate_insights(analysis_result)

        # Store results
        db.table("analysis_results").update({
            "status": "completed",
            "total_files": 1,
            "total_lines": analysis_result["total_lines"],
            "avg_complexity": analysis_result["avg_complexity"],
            "max_complexity": analysis_result["max_complexity"],
            "technical_debt_hours": analysis_result["technical_debt_hours"],
            "risk_level": analysis_result["risk_level"],
            "risk_score": analysis_result["risk_score"],
            "file_metrics": analysis_result["file_metrics"],
            "language_breakdown": analysis_result["language_breakdown"],
            "summary": f"Snippet analysis: {len(bugs)} bugs found.",
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", analysis_id).execute()

        for bug in bugs:
            db.table("bugs").insert({
                "analysis_id": analysis_id,
                "repository_id": repository_id,
                "file_path": bug["file_path"],
                "line_number": bug.get("line_number"),
                "bug_type": bug["bug_type"],
                "severity": bug["severity"],
                "title": bug["title"],
                "description": bug.get("description", ""),
                "buggy_code": bug.get("buggy_code", ""),
                "fixed_code": bug.get("fixed_code", ""),
                "explanation": bug.get("explanation", ""),
                "category": bug.get("category", ""),
            }).execute()

        for insight in insights:
            db.table("insights").insert({
                "analysis_id": analysis_id,
                "repository_id": repository_id,
                "insight_type": insight.get("insight_type", "suggestion"),
                "severity": insight.get("severity", "medium"),
                "title": insight["title"],
                "description": insight["description"],
                "recommendation": insight.get("recommendation", ""),
                "estimated_effort": insight.get("estimated_effort", ""),
            }).execute()

        return {"status": "completed", "analysis_id": analysis_id}

    except Exception as e:
        logger.error(f"Snippet analysis {analysis_id} failed: {e}")
        db.table("analysis_results").update({
            "status": "failed",
            "error_message": str(e),
        }).eq("id", analysis_id).execute()
        raise
