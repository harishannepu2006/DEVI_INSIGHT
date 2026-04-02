"""Analysis router — results, history, dashboard stats."""
from fastapi import APIRouter, HTTPException, Depends
from app.middleware.auth_middleware import get_current_user
from app.utils.supabase_client import get_db

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/")
async def list_analyses(current_user: dict = Depends(get_current_user)):
    """List all analyses for the current user."""
    db = get_db()
    result = db.table("analysis_results").select(
        "id, repository_id, status, total_files, total_lines, avg_complexity, "
        "risk_level, risk_score, technical_debt_hours, summary, created_at, completed_at"
    ).eq("user_id", current_user["id"]).order("created_at", desc=True).execute()

    return {"analyses": result.data}


@router.get("/dashboard")
async def dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics for the current user."""
    db = get_db()

    # Get repos count
    repos = db.table("repositories").select("id", count="exact").eq(
        "user_id", current_user["id"]
    ).execute()

    # Get analyses with joined repositories
    analyses = db.table("analysis_results").select("*, repositories(*)").eq(
        "user_id", current_user["id"]
    ).eq("status", "completed").order("created_at", desc=True).execute()

    # Get bug counts
    analysis_ids = [a["id"] for a in (analyses.data or [])]

    total_bugs = 0
    total_insights = 0
    recent_insights = []
    risk_distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    language_distribution = {}
    complexity_trend = []

    for analysis in (analyses.data or []):
        risk = analysis.get("risk_level", "low")
        risk_distribution[risk] = risk_distribution.get(risk, 0) + 1

        lang_breakdown = analysis.get("language_breakdown", {})
        for lang, data in lang_breakdown.items():
            if lang not in language_distribution:
                language_distribution[lang] = 0
            language_distribution[lang] += data.get("files", 0)

        complexity_trend.append({
            "date": analysis.get("created_at", ""),
            "complexity": analysis.get("avg_complexity", 0),
            "risk_score": analysis.get("risk_score", 0),
            "debt_hours": analysis.get("technical_debt_hours", 0),
        })

    if analysis_ids:
        bugs_result = db.table("bugs").select("id", count="exact").in_(
            "analysis_id", analysis_ids
        ).execute()
        total_bugs = bugs_result.count or 0

        insights_result = db.table("insights").select("id", count="exact").in_(
            "analysis_id", analysis_ids
        ).execute()
        total_insights = insights_result.count or 0

        recent_insights_res = db.table("insights").select("*").in_(
            "analysis_id", analysis_ids
        ).order("created_at", desc=True).limit(50).execute()
        recent_insights = recent_insights_res.data or []

    avg_risk = 0
    if analyses.data:
        scores = [a.get("risk_score", 0) for a in analyses.data]
        avg_risk = sum(scores) / len(scores) if scores else 0

    return {
        "total_repos": repos.count or 0,
        "total_analyses": len(analyses.data or []),
        "total_bugs": total_bugs,
        "total_insights": total_insights,
        "avg_risk_score": round(avg_risk, 1),
        "recent_analyses": (analyses.data or [])[:5],
        "risk_distribution": risk_distribution,
        "language_distribution": language_distribution,
        "complexity_trend": complexity_trend[:20],
        "recent_insights": recent_insights,
    }


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific analysis result."""
    db = get_db()
    result = db.table("analysis_results").select("*").eq("id", analysis_id).eq(
        "user_id", current_user["id"]
    ).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return result.data[0]


@router.get("/{analysis_id}/history")
async def get_repo_history(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Get analysis history for the repository of this analysis."""
    db = get_db()

    # Get the repo ID from the analysis
    analysis = db.table("analysis_results").select("repository_id").eq(
        "id", analysis_id
    ).eq("user_id", current_user["id"]).execute()

    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    repo_id = analysis.data[0]["repository_id"]

    # Get all analyses for this repo
    history = db.table("analysis_results").select(
        "id, status, total_files, total_lines, avg_complexity, max_complexity, "
        "technical_debt_hours, risk_level, risk_score, summary, created_at, completed_at"
    ).eq("repository_id", repo_id).eq("status", "completed").order("created_at", desc=True).execute()

    return {"history": history.data, "repository_id": repo_id}
