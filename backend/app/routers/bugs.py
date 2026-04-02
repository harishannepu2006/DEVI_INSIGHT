"""Bugs router — bug listing, details, and stats."""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.middleware.auth_middleware import get_current_user
from app.utils.supabase_client import get_db

router = APIRouter(prefix="/bugs", tags=["Bugs"])


@router.get("/analysis/{analysis_id}")
async def get_bugs_by_analysis(
    analysis_id: str,
    severity: str = Query(None, description="Filter by severity"),
    category: str = Query(None, description="Filter by category"),
    current_user: dict = Depends(get_current_user)
):
    """Get all bugs for a specific analysis."""
    db = get_db()

    # Verify user has access to this analysis
    analysis = db.table("analysis_results").select("id").eq(
        "id", analysis_id
    ).eq("user_id", current_user["id"]).execute()

    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    query = db.table("bugs").select("*").eq("analysis_id", analysis_id)

    if severity:
        query = query.eq("severity", severity)
    if category:
        query = query.eq("category", category)

    result = query.order("severity").execute()
    return {"bugs": result.data, "total": len(result.data)}


@router.get("/{bug_id}")
async def get_bug(bug_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific bug with full details."""
    db = get_db()
    result = db.table("bugs").select("*, analysis_results(user_id)").eq("id", bug_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug = result.data[0]
    # Verify ownership
    analysis_data = bug.pop("analysis_results", {})
    if analysis_data.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return bug


@router.patch("/{bug_id}/resolve")
async def resolve_bug(bug_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a bug as resolved."""
    db = get_db()
    from datetime import datetime

    result = db.table("bugs").update({
        "is_resolved": True,
        "resolved_at": datetime.utcnow().isoformat(),
    }).eq("id", bug_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Bug not found")

    return {"message": "Bug marked as resolved", "bug": result.data[0]}


@router.get("/stats/{analysis_id}")
async def get_bug_stats(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Get bug statistics for an analysis."""
    db = get_db()
    bugs = db.table("bugs").select("severity, bug_type, category, is_resolved").eq(
        "analysis_id", analysis_id
    ).execute()

    if not bugs.data:
        return {
            "total": 0,
            "by_severity": {},
            "by_type": {},
            "by_category": {},
            "resolved": 0,
            "unresolved": 0,
        }

    by_severity = {}
    by_type = {}
    by_category = {}
    resolved = 0

    for bug in bugs.data:
        sev = bug.get("severity", "medium")
        by_severity[sev] = by_severity.get(sev, 0) + 1

        bt = bug.get("bug_type", "unknown")
        by_type[bt] = by_type.get(bt, 0) + 1

        cat = bug.get("category", "general")
        by_category[cat] = by_category.get(cat, 0) + 1

        if bug.get("is_resolved"):
            resolved += 1

    return {
        "total": len(bugs.data),
        "by_severity": by_severity,
        "by_type": by_type,
        "by_category": by_category,
        "resolved": resolved,
        "unresolved": len(bugs.data) - resolved,
    }
