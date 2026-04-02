-- DevInsight Database Schema for Supabase
-- Run this in the Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CLEAN UP EXISTING OBJECTS (safe re-run)
-- Drop tables in reverse dependency order
-- ============================================
DROP TABLE IF EXISTS monitoring_config CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS insights CASCADE;
DROP TABLE IF EXISTS bugs CASCADE;
DROP TABLE IF EXISTS analysis_results CASCADE;
DROP TABLE IF EXISTS repositories CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop existing trigger function if exists
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    provider TEXT DEFAULT 'google',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- REPOSITORIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    url TEXT,
    description TEXT,
    language TEXT,
    default_branch TEXT DEFAULT 'main',
    is_monitoring_enabled BOOLEAN DEFAULT FALSE,
    monitoring_interval_hours INTEGER DEFAULT 24,
    last_monitored_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_repositories_user_id ON repositories(user_id);

-- ============================================
-- ANALYSIS RESULTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    commit_sha TEXT,
    total_files INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    avg_complexity FLOAT DEFAULT 0,
    max_complexity FLOAT DEFAULT 0,
    technical_debt_hours FLOAT DEFAULT 0,
    risk_level TEXT DEFAULT 'low' CHECK (risk_level IN ('critical', 'high', 'medium', 'low')),
    risk_score FLOAT DEFAULT 0,
    file_metrics JSONB DEFAULT '[]'::jsonb,
    language_breakdown JSONB DEFAULT '{}'::jsonb,
    hotspot_files JSONB DEFAULT '[]'::jsonb,
    summary TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT
);

CREATE INDEX idx_analysis_results_repo ON analysis_results(repository_id);
CREATE INDEX idx_analysis_results_user ON analysis_results(user_id);
CREATE INDEX idx_analysis_results_status ON analysis_results(status);

-- ============================================
-- BUGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS bugs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    end_line_number INTEGER,
    bug_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    title TEXT NOT NULL,
    description TEXT,
    buggy_code TEXT,
    fixed_code TEXT,
    explanation TEXT,
    category TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bugs_analysis ON bugs(analysis_id);
CREATE INDEX idx_bugs_repo ON bugs(repository_id);
CREATE INDEX idx_bugs_severity ON bugs(severity);

-- ============================================
-- INSIGHTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('suggestion', 'refactor', 'performance', 'security', 'maintainability')),
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT,
    recommendation TEXT,
    estimated_effort TEXT,
    code_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_insights_analysis ON insights(analysis_id);
CREATE INDEX idx_insights_repo ON insights(repository_id);

-- ============================================
-- REPORTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL CHECK (report_type IN ('full', 'bugs_only', 'insights_only', 'comparison')),
    format TEXT NOT NULL CHECK (format IN ('pdf', 'docx', 'json')),
    file_url TEXT,
    file_data JSONB,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_analysis ON reports(analysis_id);
CREATE INDEX idx_reports_user ON reports(user_id);

-- ============================================
-- CHAT MESSAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bug_id UUID NOT NULL REFERENCES bugs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_bug ON chat_messages(bug_id);

-- ============================================
-- MONITORING CONFIG TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS monitoring_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID UNIQUE NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    interval_hours INTEGER DEFAULT 24,
    last_commit_sha TEXT,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE bugs ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring_config ENABLE ROW LEVEL SECURITY;

-- Users can read their own data
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (true);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (true);

-- Service role has full access (used by backend)
CREATE POLICY "Service role full access repositories" ON repositories FOR ALL USING (true);
CREATE POLICY "Service role full access analysis" ON analysis_results FOR ALL USING (true);
CREATE POLICY "Service role full access bugs" ON bugs FOR ALL USING (true);
CREATE POLICY "Service role full access insights" ON insights FOR ALL USING (true);
CREATE POLICY "Service role full access reports" ON reports FOR ALL USING (true);
CREATE POLICY "Service role full access chat" ON chat_messages FOR ALL USING (true);
CREATE POLICY "Service role full access monitoring" ON monitoring_config FOR ALL USING (true);

-- ============================================
-- UPDATED_AT TRIGGER FUNCTION
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitoring_config_updated_at BEFORE UPDATE ON monitoring_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
