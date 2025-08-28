from __future__ import annotations

import base64
from typing import Optional
import requests


GITHUB_API = "https://api.github.com"


def _headers(token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "daily-trending-bot",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class GitHubContentClient:
    def __init__(self, token: Optional[str]):
        if not token:
            raise RuntimeError("缺少 GITHUB_TOKEN。請在環境變數或 GitHub Actions Secrets 設定。")
        self.token = token

    def _get_file(self, owner: str, repo: str, path: str, ref: str) -> dict | None:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        r = requests.get(url, headers=_headers(self.token), params={"ref": ref}, timeout=30)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def put_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content_bytes: bytes,
        *,
        branch: str,
        message: str,
        author_name: str,
        author_email: str,
    ) -> dict:
        existing = self._get_file(owner, repo, path, branch)
        sha = existing.get("sha") if existing else None
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        payload = {
            "message": message,
            "content": base64.b64encode(content_bytes).decode("utf-8"),
            "branch": branch,
            "committer": {"name": author_name, "email": author_email},
        }
        if sha:
            payload["sha"] = sha
        r = requests.put(url, headers=_headers(self.token), json=payload, timeout=60)
        r.raise_for_status()
        return r.json()


