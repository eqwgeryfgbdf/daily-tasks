from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List
import pytz
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


@dataclass
class RepoBrief:
    full_name: str
    name: str
    html_url: str
    description: str | None
    stargazers_count: int


def search_trending_repos(token: str | None, timezone: str, max_repos: int) -> List[RepoBrief]:
    tz = pytz.timezone(timezone or "UTC")
    since_date = (datetime.now(tz) - timedelta(days=1)).date().isoformat()
    url = f"{GITHUB_API}/search/repositories"
    params = {
        "q": f"created:>{since_date}",
        "sort": "stars",
        "order": "desc",
        "per_page": max(1, min(max_repos, 50)),
        "page": 1,
    }
    resp = requests.get(url, headers=_headers(token), params=params, timeout=30)
    resp.raise_for_status()
    items = resp.json().get("items", [])
    repos: List[RepoBrief] = []
    for item in items:
        repos.append(
            RepoBrief(
                full_name=item.get("full_name", ""),
                name=item.get("name", ""),
                html_url=item.get("html_url", ""),
                description=item.get("description"),
                stargazers_count=item.get("stargazers_count", 0),
            )
        )
    return repos


def fetch_repo_details(token: str | None, full_name: str) -> dict:
    url = f"{GITHUB_API}/repos/{full_name}"
    r = requests.get(url, headers=_headers(token), timeout=30)
    r.raise_for_status()
    repo = r.json()

    # 讀取 README 原文
    readme_text = None
    try:
        r2 = requests.get(
            f"{GITHUB_API}/repos/{full_name}/readme",
            headers={**_headers(token), "Accept": "application/vnd.github.raw"},
            timeout=30,
        )
        if r2.status_code == 200:
            readme_text = r2.text
    except Exception:
        readme_text = None

    return {
        "full_name": repo.get("full_name", full_name),
        "name": repo.get("name"),
        "html_url": repo.get("html_url"),
        "description": repo.get("description"),
        "stargazers_count": repo.get("stargazers_count", 0),
        "language": repo.get("language"),
        "homepage": repo.get("homepage"),
        "topics": repo.get("topics", []),
        "readme_excerpt": (readme_text or "")[:4000],
    }


