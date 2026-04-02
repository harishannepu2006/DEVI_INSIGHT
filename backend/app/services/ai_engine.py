"""AI Insights Engine — heuristic analysis with LLM-ready templates."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AIEngine:
    """AI-powered code analysis and insights generation.

    Currently uses rule-based heuristic analysis.
    Ready for LLM integration — just implement the _call_llm() method.
    """

    # ---- Prompt Templates (LLM-ready) ----
    INSIGHT_PROMPT = """Analyze the following code metrics and provide actionable insights:

Repository: {repo_name}
Total Files: {total_files}
Total Lines: {total_lines}
Average Complexity: {avg_complexity}
Max Complexity: {max_complexity}
Technical Debt: {debt_hours} hours
Risk Level: {risk_level}
Hotspot Files: {hotspots}

Provide:
1. Top 3 actionable suggestions for improvement
2. Refactoring strategies for hotspot files
3. Performance optimization opportunities
4. Security concerns if any

Format as structured JSON with keys: suggestions, refactoring, performance, security
"""

    BUG_EXPLANATION_PROMPT = """Explain this bug to a developer:

File: {file_path}
Bug Type: {bug_type}
Severity: {severity}

Buggy Code:
```
{buggy_code}
```

Fixed Code:
```
{fixed_code}
```

Provide:
1. Clear explanation of what's wrong
2. Why the fix works
3. How to prevent this in the future
"""

    CHAT_PROMPT = """You are an AI code assistant. A developer is asking about a specific bug.

Context:
- File: {file_path}
- Bug: {bug_title}
- Severity: {severity}
- Buggy Code: {buggy_code}
- Fixed Code: {fixed_code}
- Explanation: {explanation}

Chat History:
{chat_history}

Developer's Question: {question}

