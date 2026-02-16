from __future__ import annotations

"""Utilities to expose Git metadata for logging and reporting (Jenkins-friendly)."""

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
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    out = result.stdout.strip()
    return out or None


def _normalize_jenkins_branch(branch: str | None) -> str | None:
    """Normalize common Jenkins branch formats like 'origin/main' -> 'main'."""
    if not branch:
        return None
    b = branch.strip()
    # Typical formats: "origin/main", "refs/remotes/origin/main"
    for prefix in ("refs/remotes/origin/", "origin/"):
        if b.startswith(prefix):
            b = b[len(prefix):]
    return b or None


def get_git_metadata() -> GitMetadata:
    """Gather commit, branch, and user info from Jenkins env or git tooling."""

    commit = os.getenv("GIT_COMMIT") or _git(["git", "rev-parse", "HEAD"])

    branch_env = os.getenv("GIT_BRANCH") or os.getenv("BRANCH_NAME")
    branch = _normalize_jenkins_branch(branch_env) or _git(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    )

    # User/email: available only if Jenkins is configured to expose them (e.g. Build User Vars Plugin)
    user = os.getenv("BUILD_USER") or os.getenv("BUILD_USER_ID") or _git(
        ["git", "config", "--get", "user.name"]
    )
    email = os.getenv("BUILD_USER_EMAIL") or _git(["git", "config", "--get", "user.email"])

    return GitMetadata(commit=commit, branch=branch, user=user, email=email)
