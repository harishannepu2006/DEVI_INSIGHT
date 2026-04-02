"""Reports router — generate and download reports."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from app.middleware.auth_middleware import get_current_user, verify_jwt_token
from app.utils.supabase_client import get_db
from app.services.report_service import ReportService
from app.models.schemas import ReportGenerateRequest

router = APIRouter(tags=["Reports"])


@router.post("/generate")
async def generate_report(data: ReportGenerateRequest, current_user: dict = Depends(get_current_user)):
    """Generate a report for an analysis."""
    db = get_db()

    # Get analysis
    analysis = db.table("analysis_results").select("*").eq(
        "id", data.analysis_id
    ).eq("user_id", current_user["id"]).execute()

    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_data = analysis.data[0]

    # Get bugs and insights
    bugs = db.table("bugs").select("*").eq("analysis_id", data.analysis_id).execute()
    insights = db.table("insights").select("*").eq("analysis_id", data.analysis_id).execute()

    # Generate report
    report_service = ReportService()
    report_bytes = report_service.generate_report(
        analysis=analysis_data,
        bugs=bugs.data or [],
        insights=insights.data or [],
        report_type=data.report_type.value,
        format=data.format.value,
    )

    # Store report record
    report_record = {
        "analysis_id": data.analysis_id,
        "user_id": current_user["id"],
        "report_type": data.report_type.value,
        "format": data.format.value,
    }
    result = db.table("reports").insert(report_record).execute()

    return {
        "status": "success",
        "report_id": result.data[0]["id"],
        "message": "Report generated successfully"
    }


@router.get("/download/{report_id}/{filename}")
@router.get("/download/{report_id}")
async def download_report(report_id: str, filename: str = None, current_user: dict = Depends(get_current_user)):
    """Download an existing report by ID."""
    db = get_db()
    
    # Get report record
    report = db.table("reports").select("*").eq("id", report_id).eq(
        "user_id", current_user["id"]
    ).execute()
    
    if not report.data:
        raise HTTPException(status_code=404, detail="Report record not found")
        
    report_record = report.data[0]
    analysis_id = report_record["analysis_id"]
    format = report_record["format"]
    report_type = report_record["report_type"]
    
    # Get analysis and bugs to regenerate (or we could store the bytes in Supabase storage, 
    # but for now we regenerate to save storage costs/simplicity)
    analysis = db.table("analysis_results").select("*").eq("id", analysis_id).execute()
    bugs = db.table("bugs").select("*").eq("analysis_id", analysis_id).execute()
    insights = db.table("insights").select("*").eq("analysis_id", analysis_id).execute()
    
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis data for report not found")
        
    report_service = ReportService()
    report_bytes = report_service.generate_report(
        analysis=analysis.data[0],
        bugs=bugs.data or [],
        insights=insights.data or [],
        report_type=report_type,
        format=format,
    )
    
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "json": "application/json",
    }
    filename = f"devinsight_report_{report_type}.{format}"
    
    return Response(
        content=report_bytes,
        media_type=content_types.get(format, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*="UTF-8\'\'{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@router.get("/")
async def list_reports(current_user: dict = Depends(get_current_user)):
    """List all reports for the current user."""
    db = get_db()
    result = db.table("reports").select("*").eq(
        "user_id", current_user["id"]
    ).order("created_at", desc=True).execute()

    return {"reports": result.data}
