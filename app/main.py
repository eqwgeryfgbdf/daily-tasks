from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import List
import pytz

from .config import AppConfig
from .github.trending import search_trending_repos, fetch_repo_details
from .github.content import GitHubContentClient
from .llm.provider import create_llm_client, RepoInfo
from .render import render_daily_markdown, render_daily_html
import os


def _build_output_path(prefix: str, timezone: str) -> str:
    tz = pytz.timezone(timezone or "UTC")
    now = datetime.now(tz)
    return f"{prefix}/{now.strftime('%Y')}/{now.strftime('%m')}/{now.strftime('%Y-%m-%d')}.md"


def main() -> None:
    cfg = AppConfig.load()
    dry_run = os.environ.get("DRY_RUN", "0") == "1"
    
    owner, repo = None, None
    if not dry_run:
        if not cfg.target_repo:
            raise RuntimeError("TARGET_REPO 未設定。請提供 owner/repo。")
        owner, repo = cfg.target_repo.split("/", 1)

    # 1) 取得當日熱門
    briefs = search_trending_repos(cfg.github_token, cfg.timezone, cfg.max_repos)
    # 2) 取得詳細資料
    details = [fetch_repo_details(cfg.github_token, b.full_name) for b in briefs]
    repo_infos: List[RepoInfo] = []
    for d in details:
        readme_excerpt = d.get("readme_excerpt")
        if readme_excerpt:
            print(f"[INFO] {d['full_name']}: README available ({len(readme_excerpt)} chars)")
        else:
            print(f"[WARN] {d['full_name']}: No README content")

        repo_infos.append(
            RepoInfo(
                full_name=d["full_name"],
                name=d.get("name") or d["full_name"].split("/")[-1],
                html_url=d.get("html_url", ""),
                description=d.get("description"),
                stars=int(d.get("stargazers_count", 0)),
                language=d.get("language"),
                homepage=d.get("homepage"),
                topics=d.get("topics", []),
                readme_excerpt=readme_excerpt,
            )
        )

    # 3) 產生介紹
    try:
        llm = create_llm_client(
            cfg.llm_provider,
            anthropic_api_key=cfg.anthropic_api_key,
            claude_model=cfg.claude_model,
            ollama_base_url=cfg.ollama_base_url,
            ollama_model=cfg.ollama_model,
        )
        summaries = llm.generate_repo_summaries(repo_infos)
    except Exception as e:
        print(f"[WARN] LLM summarize failed, use description fallback: {e}")
        summaries = [{"full_name": r.full_name, "intro_md": r.description or ""} for r in repo_infos]
    
    full_name_to_intro = {}
    name_to_intro = {}
    for s in summaries:
        fn = s.get("full_name", "")
        intro = s.get("intro_md", "")
        full_name_to_intro[fn] = intro
        # 建立 name -> intro 的映射以備容錯
        if "/" in fn:
            name_to_intro[fn.split("/")[-1]] = intro
        else:
            name_to_intro[fn] = intro

    repos_context = []
    for info in repo_infos:
        # 優先使用 full_name 匹配，失敗則嘗試 name 匹配
        intro = full_name_to_intro.get(info.full_name)
        if not intro:
            intro = name_to_intro.get(info.name)
        
        repos_context.append(
            {
                "full_name": info.full_name,
                "name": info.name,
                "html_url": info.html_url,
                "description": info.description,
                "stars": info.stars,
                "language": info.language,
                "homepage": info.homepage,
                "topics": info.topics,
                "intro_md": intro or info.description or "",
            }
        )

    # 4) 渲染 Markdown 與 HTML
    content = render_daily_markdown(timezone=cfg.timezone, repos=repos_context)
    html_content = render_daily_html(
        timezone=cfg.timezone, 
        repos=repos_context, 
        github_repo=cfg.target_repo or "owner/repo"
    )

    # 5) 推送到 GitHub 或本地輸出
    out_path = _build_output_path(cfg.path_prefix, cfg.timezone)
    if dry_run:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        out_file = os.path.join(output_dir, out_path.replace("/", "-"))
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[DRY_RUN] wrote {out_file}")
        
        out_html = os.path.join(output_dir, "index.html")
        with open(out_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[DRY_RUN] wrote {out_html}")
    else:
        client = GitHubContentClient(cfg.github_token)
        
        # Upload Markdown
        commit_message = f"chore(daily): {out_path}"
        client.put_file(
            owner=owner,
            repo=repo,
            path=out_path,
            content_bytes=content.encode("utf-8"),
            branch=cfg.target_branch,
            message=commit_message,
            author_name=cfg.commit_author_name,
            author_email=cfg.commit_author_email,
        )
        print(f"Created/updated {out_path} in {cfg.target_repo}")

        # Upload HTML
        client.put_file(
            owner=owner,
            repo=repo,
            path="index.html",
            content_bytes=html_content.encode("utf-8"),
            branch=cfg.target_branch,
            message=f"chore(web): update index.html",
            author_name=cfg.commit_author_name,
            author_email=cfg.commit_author_email,
        )
        print(f"Created/updated index.html in {cfg.target_repo}")


if __name__ == "__main__":
    main()
