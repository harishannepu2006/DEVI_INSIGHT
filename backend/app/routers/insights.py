"""Insights router — AI-generated insights for analyses."""
from fastapi import APIRouter, HTTPException, Depends
from app.middleware.auth_middleware import get_current_user
from app.utils.supabase_client import get_db

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/analysis/{analysis_id}")
async def get_insights(analysis_id: str, current_user: dict = Depends(get_current_user)):
    """Get all AI insights for a specific analysis."""
    db = get_db()

    # Verify access
    analysis = db.table("analysis_results").select("id").eq(
        "id", analysis_id
    ).eq("user_id", current_user["id"]).execute()

    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    result = db.table("insights").select("*").eq(
        "analysis_id", analysis_id
    ).order("severity").execute()

    return {"insights": result.data, "total": len(result.data)}


@router.get("/{insight_id}")
async def get_insight(insight_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific insight."""
    db = get_db()
    result = db.table("insights").select("*").eq("id", insight_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Insight not found")

    return result.data[0]
