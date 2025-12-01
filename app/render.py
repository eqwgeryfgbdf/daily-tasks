from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List
import os
import pytz
import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape


def _get_env() -> Environment:
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    return Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(enabled_extensions=(".html", ".xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_daily_markdown(*, timezone: str, repos: list[dict]) -> str:
    tz = pytz.timezone(timezone or "UTC")
    now = datetime.now(tz)
    date_str = now.strftime("%Y-%m-%d")

    env = _get_env()
    tpl = env.get_template("daily.md.j2")
    return tpl.render(date_str=date_str, timezone=timezone, repos=repos)


def render_daily_html(*, timezone: str, repos: list[dict], github_repo: str) -> str:
    tz = pytz.timezone(timezone or "UTC")
    now = datetime.now(tz)
    date_str = now.strftime("%Y-%m-%d")

    # Convert markdown intro to HTML
    repos_html = []
    for r in repos:
        r_copy = r.copy()
        intro_md = r.get("intro_md", "")
        # Use markdown to convert, also could add extensions if needed
        r_copy["intro_html"] = markdown.markdown(intro_md)
        repos_html.append(r_copy)

    env = _get_env()
    tpl = env.get_template("index.html.j2")
    return tpl.render(
        date_str=date_str,
        timezone=timezone,
        repos=repos_html,
        github_repo=github_repo
    )
