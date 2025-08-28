from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List
import os
import pytz
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_daily_markdown(*, timezone: str, repos: list[dict]) -> str:
    tz = pytz.timezone(timezone or "UTC")
    now = datetime.now(tz)
    date_str = now.strftime("%Y-%m-%d")

    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(enabled_extensions=(".html", ".xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template("daily.md.j2")
    return tpl.render(date_str=date_str, timezone=timezone, repos=repos)


