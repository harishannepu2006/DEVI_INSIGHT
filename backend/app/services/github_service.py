"""GitHub repository service — cloning and file scanning."""
import os
import shutil
import logging
import httpx
import stat
from git import Repo
from app.config import settings

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub repositories."""

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.clone_dir = settings.CLONE_DIR
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        os.makedirs(self.clone_dir, exist_ok=True)

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Extract owner and repo name from GitHub URL, sanitizing trailing chars."""
        # Strip common trailing characters that shouldn't be part of the repo name
        url = url.rstrip("/-.").replace(".git", "")
        parts = [p for p in url.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL format: {url}")
        owner = parts[-2]
        repo = parts[-1]
        return owner, repo

    async def get_repo_info(self, url: str) -> dict:
        """Fetch repository metadata from GitHub API."""
        owner, repo = self.parse_repo_url(url)
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=self.headers)
            if response.status_code == 404:
                raise ValueError(f"Repository '{owner}/{repo}' not found. Please check the URL or ensure it's a public repository.")
            elif response.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded or access forbidden. Please check your GITHUB_TOKEN.")
            elif response.status_code != 200:
                raise ValueError(f"Failed to fetch repo info from GitHub (Status {response.status_code}).")
            return response.json()

    def clone_repo(self, url: str, branch: str = "main") -> str:
        """Clone a GitHub repository to local storage."""
        owner, repo_name = self.parse_repo_url(url)
        repo_path = os.path.join(self.clone_dir, f"{owner}_{repo_name}")

        # Clean existing clone
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, onerror=remove_readonly)

        try:
            # Add token to URL for private repos
            auth_url = url.replace("https://", f"https://{self.token}@")
            Repo.clone_from(auth_url, repo_path, branch=branch, depth=1)
            logger.info(f"Cloned {url} to {repo_path}")
            return repo_path
        except Exception as e:
            logger.error(f"Failed to clone {url}: {e}")
            raise ValueError(f"Failed to clone repository: {e}")

    def scan_files(self, repo_path: str) -> list[dict]:
        """Scan repository for supported source files."""
        files = []
        supported_ext = settings.SUPPORTED_EXTENSIONS
        max_size = settings.MAX_FILE_SIZE_KB * 1024

        for root, dirs, filenames in os.walk(repo_path):
            # Skip hidden dirs and common non-source dirs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ['node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', '.git']]

            for fname in filenames:
                ext = os.path.splitext(fname)[1]
                if ext not in supported_ext:
                    continue

                filepath = os.path.join(root, fname)
                file_size = os.path.getsize(filepath)

                if file_size > max_size:
                    continue

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    relative_path = os.path.relpath(filepath, repo_path)
                    files.append({
                        "path": relative_path.replace("\\", "/"),
                        "content": content,
                        "extension": ext,
                        "language": self._detect_language(ext),
                        "size": file_size,
                        "lines": content.count('\n') + 1,
                    })
                except Exception as e:
                    logger.warning(f"Error reading {filepath}: {e}")

        return files

    def _detect_language(self, ext: str) -> str:
        """Detect programming language from file extension."""
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
        }
        return lang_map.get(ext, "unknown")

    def cleanup_repo(self, repo_path: str):
        """Remove cloned repository from local storage."""
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, onerror=remove_readonly)
            logger.info(f"Cleaned up {repo_path}")
