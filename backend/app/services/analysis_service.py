"""Code analysis service — static analysis, complexity, debt estimation."""
import ast
import re
import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for analyzing code quality metrics."""

    def analyze_files(self, files: list[dict]) -> dict:
        """Analyze all files and return aggregated metrics."""
        file_metrics = []
        total_lines = 0
        total_complexity = 0
        max_complexity = 0
        total_issues = 0
        total_maintainability = 0
        language_breakdown = {}
        hotspot_files = []

        for file_info in files:
            metrics = self.analyze_single_file(file_info)
            file_metrics.append(metrics)

            total_lines += metrics["lines"]
            total_complexity += metrics["complexity"]
            max_complexity = max(max_complexity, metrics["complexity"])
            total_issues += metrics["issues_count"]
            total_maintainability += metrics["maintainability_index"]

            lang = metrics["language"]
            if lang not in language_breakdown:
                language_breakdown[lang] = {"files": 0, "lines": 0}
            language_breakdown[lang]["files"] += 1
            language_breakdown[lang]["lines"] += metrics["lines"]

            # Mark high-complexity files as hotspots
            if metrics["complexity"] > 15 or metrics["risk_level"] in ("critical", "high"):
                hotspot_files.append({
                    "file_path": metrics["file_path"],
                    "complexity": metrics["complexity"],
                    "risk_level": metrics["risk_level"],
                    "issues_count": metrics["issues_count"],
                })

        num_files = len(files)
        avg_complexity = total_complexity / num_files if num_files > 0 else 0
        avg_maintainability = total_maintainability / num_files if num_files > 0 else 100.0
        
        # Estimate duplication based on average complexity and sizes as a simple placeholder heuristic
        # In a real app we would use a clone-detector like jscpd
        duplication_percentage = min(100, max(0, (avg_complexity / 20.0) * 15.0 + (total_lines / 10000.0) * 5.0))


        # Technical debt estimation (hours)
        debt_hours = self._estimate_debt(file_metrics)

        # Overall risk
        risk_score = self._calculate_risk_score(avg_complexity, max_complexity, debt_hours, num_files)
        risk_level = self._classify_risk(risk_score)

        # Sort hotspots by complexity
        hotspot_files.sort(key=lambda x: x["complexity"], reverse=True)

        return {
            "total_files": num_files,
            "total_lines": total_lines,
            "avg_complexity": round(avg_complexity, 2),
            "max_complexity": round(max_complexity, 2),
            "total_issues": total_issues,
            "avg_maintainability": round(avg_maintainability, 2),
            "duplication_percentage": round(duplication_percentage, 2),
            "technical_debt_hours": round(debt_hours, 1),
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "file_metrics": file_metrics,
            "language_breakdown": language_breakdown,
            "hotspot_files": hotspot_files[:20],
        }

    def analyze_single_file(self, file_info: dict) -> dict:
        """Analyze a single file for quality metrics."""
        content = file_info["content"]
        language = file_info["language"]
        lines = file_info["lines"]

        # Calculate cyclomatic complexity
        if language == "python":
            complexity = self._python_complexity(content)
        elif language in ("javascript", "typescript"):
            complexity = self._js_complexity(content)
        else:
            complexity = self._generic_complexity(content)

        # Count code smells
        issues = self._detect_code_smells(content, language)

        # Risk classification
        risk_level = self._file_risk_level(complexity, lines, len(issues))

        return {
            "file_path": file_info["path"],
            "language": language,
            "lines": lines,
            "complexity": round(complexity, 2),
            "risk_level": risk_level,
            "issues_count": len(issues),
            "issues": issues,
            "maintainability_index": self._maintainability_index(complexity, lines),
        }

    def _python_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity for Python code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return self._generic_complexity(code)

        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1

        return complexity

    def _js_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity for JavaScript/TypeScript."""
        complexity = 1
        patterns = [
            r'\bif\b', r'\belse\s+if\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\b\?\b', r'&&', r'\|\|',
            r'\bfunction\b', r'=>',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, code)
            complexity += len(matches)

        return complexity

    def _generic_complexity(self, code: str) -> float:
        """Generic complexity estimation based on control flow keywords."""
        complexity = 1
        keywords = ['if', 'else', 'for', 'while', 'switch', 'case',
                     'catch', 'try', 'throw', 'return', '?', '&&', '||']

        for keyword in keywords:
            complexity += code.count(f' {keyword} ') + code.count(f'\t{keyword} ')

        return complexity

    def _detect_code_smells(self, content: str, language: str) -> list[dict]:
        """Detect common code smells."""
        smells = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Long lines
            if len(line) > 120:
                smells.append({
                    "type": "long_line",
                    "line": i,
                    "message": f"Line exceeds 120 characters ({len(line)} chars)",
                    "severity": "low",
                })

            # TODO/FIXME/HACK comments
            if any(tag in stripped.upper() for tag in ['TODO', 'FIXME', 'HACK', 'XXX']):
                smells.append({
                    "type": "todo_comment",
                    "line": i,
                    "message": "Contains TODO/FIXME/HACK comment",
                    "severity": "low",
                })

            # Deep nesting (check indentation)
            indent_level = len(line) - len(line.lstrip())
            if indent_level >= 20 and stripped:  # ~5 levels
                smells.append({
                    "type": "deep_nesting",
                    "line": i,
                    "message": f"Deeply nested code (indentation: {indent_level})",
                    "severity": "medium",
                })

        # Python-specific smells
        if language == "python":
            smells.extend(self._python_smells(content))

        # JS-specific smells
        if language in ("javascript", "typescript"):
            smells.extend(self._js_smells(content))

        # Long function detection
        smells.extend(self._detect_long_functions(content, language))

        return smells

    def _python_smells(self, code: str) -> list[dict]:
        """Detect Python-specific code smells."""
        smells = []

        # Bare except
        for i, line in enumerate(code.split('\n'), 1):
            if re.match(r'\s*except\s*:', line):
                smells.append({
                    "type": "bare_except",
                    "line": i,
                    "message": "Bare except clause catches all exceptions",
                    "severity": "high",
                })

            # Star imports
            if re.match(r'from\s+\S+\s+import\s+\*', line):
                smells.append({
                    "type": "star_import",
                    "line": i,
                    "message": "Wildcard import pollutes namespace",
                    "severity": "medium",
                })

            # Mutable default arguments
            if re.match(r'.*def\s+\w+\(.*=\s*(\[|\{|\blist\().*\)', line):
                smells.append({
                    "type": "mutable_default",
                    "line": i,
                    "message": "Mutable default argument",
                    "severity": "high",
                })

        return smells

    def _js_smells(self, code: str) -> list[dict]:
        """Detect JavaScript-specific code smells."""
        smells = []

        for i, line in enumerate(code.split('\n'), 1):
            stripped = line.strip()

            # var usage
            if re.match(r'\bvar\s+', stripped):
                smells.append({
                    "type": "var_usage",
                    "line": i,
                    "message": "Use 'let' or 'const' instead of 'var'",
                    "severity": "medium",
                })

            # == instead of ===
            if '==' in stripped and '===' not in stripped and '!==' not in stripped:
                smells.append({
                    "type": "loose_equality",
                    "line": i,
                    "message": "Use strict equality (===) instead of loose equality (==)",
                    "severity": "medium",
                })

            # console.log
            if 'console.log(' in stripped:
                smells.append({
                    "type": "console_log",
                    "line": i,
                    "message": "Remove console.log in production code",
                    "severity": "low",
                })

        return smells

    def _detect_long_functions(self, content: str, language: str) -> list[dict]:
        """Detect functions that are too long."""
        smells = []

        if language == "python":
            pattern = r'def\s+(\w+)'
        elif language in ("javascript", "typescript"):
            pattern = r'(?:function\s+(\w+)|(\w+)\s*(?:=|:)\s*(?:async\s+)?(?:function|\(.*\)\s*=>))'
        else:
            return smells

        lines = content.split('\n')
        func_starts = []
        for i, line in enumerate(lines):
            matches = re.findall(pattern, line)
            if matches:
                name = matches[0] if isinstance(matches[0], str) else next(m for m in matches[0] if m)
                func_starts.append((i + 1, name))

        # Approximate function length by distance between starts
        for j in range(len(func_starts)):
            start = func_starts[j][0]
            end = func_starts[j + 1][0] if j + 1 < len(func_starts) else len(lines)
            length = end - start

            if length > 50:
                smells.append({
                    "type": "long_function",
                    "line": start,
                    "message": f"Function '{func_starts[j][1]}' is {length} lines (consider refactoring if >50)",
                    "severity": "medium",
                })

        return smells

    def _file_risk_level(self, complexity: float, lines: int, issues: int) -> str:
        """Classify file risk level."""
        score = 0
        if complexity > 30:
            score += 3
        elif complexity > 20:
            score += 2
        elif complexity > 10:
            score += 1

        if lines > 500:
            score += 2
        elif lines > 300:
            score += 1

        if issues > 10:
            score += 2
        elif issues > 5:
            score += 1

        if score >= 5:
            return "critical"
        elif score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        return "low"

    def _estimate_debt(self, file_metrics: list[dict]) -> float:
        """Estimate technical debt in hours."""
        total_hours = 0
        for fm in file_metrics:
            issue_count = fm.get("issues_count", 0)
            complexity = fm.get("complexity", 0)

            # ~15 min per issue, extra for high complexity
            hours = issue_count * 0.25
            if complexity > 20:
                hours += (complexity - 20) * 0.1
            total_hours += hours

        return total_hours

    def _calculate_risk_score(self, avg_complexity: float, max_complexity: float,
                              debt_hours: float, num_files: int) -> float:
        """Calculate overall risk score (0-100)."""
        score = 0
        score += min(avg_complexity * 2, 30)
        score += min(max_complexity * 0.5, 20)
        score += min(debt_hours * 0.5, 25)
        score += min(num_files * 0.1, 25)
        return min(score, 100)

    def _classify_risk(self, score: float) -> str:
        """Classify overall risk from score."""
        if score >= 75:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 25:
            return "medium"
        return "low"

    def _maintainability_index(self, complexity: float, lines: int) -> float:
        """Calculate maintainability index (0-100, higher is better)."""
        if lines == 0:
            return 100
        volume = lines * math.log2(max(complexity, 1))
        mi = max(0, 171 - 5.2 * math.log(max(volume, 1)) - 0.23 * complexity - 16.2 * math.log(max(lines, 1)))
        return round(min(mi * 100 / 171, 100), 1)
