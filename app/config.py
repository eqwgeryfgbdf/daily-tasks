import os
from dataclasses import dataclass


def _get_env(key: str, default: str | None = None) -> str | None:
    value = os.environ.get(key)
    if value is not None and value != "":
        return value
    return default


@dataclass
class AppConfig:
    llm_provider: str
    anthropic_api_key: str | None
    claude_model: str
    ollama_base_url: str
    ollama_model: str
    github_token: str | None
    target_repo: str
    target_branch: str
    max_repos: int
    path_prefix: str
    timezone: str
    commit_author_name: str
    commit_author_email: str

    @staticmethod
    def load() -> "AppConfig":
        return AppConfig(
            llm_provider=_get_env("LLM_PROVIDER", "claude"),
            anthropic_api_key=_get_env("ANTHROPIC_API_KEY"),
            claude_model=_get_env("CLAUDE_MODEL", "claude-3-5-sonnet-20240620"),
            ollama_base_url=_get_env("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1"),
            ollama_model=_get_env("OLLAMA_MODEL", "llama3.1:8b-instruct"),
            github_token=_get_env("GITHUB_TOKEN"),
            target_repo=_get_env("TARGET_REPO", _get_env("GITHUB_REPOSITORY", "")) or "",
            target_branch=_get_env("TARGET_BRANCH", "main"),
            max_repos=int(_get_env("MAX_REPOS", "5")),
            path_prefix=_get_env("PATH_PREFIX", "daily"),
            timezone=_get_env("TIMEZONE", "Asia/Taipei"),
            commit_author_name=_get_env("COMMIT_AUTHOR_NAME", "DailyTasksBot"),
            commit_author_email=_get_env("COMMIT_AUTHOR_EMAIL", "bot@example.com"),
        )