Provide a helpful, concise response.
"""

    def generate_insights(self, analysis_result: dict, repo_name: str = "") -> list[dict]:
        """Generate AI insights from analysis results."""
        insights = []

        # Complexity insights
        insights.extend(self._complexity_insights(analysis_result))

        # Technical debt insights
        insights.extend(self._debt_insights(analysis_result))

        # Hotspot insights
        insights.extend(self._hotspot_insights(analysis_result))

        # Security insights (from bug data if available)
        insights.extend(self._security_insights(analysis_result))

        # Architecture insights
        insights.extend(self._architecture_insights(analysis_result))

        return insights

    def generate_bug_chat_response(self, bug: dict, question: str, chat_history: list = None) -> str:
        """Generate a chat response for a bug-specific question."""
        if chat_history is None:
            chat_history = []

        # Context-aware response generation (heuristic)
        question_lower = question.lower()

        if any(w in question_lower for w in ['explain', 'what', 'why', 'how']):
            return self._explain_bug(bug, question)
        elif any(w in question_lower for w in ['fix', 'solve', 'resolve', 'patch']):
            return self._suggest_fix(bug, question)
        elif any(w in question_lower for w in ['prevent', 'avoid', 'stop']):
            return self._prevention_advice(bug, question)
        elif any(w in question_lower for w in ['impact', 'severity', 'serious', 'dangerous']):
            return self._impact_analysis(bug, question)
        else:
            return self._general_response(bug, question)

    # ---- Insight Generators ----

    def _complexity_insights(self, result: dict) -> list[dict]:
        insights = []
        avg = result.get("avg_complexity", 0)
        max_c = result.get("max_complexity", 0)

        if avg > 15:
            insights.append({
                "insight_type": "refactor",
                "severity": "high",
                "title": "High Average Complexity",
                "description": f"The average cyclomatic complexity is {avg:.1f}, which is above the recommended threshold of 10. This indicates the codebase is difficult to test and maintain.",
                "recommendation": "Apply the Extract Method refactoring pattern to break complex functions into smaller, focused units. Target functions with complexity > 10 first.",
                "estimated_effort": f"{max(1, int(avg - 10))} hours",
            })
        elif avg > 10:
            insights.append({
                "insight_type": "suggestion",
                "severity": "medium",
                "title": "Moderate Complexity Detected",
                "description": f"Average complexity is {avg:.1f}. While not critical, reducing it below 10 would improve maintainability.",
                "recommendation": "Review the most complex functions and consider splitting them. Use guard clauses to reduce nesting.",
                "estimated_effort": "2-4 hours",
            })

        if max_c > 30:
            insights.append({
                "insight_type": "refactor",
                "severity": "critical",
                "title": "Extremely Complex Function Detected",
                "description": f"The maximum cyclomatic complexity is {max_c:.1f}. Functions with complexity > 30 are nearly impossible to test thoroughly.",
                "recommendation": "This function urgently needs refactoring. Consider the Strategy pattern, State pattern, or breaking it into a chain of smaller functions.",
                "estimated_effort": "4-8 hours",
            })

        return insights

    def _debt_insights(self, result: dict) -> list[dict]:
        insights = []
        debt = result.get("technical_debt_hours", 0)

        if debt > 40:
            insights.append({
                "insight_type": "maintainability",
                "severity": "critical",
                "title": "Significant Technical Debt Accumulated",
                "description": f"Estimated technical debt is {debt:.1f} hours. This level of debt will slow development velocity significantly.",
                "recommendation": "Allocate 20% of sprint capacity to debt reduction. Prioritize security-related issues first, then complexity hotspots.",
                "estimated_effort": f"{debt:.0f} hours total",
            })
        elif debt > 16:
            insights.append({
                "insight_type": "maintainability",
                "severity": "high",
                "title": "Technical Debt Growing",
                "description": f"Technical debt is estimated at {debt:.1f} hours. Address it before it becomes unmanageable.",
                "recommendation": "Schedule a focused refactoring sprint. Start with the top 5 hotspot files.",
                "estimated_effort": f"{debt:.0f} hours total",
            })
        elif debt > 4:
            insights.append({
                "insight_type": "suggestion",
                "severity": "medium",
                "title": "Minor Technical Debt Present",
                "description": f"Technical debt is approximately {debt:.1f} hours. Keep it in check with regular cleanup.",
                "recommendation": "Address code smells during regular development. Follow the Boy Scout Rule: leave code cleaner than you found it.",
                "estimated_effort": f"{debt:.0f} hours total",
            })

        return insights

    def _hotspot_insights(self, result: dict) -> list[dict]:
        insights = []
        hotspots = result.get("hotspot_files", [])

        if len(hotspots) > 5:
            files_list = ", ".join(h["file_path"] for h in hotspots[:5])
            insights.append({
                "insight_type": "refactor",
                "severity": "high",
                "title": f"{len(hotspots)} Hotspot Files Identified",
                "description": f"Multiple files have high complexity and risk. Top hotspots: {files_list}",
                "recommendation": "Focus refactoring efforts on these files. Consider splitting large modules and extracting shared logic into utilities.",
                "estimated_effort": f"{len(hotspots) * 2} hours",
            })
        elif len(hotspots) > 0:
            for hotspot in hotspots[:3]:
                insights.append({
                    "insight_type": "refactor",
                    "severity": "medium",
                    "title": f"Hotspot: {hotspot['file_path']}",
                    "description": f"Complexity: {hotspot['complexity']:.1f}, Risk: {hotspot['risk_level']}, Issues: {hotspot['issues_count']}",
                    "recommendation": f"Review and refactor {hotspot['file_path']}. Extract helper functions and reduce nesting.",
                    "estimated_effort": "1-2 hours",
                    "file_path": hotspot["file_path"],
                })

        return insights

    def _security_insights(self, result: dict) -> list[dict]:
        insights = []
        file_metrics = result.get("file_metrics", [])

        security_issues = 0
        for fm in file_metrics:
            for issue in fm.get("issues", []):
                if issue.get("type") in ("hardcoded_secret", "sql_injection", "eval_usage", "xss_risk"):
                    security_issues += 1

        if security_issues > 0:
            insights.append({
                "insight_type": "security",
                "severity": "critical",
                "title": f"{security_issues} Security Issue(s) Detected",
                "description": "Security vulnerabilities were found in the codebase including potential secrets exposure, injection risks, or unsafe code execution.",
                "recommendation": "Address all security issues immediately. Use environment variables for secrets, parameterized queries for SQL, and avoid eval/exec.",
                "estimated_effort": f"{security_issues * 0.5} hours",
            })

        return insights

    def _architecture_insights(self, result: dict) -> list[dict]:
        insights = []
        lang_breakdown = result.get("language_breakdown", {})
        total_files = result.get("total_files", 0)

        if len(lang_breakdown) > 3:
            insights.append({
                "insight_type": "maintainability",
                "severity": "medium",
                "title": "Multi-Language Codebase",
                "description": f"The repository uses {len(lang_breakdown)} different languages. This increases maintenance complexity.",
                "recommendation": "Ensure each language has proper tooling, linting, and testing. Consider consolidating where possible.",
                "estimated_effort": "Ongoing",
            })

        if total_files > 100:
            insights.append({
                "insight_type": "suggestion",
                "severity": "medium",
                "title": "Large Codebase",
                "description": f"With {total_files} files, ensure you have proper modular architecture.",
                "recommendation": "Verify the project follows a clear module structure. Consider a monorepo tool if managing multiple packages.",
                "estimated_effort": "4-8 hours for architecture review",
            })

        return insights

    # ---- Chat Response Generators ----

    def _explain_bug(self, bug: dict, question: str) -> str:
        return f"""**Bug: {bug.get('title', 'Unknown')}**

