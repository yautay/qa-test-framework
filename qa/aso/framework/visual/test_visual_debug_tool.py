from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

import tools.visual.debug as debug_cli
from tools.visual.debug import (
    _build_release_destination_key,
    _is_access_denied_error,
    _normalize_endpoint,
    _resolve_credentials,
)

pytestmark = [pytest.mark.aso]


def test_normalize_endpoint_accepts_host_and_url() -> None:
    assert _normalize_endpoint("127.0.0.1:9000") == "127.0.0.1:9000"
    assert _normalize_endpoint("https://minio.example.com") == "minio.example.com"


@pytest.mark.parametrize(
    "raw",
    [
        "https://minio.example.com/minio",
        "https://minio.example.com?a=1",
        "ftp://minio.example.com",
        "https://user:pass@minio.example.com",
    ],
)
def test_normalize_endpoint_rejects_invalid_shapes(raw: str) -> None:
    with pytest.raises(ValueError):
        _normalize_endpoint(raw)


def test_resolve_credentials_uses_env_mode() -> None:
    args = SimpleNamespace(auth_mode="env", ask_release_credentials=False)
    access_key, secret_key = _resolve_credentials(
        args,
        env_access_key="env-user",
        env_secret_key="env-secret",
    )
    assert access_key == "env-user"
    assert secret_key == "env-secret"


def test_resolve_credentials_uses_flags_mode() -> None:
    args = SimpleNamespace(
        auth_mode="flags",
        ask_release_credentials=False,
        access_key="flag-user",
        secret_key="flag-secret",
    )
    access_key, secret_key = _resolve_credentials(
        args,
        env_access_key="env-user",
        env_secret_key="env-secret",
    )
    assert access_key == "flag-user"
    assert secret_key == "flag-secret"


def test_resolve_credentials_uses_interactive_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    args = SimpleNamespace(
        auth_mode="ask-release",
        ask_release_credentials=False,
        access_key="",
        minio_access_key="",
    )
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "release-user")
    monkeypatch.setattr("tools.visual.debug.getpass", lambda *_a, **_k: "release-secret")

    access_key, secret_key = _resolve_credentials(
        args,
        env_access_key="env-user",
        env_secret_key="env-secret",
    )
    assert access_key == "release-user"
    assert secret_key == "release-secret"


def test_build_release_destination_key_uses_prefix_and_source_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USERNAME", "tester")
    key = _build_release_destination_key(
        src_key="suite/test-ref/latest/a.png",
        scratch_prefix="_debug",
    )
    assert key.startswith("_debug/tester/")
    assert key.endswith("/suite/test-ref/latest/a.png")


def test_is_access_denied_error_matches_common_messages() -> None:
    assert _is_access_denied_error(Exception("Access Denied"))
    assert _is_access_denied_error(Exception("code: AccessDenied"))
    assert not _is_access_denied_error(Exception("NoSuchBucket"))


class _ParserStub:
    def __init__(self, args: SimpleNamespace) -> None:
        self._args = args

    def parse_args(self) -> SimpleNamespace:
        return self._args


def test_debug_main_auto_skips_release_checks_on_access_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    args = SimpleNamespace(
        endpoint=None,
        bucket=None,
        access_key=None,
        secret_key=None,
        ask_release_credentials=False,
        minio_access_key="",
        auth_mode="env",
        secure=False,
        insecure=False,
        src_key="suite/test-ref/latest/a.png",
        dst_key="suite/test-ref/v1/a.png",
        check_profile="auto",
        scratch_prefix="_debug",
        test_delete=False,
    )
    monkeypatch.setattr(debug_cli, "_build_parser", lambda: _ParserStub(args))
    monkeypatch.setattr(
        debug_cli,
        "load_env",
        lambda: SimpleNamespace(
            visual_minio_endpoint="minio.example.com",
            visual_minio_bucket="visual-baselines",
            visual_minio_access_key="readonly-user",
            visual_minio_secret_key="readonly-secret",
            visual_minio_secure=True,
        ),
    )

    class _FakeMinio:
        def __init__(self, *_a, **_k) -> None:
            pass

        def list_objects(self, *_a, **_k):
            yield SimpleNamespace(object_name="suite/test-ref/latest/a.png")

        def stat_object(self, *_a, **_k):
            return SimpleNamespace(size=1)

        def copy_object(self, *_a, **_k):
            raise Exception("S3 operation failed; code: AccessDenied")

        def remove_object(self, *_a, **_k):
            return None

    class _FakeCopySource:
        def __init__(self, *_a, **_k) -> None:
            pass

    monkeypatch.setitem(sys.modules, "minio", SimpleNamespace(Minio=_FakeMinio))
    monkeypatch.setitem(sys.modules, "minio.commonconfig", SimpleNamespace(CopySource=_FakeCopySource))

    assert debug_cli.main() == 0
