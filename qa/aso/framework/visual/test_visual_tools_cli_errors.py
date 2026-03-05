from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import tools.visual.promote_candidates_local as promote_cli
import tools.visual.version_baselines as version_cli

pytestmark = [pytest.mark.aso]


class _ParserStub:
    def __init__(self, args: Any) -> None:
        self._args = args

    def parse_args(self) -> Any:
        return self._args


def test_promote_candidates_local_main_returns_2_for_missing_source(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    args = SimpleNamespace(profile="test-ref", suite=[], prune_missing=False, apply=False)
    monkeypatch.setattr(promote_cli, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(promote_cli, "load_env", lambda: SimpleNamespace(visual_baseline_profile="test-ref"))

    def _raise(*_a, **_k):
        raise ValueError("no source PNG files found for profile='test-ref', version='candidates'")

    monkeypatch.setattr(promote_cli, "promote_candidates_local", _raise)

    code = promote_cli.main()
    captured = capsys.readouterr()

    assert code == 2
    assert "nothing to promote" in captured.err


def test_version_baselines_main_returns_2_for_invalid_minio_endpoint(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    args = SimpleNamespace(
        command="create",
        profile="test-ref",
        suite=[],
        from_version="latest",
        to_version="2026-03-05",
        prune_missing=False,
        with_minio=True,
        ask_release_credentials=False,
        minio_access_key="",
        apply=True,
    )
    monkeypatch.setattr(version_cli, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        version_cli,
        "load_env",
        lambda: SimpleNamespace(
            visual_baseline_profile="test-ref",
            visual_minio_access_key="readonly",
            visual_minio_secret_key="readonly-secret",
        ),
    )
    monkeypatch.setattr(version_cli, "_resolve_runtime_minio_credentials", lambda *_a, **_k: None)

    def _raise(*_a, **_k):
        raise ValueError("invalid VISUAL_MINIO_ENDPOINT: path is not allowed; use host[:port] only")

    monkeypatch.setattr(version_cli, "apply_version_copy", _raise)

    code = version_cli.main()
    captured = capsys.readouterr()

    assert code == 2
    assert "VISUAL_MINIO_ENDPOINT" in captured.err


def test_version_baselines_main_returns_1_for_other_value_errors(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    args = SimpleNamespace(
        command="create",
        profile="test-ref",
        suite=[],
        from_version="latest",
        to_version="2026-03-05",
        prune_missing=False,
        with_minio=False,
        ask_release_credentials=False,
        minio_access_key="",
        apply=True,
    )
    monkeypatch.setattr(version_cli, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(version_cli, "load_env", lambda: SimpleNamespace(visual_baseline_profile="test-ref"))
    monkeypatch.setattr(version_cli, "_resolve_runtime_minio_credentials", lambda *_a, **_k: None)

    def _raise(*_a, **_k):
        raise ValueError("boom")

    monkeypatch.setattr(version_cli, "apply_version_copy", _raise)

    code = version_cli.main()
    captured = capsys.readouterr()

    assert code == 1
    assert "error: boom" in captured.err
