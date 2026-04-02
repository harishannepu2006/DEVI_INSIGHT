"""Bug detection engine — AST parsing and rule-based detection."""
import ast
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BugDetector:
    """Detect potential bugs using AST parsing and rule-based checks."""

    def detect_bugs(self, files: list[dict]) -> list[dict]:
        """Detect bugs across all files."""
        all_bugs = []

        for file_info in files:
            language = file_info.get("language", "unknown")
            content = file_info.get("content", "")
            path = file_info.get("path", "unknown")

            if language == "python":
                bugs = self._detect_python_bugs(content, path)
            elif language in ("javascript", "typescript"):
                bugs = self._detect_js_bugs(content, path)
            else:
                bugs = self._detect_generic_bugs(content, path)

            all_bugs.extend(bugs)

        return all_bugs

    def _detect_python_bugs(self, code: str, file_path: str) -> list[dict]:
        """Detect Python-specific bugs using AST parsing."""
        bugs = []

        # AST-based detection
        try:
            tree = ast.parse(code)
            bugs.extend(self._ast_bare_except(tree, code, file_path))
            bugs.extend(self._ast_unused_variables(tree, code, file_path))
            bugs.extend(self._ast_mutable_defaults(tree, code, file_path))
            bugs.extend(self._ast_return_in_init(tree, code, file_path))
            bugs.extend(self._ast_unreachable_code(tree, code, file_path))
        except SyntaxError as e:
            bugs.append({
                "file_path": file_path,
                "line_number": e.lineno or 1,
                "bug_type": "syntax_error",
                "severity": "critical",
                "title": "Syntax Error",
                "description": f"Syntax error in file: {e.msg}",
                "buggy_code": self._get_lines(code, e.lineno or 1, 3),
                "fixed_code": "",
                "explanation": f"This file has a syntax error at line {e.lineno}: {e.msg}. Fix the syntax to make the file parseable.",
                "category": "error",
            })

        # Rule-based detection
        bugs.extend(self._rule_sql_injection(code, file_path))
        bugs.extend(self._rule_hardcoded_secrets(code, file_path))
        bugs.extend(self._rule_eval_usage(code, file_path))
        bugs.extend(self._rule_os_command_injection(code, file_path))

        return bugs

    def _detect_js_bugs(self, code: str, file_path: str) -> list[dict]:
        """Detect JavaScript/TypeScript bugs using rule-based checks."""
        bugs = []

        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # == null check (should be === null || === undefined)
            if re.search(r'==\s*null\b', stripped) and '===' not in stripped:
                bugs.append({
                    "file_path": file_path,
                    "line_number": i,
                    "bug_type": "loose_null_check",
                    "severity": "medium",
                    "title": "Loose null comparison",
                    "description": "Using == null can lead to unexpected behavior",
                    "buggy_code": stripped,
                    "fixed_code": stripped.replace("== null", "=== null || value === undefined"),
                    "explanation": "Use strict equality (=== null) to avoid type coercion. == null matches both null and undefined, which might be unintentional.",
                    "category": "type_safety",
                })

            # Async function without await
            # (simplified check)
            if 'async ' in stripped and '=>' in stripped and 'await' not in stripped:
                # Check if it's a simple async arrow function without await
                bugs.append({
                    "file_path": file_path,
                    "line_number": i,
                    "bug_type": "unnecessary_async",
                    "severity": "low",
                    "title": "Async function without await",
                    "description": "Async function doesn't use await",
                    "buggy_code": stripped,
                    "fixed_code": stripped.replace("async ", ""),
                    "explanation": "This function is marked as async but doesn't use await. Remove the async keyword unless you plan to add await later.",
                    "category": "performance",
                })

            # innerHTML XSS risk
            if '.innerHTML' in stripped and ('=' in stripped):
                bugs.append({
                    "file_path": file_path,
                    "line_number": i,
                    "bug_type": "xss_risk",
                    "severity": "high",
                    "title": "Potential XSS vulnerability",
                    "description": "Direct innerHTML assignment can lead to XSS attacks",
                    "buggy_code": stripped,
                    "fixed_code": stripped.replace(".innerHTML", ".textContent"),
                    "explanation": "Using innerHTML with untrusted data can allow XSS attacks. Use textContent for text-only content, or sanitize HTML before inserting.",
                    "category": "security",
                })

            # Missing error handling in promises
            if '.then(' in stripped and '.catch(' not in stripped and 'await' not in stripped:
                bugs.append({
                    "file_path": file_path,
                    "line_number": i,
                    "bug_type": "unhandled_promise",
                    "severity": "medium",
                    "title": "Unhandled promise rejection",
                    "description": "Promise chain without .catch() handler",
                    "buggy_code": stripped,
                    "fixed_code": stripped.rstrip(';)') + ".catch(err => console.error(err));",
                    "explanation": "Unhandled promise rejections can crash your application. Always add a .catch() handler or use try/catch with await.",
                    "category": "error_handling",
                })

        # General rule-based checks
        bugs.extend(self._rule_hardcoded_secrets(code, file_path))
        bugs.extend(self._rule_sql_injection(code, file_path))

        return bugs

    def _detect_generic_bugs(self, code: str, file_path: str) -> list[dict]:
        """Detect generic bugs for any language."""
        bugs = []
        bugs.extend(self._rule_hardcoded_secrets(code, file_path))
        bugs.extend(self._rule_sql_injection(code, file_path))
        return bugs

    # ---- AST-based Python checks ----

    def _ast_bare_except(self, tree: ast.AST, code: str, file_path: str) -> list[dict]:
        bugs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                bugs.append({
                    "file_path": file_path,
                    "line_number": node.lineno,
                    "bug_type": "bare_except",
                    "severity": "high",
                    "title": "Bare except clause",
                    "description": "Catches all exceptions including SystemExit and KeyboardInterrupt",
                    "buggy_code": self._get_lines(code, node.lineno, 2),
                    "fixed_code": self._get_lines(code, node.lineno, 2).replace("except:", "except Exception:"),
                    "explanation": "Bare except clauses catch ALL exceptions, including SystemExit and KeyboardInterrupt. Use 'except Exception:' instead to only catch standard exceptions.",
                    "category": "error_handling",
                })
        return bugs

    def _ast_unused_variables(self, tree: ast.AST, code: str, file_path: str) -> list[dict]:
        bugs = []
        # Find simple assignments where variable is never used again
        assigned = {}
        used = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id.startswith('_'):
                            continue
                        assigned[target.id] = node.lineno
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)

        for var, lineno in assigned.items():
            if var not in used and not var.startswith('_'):
                bugs.append({
                    "file_path": file_path,
                    "line_number": lineno,
                    "bug_type": "unused_variable",
                    "severity": "low",
                    "title": f"Possibly unused variable: '{var}'",
                    "description": f"Variable '{var}' is assigned but may not be used",
                    "buggy_code": self._get_lines(code, lineno, 1),
                    "fixed_code": f"# Remove or use variable '{var}'",
                    "explanation": f"The variable '{var}' appears to be assigned but never read. This may indicate dead code or a missing reference.",
                    "category": "code_quality",
                })
        return bugs

    def _ast_mutable_defaults(self, tree: ast.AST, code: str, file_path: str) -> list[dict]:
        bugs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        bugs.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "bug_type": "mutable_default",
                            "severity": "high",
                            "title": f"Mutable default argument in '{node.name}'",
                            "description": "Mutable default arguments are shared between calls",
                            "buggy_code": self._get_lines(code, node.lineno, 1),
                            "fixed_code": f"# Use None as default and create mutable object inside function body",
                            "explanation": "Mutable default arguments (lists, dicts, sets) in Python are created once and shared across all calls. Use None as default and create the mutable object inside the function body.",
                            "category": "bug",
                        })
        return bugs

    def _ast_return_in_init(self, tree: ast.AST, code: str, file_path: str) -> list[dict]:
        bugs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        bugs.append({
                            "file_path": file_path,
                            "line_number": child.lineno,
                            "bug_type": "return_in_init",
                            "severity": "high",
                            "title": "Non-None return in __init__",
                            "description": "__init__ should not return a value",
                            "buggy_code": self._get_lines(code, child.lineno, 1),
                            "fixed_code": "        return  # __init__ should not return a value",
                            "explanation": "The __init__ method should not return any value. It initializes the object in-place. Returning a value from __init__ will raise a TypeError.",
                            "category": "bug",
                        })
        return bugs

    def _ast_unreachable_code(self, tree: ast.AST, code: str, file_path: str) -> list[dict]:
        bugs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                for i, stmt in enumerate(body):
                    if isinstance(stmt, ast.Return) and i < len(body) - 1:
                        next_stmt = body[i + 1]
                        bugs.append({
                            "file_path": file_path,
                            "line_number": next_stmt.lineno,
                            "bug_type": "unreachable_code",
                            "severity": "medium",
                            "title": f"Unreachable code after return in '{node.name}'",
                            "description": "Code after a return statement will never execute",
                            "buggy_code": self._get_lines(code, next_stmt.lineno, 2),
                            "fixed_code": "# Remove unreachable code or move before return statement",
                            "explanation": "Code placed after a return statement in the same block will never be executed. Either remove it or move it before the return.",
                            "category": "dead_code",
                        })
                        break
        return bugs

    # ---- Rule-based checks (any language) ----

    def _rule_sql_injection(self, code: str, file_path: str) -> list[dict]:
        bugs = []
        patterns = [
            (r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP).*\{.*\}', "f-string SQL query"),
            (r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP).*["\']\s*%\s*\(', "%-format SQL query"),
            (r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP).*["\']\s*\+\s*', "concatenated SQL query"),
            (r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP).*["\'].*\.format\(', ".format() SQL query"),
        ]

        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, desc in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    bugs.append({
                        "file_path": file_path,
                        "line_number": i,
                        "bug_type": "sql_injection",
                        "severity": "critical",
                        "title": "Potential SQL Injection",
                        "description": f"SQL query built using {desc}",
                        "buggy_code": line.strip(),
                        "fixed_code": "# Use parameterized queries instead",
                        "explanation": "Building SQL queries with string formatting is vulnerable to SQL injection. Use parameterized queries or an ORM instead.",
                        "category": "security",
                    })
                    break
        return bugs

    def _rule_hardcoded_secrets(self, code: str, file_path: str) -> list[dict]:
        bugs = []
        patterns = [
            (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', "hardcoded password"),
            (r'(?:api_key|apikey|api_secret)\s*=\s*["\'][^"\']{8,}["\']', "hardcoded API key"),
            (r'(?:secret_key|secret)\s*=\s*["\'][^"\']{8,}["\']', "hardcoded secret"),
            (r'(?:token)\s*=\s*["\'][^"\']{10,}["\']', "hardcoded token"),
        ]

        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            for pattern, desc in patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    bugs.append({
                        "file_path": file_path,
                        "line_number": i,
                        "bug_type": "hardcoded_secret",
                        "severity": "critical",
                        "title": f"Hardcoded Credential: {desc}",
                        "description": f"Found {desc} in source code",
                        "buggy_code": stripped,
                        "fixed_code": "# Use environment variables or a secrets manager",
                        "explanation": f"Hardcoded credentials ({desc}) in source code are a security risk. Use environment variables, .env files, or a secrets manager instead.",
                        "category": "security",
                    })
                    break
        return bugs

    def _rule_eval_usage(self, code: str, file_path: str) -> list[dict]:
        bugs = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if re.search(r'\beval\s*\(', stripped):
                bugs.append({
                    "file_path": file_path,
                    "line_number": i,
                    "bug_type": "eval_usage",
                    "severity": "critical",
                    "title": "Use of eval()",
                    "description": "eval() executes arbitrary code and is a security risk",
                    "buggy_code": stripped,
                    "fixed_code": "# Use ast.literal_eval() for safe evaluation, or refactor without eval",
                    "explanation": "eval() can execute arbitrary code, making it a severe security risk. Use ast.literal_eval() for safe parsing of Python literals, or find an alternative approach.",
                    "category": "security",
                })

            if re.search(r'\bexec\s*\(', stripped):
                bugs.append({
                    "file_path": file_path,
                    "line_number": i,
                    "bug_type": "exec_usage",
                    "severity": "critical",
                    "title": "Use of exec()",
                    "description": "exec() executes arbitrary code and is a security risk",
                    "buggy_code": stripped,
                    "fixed_code": "# Refactor to avoid exec()",
                    "explanation": "exec() can execute arbitrary Python code, which is a severe security risk. Refactor to use safer alternatives.",
                    "category": "security",
                })
        return bugs

    def _rule_os_command_injection(self, code: str, file_path: str) -> list[dict]:
        bugs = []
        patterns = [
            (r'os\.system\s*\(', "os.system()"),
            (r'subprocess\.call\s*\(\s*["\']', "subprocess with shell string"),
            (r'subprocess\.\w+\(.*shell\s*=\s*True', "subprocess with shell=True"),
        ]

        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            for pattern, desc in patterns:
                if re.search(pattern, line):
                    bugs.append({
                        "file_path": file_path,
                        "line_number": i,
                        "bug_type": "command_injection",
                        "severity": "high",
                        "title": f"Potential command injection via {desc}",
                        "description": f"Using {desc} with user input can lead to command injection",
                        "buggy_code": line.strip(),
                        "fixed_code": "# Use subprocess.run() with a list of arguments and shell=False",
                        "explanation": f"{desc} can be vulnerable to command injection if used with unsanitized input. Use subprocess.run() with a list of arguments and shell=False for safer command execution.",
                        "category": "security",
                    })
                    break
        return bugs

    # ---- Helpers ----

    def _get_lines(self, code: str, line_num: int, count: int = 1) -> str:
        """Get a range of lines from code."""
        lines = code.split('\n')
        start = max(0, line_num - 1)
        end = min(len(lines), start + count)
        return '\n'.join(lines[start:end])
