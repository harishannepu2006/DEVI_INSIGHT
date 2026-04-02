"""Pydantic models/schemas for DevInsight API."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ---- Enums ----
class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BugSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InsightType(str, Enum):
    SUGGESTION = "suggestion"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"


class ReportType(str, Enum):
    FULL = "full"
    BUGS_ONLY = "bugs_only"
    INSIGHTS_ONLY = "insights_only"
    COMPARISON = "comparison"


class ReportFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    JSON = "json"


# ---- Auth ----
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None


class AuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---- Repository ----
class RepoSubmitRequest(BaseModel):
    url: str = Field(..., description="GitHub repository URL")
    branch: Optional[str] = Field("main", description="Branch to analyze")


class CodeSnippetRequest(BaseModel):
    code: str = Field(..., description="Raw code snippet")
    language: str = Field("python", description="Programming language")
    filename: Optional[str] = Field("snippet.py", description="Virtual filename")


class RepositoryResponse(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    is_monitoring_enabled: bool = False
    created_at: Optional[str] = None


# ---- Analysis ----
class FileMetric(BaseModel):
    file_path: str
    language: str
    lines: int
    complexity: float
    risk_level: str
    issues_count: int


class AnalysisResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    total_files: int = 0
    total_lines: int = 0
    avg_complexity: float = 0
    max_complexity: float = 0
    total_issues: int = 0
    avg_maintainability: float = 100.0
    duplication_percentage: float = 0.0
    technical_debt_hours: float = 0
    risk_level: str = "low"
    risk_score: float = 0
    language_breakdown: dict = {}
    hotspot_files: list = []
    summary: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class AnalysisTriggerResponse(BaseModel):
    analysis_id: str
    status: str = "queued"
    message: str = "Analysis queued successfully"


# ---- Bugs ----
class BugResponse(BaseModel):
    id: str
    analysis_id: str
    file_path: str
    line_number: Optional[int] = None
    bug_type: str
    severity: str
    title: str
    description: Optional[str] = None
    buggy_code: Optional[str] = None
    fixed_code: Optional[str] = None
    explanation: Optional[str] = None
    category: Optional[str] = None
    is_resolved: bool = False
    created_at: Optional[str] = None


# ---- Insights ----
class InsightResponse(BaseModel):
    id: str
    analysis_id: str
    insight_type: str
    severity: str
    title: str
    description: str
    file_path: Optional[str] = None
    recommendation: Optional[str] = None
    estimated_effort: Optional[str] = None
    code_snippet: Optional[str] = None
    created_at: Optional[str] = None


# ---- Reports ----
class ReportGenerateRequest(BaseModel):
    analysis_id: str
    report_type: ReportType = ReportType.FULL
    format: ReportFormat = ReportFormat.PDF


class ReportResponse(BaseModel):
    id: str
    analysis_id: str
    report_type: str
    format: str
    file_url: Optional[str] = None
    generated_at: Optional[str] = None


# ---- Chat ----
class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    bug_id: str
    role: str
    content: str
    created_at: Optional[str] = None


# ---- Monitoring ----
class MonitoringConfigRequest(BaseModel):
    interval_hours: int = 24
    notification_enabled: bool = True


class MonitoringConfigResponse(BaseModel):
    id: str
    repository_id: str
    is_active: bool
    interval_hours: int
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None


# ---- Dashboard ----
class DashboardStats(BaseModel):
    total_repos: int = 0
    total_analyses: int = 0
    total_bugs: int = 0
    total_insights: int = 0
    avg_risk_score: float = 0
    recent_analyses: list = []
    risk_distribution: dict = {}
    language_distribution: dict = {}
    complexity_trend: list = []


# ---- Repository Insights Dashboard ----
class InsightsResponse(BaseModel):
    repository_id: str
    health_score: float = 0
    risk_level: str = "low"
    metrics: dict = {}
    ai_summary: Optional[str] = None
    charts: dict = {}
    recommendations: list[str] = []
    created_at: Optional[str] = None
