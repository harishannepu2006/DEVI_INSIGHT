from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.middleware.auth_middleware import get_current_user
from app.utils.supabase_client import get_db
from app.services.github_service import GitHubService
from app.models.schemas import RepoSubmitRequest, CodeSnippetRequest, RepositoryResponse, InsightsResponse
from app.tasks.analysis_tasks import run_analysis, run_snippet_analysis

router = APIRouter(tags=["Repositories"])


@router.post("/submit")
async def submit_repository(data: RepoSubmitRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Submit a GitHub repository for analysis."""
    db = get_db()
    github_service = GitHubService()

    try:
        # Fetch repo info from GitHub
        repo_info = await github_service.get_repo_info(data.url)

        # Create repository record
        repo_record = {
            "user_id": current_user["id"],
            "name": repo_info.get("name", ""),
            "url": data.url,
            "description": repo_info.get("description", ""),
            "language": repo_info.get("language", ""),
            "default_branch": repo_info.get("default_branch", data.branch),
        }

        result = db.table("repositories").insert(repo_record).execute()
        repo_id = result.data[0]["id"]

        # Create analysis record
        analysis_record = {
            "repository_id": repo_id,
            "user_id": current_user["id"],
            "status": "queued",
        }
        analysis_result = db.table("analysis_results").insert(analysis_record).execute()
        analysis_id = analysis_result.data[0]["id"]

        # Trigger async analysis using BackgroundTasks (serverless friendly)
        background_tasks.add_task(
            run_analysis,
            analysis_id=analysis_id,
            repo_url=data.url,
            branch=data.branch or repo_info.get("default_branch", "main"),
            user_id=current_user["id"],
            repository_id=repo_id,
        )

        return {
            "repository_id": repo_id,
            "analysis_id": analysis_id,
            "status": "queued",
            "message": "Repository submitted for analysis. Check back for results."
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Submission Error: {str(e)}")
        print(error_detail)
        # Return string detail for frontend toast compatibility
        error_msg = f"Failed to submit repository: {type(e).__name__} - {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/snippet")
async def submit_snippet(data: CodeSnippetRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Submit a code snippet for analysis."""
    db = get_db()

    try:
        # Create a virtual repository record
        repo_record = {
            "user_id": current_user["id"],
            "name": f"snippet_{data.filename}",
            "description": f"Code snippet ({data.language})",
            "language": data.language,
        }
        result = db.table("repositories").insert(repo_record).execute()
        repo_id = result.data[0]["id"]

        # Create analysis record
        analysis_record = {
            "repository_id": repo_id,
            "user_id": current_user["id"],
            "status": "queued",
        }
        analysis_result = db.table("analysis_results").insert(analysis_record).execute()
        analysis_id = analysis_result.data[0]["id"]

        # Trigger snippet analysis using BackgroundTasks
        background_tasks.add_task(
            run_snippet_analysis,
            analysis_id=analysis_id,
            code=data.code,
            language=data.language,
            filename=data.filename,
            user_id=current_user["id"],
            repository_id=repo_id,
        )

        return {
            "repository_id": repo_id,
            "analysis_id": analysis_id,
            "status": "queued",
            "message": "Snippet submitted for analysis."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze snippet: {str(e)}")


@router.get("")
@router.get("/")
async def list_repositories(current_user: dict = Depends(get_current_user)):
    """List all repositories for the current user."""
    db = get_db()
    result = db.table("repositories").select("*").eq(
        "user_id", current_user["id"]
    ).order("created_at", desc=True).execute()

    return {"repositories": result.data}


@router.get("/{repo_id}")
async def get_repository(repo_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific repository."""
    db = get_db()
    result = db.table("repositories").select("*").eq("id", repo_id).eq(
        "user_id", current_user["id"]
    ).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Repository not found")

    return result.data[0]


@router.delete("/{repo_id}")
async def delete_repository(repo_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a repository and all related data."""
    db = get_db()

    # Verify ownership
    result = db.table("repositories").select("id").eq("id", repo_id).eq(
        "user_id", current_user["id"]
    ).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Repository not found")

    db.table("repositories").delete().eq("id", repo_id).execute()
    return {"message": "Repository deleted successfully"}


@router.get("/{repo_id}/insights", response_model=InsightsResponse)
async def get_repository_insights(repo_id: str, current_user: dict = Depends(get_current_user)):
    """Get the AI Insights summary, charts, and metrics for a repository."""
    db = get_db()
    
    # Verify ownership
    repo_result = db.table("repositories").select("id, name").eq("id", repo_id).eq(
        "user_id", current_user["id"]
    ).execute()
    if not repo_result.data:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    # Get latest completed analysis
    analysis = db.table("analysis_results").select("*").eq(
        "repository_id", repo_id
    ).eq("status", "completed").order("created_at", desc=True).limit(1).execute()
    
    if not analysis.data:
        raise HTTPException(status_code=404, detail="No completed analysis found for insights")
        
    latest = analysis.data[0]
    
    file_metrics = latest.get("file_metrics", [])
    total_issues = 0
    total_maintainability = 0
    total_lines = latest.get("total_lines", 1) or 1
    avg_complexity = latest.get("avg_complexity", 0)
    
    for fm in file_metrics:
        total_issues += fm.get("issues_count", 0)
        total_maintainability += fm.get("maintainability_index", 100.0)
        
    num_files = len(file_metrics)
    avg_maintainability = total_maintainability / num_files if num_files > 0 else 100.0
    
    # Heuristic duplication calculation
    duplication_percentage = min(100, max(0, (avg_complexity / 20.0) * 15.0 + (total_lines / 10000.0) * 5.0))
    
    # Compute metrics
    metrics = {
        "avg_complexity": avg_complexity,
        "total_issues": total_issues,
        "technical_debt_hours": latest.get("technical_debt_hours", 0),
        "bug_density": round((total_issues / total_lines) * 1000, 2),
        "maintainability_index": round(avg_maintainability, 2),
        "duplication_percentage": round(duplication_percentage, 2)
    }
    
    # Determine summary dynamically
    issues = []
    recommendations = []
    
    if metrics["avg_complexity"] > 15:
        issues.append("high cyclomatic complexity")
        recommendations.append("Refactor extremely large or deeply nested functions.")
    if metrics["bug_density"] > 10:
        issues.append("high bug density")
        recommendations.append("Prioritize fixing existing bugs and improve test coverage.")
    if metrics["technical_debt_hours"] > 20:
        issues.append("significant technical debt")
        recommendations.append("Allocate time to address tech debt bottlenecks.")
    if metrics["duplication_percentage"] > 10:
        issues.append("notable code duplication")
        recommendations.append("Abstract repeating logic into shared utilities.")
    if metrics["maintainability_index"] < 60:
        issues.append("poor maintainability")
        recommendations.append("Enhance modularization across components.")
        
    ai_summary = "The repository is in good health overall."
    if issues:
        ai_summary = f"The repository shows {', '.join(issues)} in core modules, indicating potential maintainability risks. Addressing these areas can significantly improve code quality."
        
    if not recommendations:
        recommendations.append("Keep up the good coding standards!")
    
    # Get bug distribution for pie chart (stubbed from risk level for simplicity if bugs table is massive)
    # Fetch risk distribution for this particular analysis (i.e. number of hotspot files in each category)
    hotspots = latest.get("hotspot_files", [])
    charts = {
        "risk_distribution": hotspots,  # Can process further on frontend
        "complexity_trend": [], 
        "language_distribution": latest.get("language_breakdown", {})
    }
    
    # Get complexity trend (last 10 analyses)
    history = db.table("analysis_results").select("created_at, avg_complexity").eq(
        "repository_id", repo_id
    ).eq("status", "completed").order("created_at", desc=False).limit(10).execute()
    if history.data:
        charts["complexity_trend"] = [{"date": h["created_at"], "complexity": h["avg_complexity"]} for h in history.data]

    return InsightsResponse(
        repository_id=repo_id,
        health_score=latest.get("risk_score", 100),  # the score is 0-100 where higher is better now
        risk_level=latest.get("risk_level", "low"),
        metrics=metrics,
        ai_summary=ai_summary,
        charts=charts,
        recommendations=recommendations,
        created_at=latest.get("completed_at", "")
    )