**What's Wrong:**
{bug.get('description', 'No description available.')}

**Location:** `{bug.get('file_path', 'unknown')}` at line {bug.get('line_number', '?')}

**Problematic Code:**
```
{bug.get('buggy_code', 'N/A')}
```

**Explanation:**
{bug.get('explanation', 'This is a code quality issue that should be addressed to improve reliability and maintainability.')}

**Severity:** {bug.get('severity', 'unknown').upper()} — {"This needs immediate attention." if bug.get('severity') in ('critical', 'high') else "Consider fixing this in your next refactoring session."}"""

    def _suggest_fix(self, bug: dict, question: str) -> str:
        return f"""**Suggested Fix for: {bug.get('title', 'Unknown')}**

**Current Code:**
```
{bug.get('buggy_code', 'N/A')}
```

**Fixed Code:**
```
{bug.get('fixed_code', 'N/A')}
```

**Why This Fix Works:**
{bug.get('explanation', 'The fix addresses the identified issue.')}

**Steps to Apply:**
1. Open `{bug.get('file_path', 'the file')}` at line {bug.get('line_number', '?')}
2. Replace the buggy code with the fixed version
3. Run your test suite to verify the fix
4. Consider adding a test case to prevent regression"""

    def _prevention_advice(self, bug: dict, question: str) -> str:
        category = bug.get('category', '')
        prevention = {
            'security': "Use automated security scanning (SAST), environment variables for secrets, and parameterized queries. Set up pre-commit hooks with security checks.",
            'error_handling': "Establish error handling guidelines. Always catch specific exceptions, log errors with context, and use custom exception classes.",
            'code_quality': "Set up linters (pylint/eslint), enforce code review policies, and use static analysis tools in CI/CD.",
            'performance': "Profile your code regularly, set up performance benchmarks, and monitor in production.",
            'bug': "Write unit tests covering edge cases, use type hints, and run static type checkers (mypy/TypeScript).",
            'type_safety': "Use strict typing (TypeScript strict mode, Python type hints + mypy) and avoid loose comparisons.",
        }

        advice = prevention.get(category, "Implement automated code review, linting, and comprehensive testing to catch issues early.")

        return f"""**How to Prevent: {bug.get('title', 'Unknown')}**

**Category:** {category or 'general'}

**Prevention Strategy:**
{advice}

**Recommended Tools:**
- **Linting:** pylint, eslint, flake8
- **Type Checking:** mypy, TypeScript strict mode
- **Security:** bandit (Python), npm audit (JS)
- **CI/CD:** Integrate all checks into your pipeline"""

    def _impact_analysis(self, bug: dict, question: str) -> str:
        severity = bug.get('severity', 'medium')
        impact_map = {
            'critical': "🔴 **CRITICAL** — This is a severe issue that could cause security breaches, data loss, or system crashes. Fix immediately.",
            'high': "🟠 **HIGH** — This is a significant issue that could lead to bugs in production, data integrity problems, or security vulnerabilities. Schedule a fix in the current sprint.",
            'medium': "🟡 **MEDIUM** — This is a moderate issue that affects code quality and maintainability. Plan to fix in the next sprint.",
            'low': "🟢 **LOW** — This is a minor issue that slightly affects code quality. Fix when convenient.",
        }

        return f"""**Impact Analysis: {bug.get('title', 'Unknown')}**

{impact_map.get(severity, '**UNKNOWN** severity')}

**Bug Type:** {bug.get('bug_type', 'unknown')}
**File:** `{bug.get('file_path', 'unknown')}`

**Potential Impact:**
- Could affect {"security and data integrity" if severity in ('critical', 'high') else "code maintainability and developer experience"}
- {"May be exploitable by attackers" if bug.get('category') == 'security' else "May cause unexpected behavior in edge cases"}
- {"Blocks production readiness" if severity == 'critical' else "Should be addressed before next release" if severity == 'high' else "Good to fix for code quality"}"""

    def _general_response(self, bug: dict, question: str) -> str:
        return f"""Regarding **{bug.get('title', 'this bug')}** in `{bug.get('file_path', 'the file')}`:

{bug.get('explanation', 'This is an identified code issue.')}

**Quick Summary:**
- **Type:** {bug.get('bug_type', 'unknown')}
- **Severity:** {bug.get('severity', 'unknown')}
- **Category:** {bug.get('category', 'general')}

Would you like me to:
- Explain what's wrong in more detail?
- Show you the fix?
- Discuss how to prevent this?
- Analyze the impact?

Just ask!"""
