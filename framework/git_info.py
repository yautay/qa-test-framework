from __future__ import annotations

"""Utilities to expose Git metadata for logging and reporting."""

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GitMetadata:
    """Basic identifiers captured from git for diagnostics."""

    commit: str | None
    branch: str | None
    user: str | None
    email: str | None


def _git(command: list[str]) -> str | None:
    """Run a git subcommand and return stdout if it succeeds."""

    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            return None
        return result.stdout.strip() or None
    except Exception:
        return None


def get_git_metadata() -> GitMetadata:
    """Gather commit, branch, and user info from the environment or git tooling."""

    commit = os.getenv("GITHUB_SHA") or _git(["git", "rev-parse", "HEAD"])
    branch = os.getenv("GITHUB_REF_NAME") or _git(["git", "branch", "--show-current"])
    user = os.getenv("GITHUB_ACTOR") or _git(["git", "config", "--get", "user.name"])
    email = os.getenv("GITHUB_ACTOR_EMAIL") or _git(["git", "config", "--get", "user.email"])
    return GitMetadata(commit=commit, branch=branch, user=user, email=email)
