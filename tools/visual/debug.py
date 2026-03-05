from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from getpass import getpass
from pathlib import Path
from time import time
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Debug MinIO/S3 baseline permissions (list/get/put/delete)")
    parser.add_argument("--endpoint", default=None, help="MinIO endpoint (host[:port] or http(s)://host[:port])")
    parser.add_argument("--bucket", default=None, help="Bucket name")
    parser.add_argument("--access-key", default=None, help="MinIO access key")
    parser.add_argument("--secret-key", default=None, help="MinIO secret key")
    parser.add_argument(
        "--ask-release-credentials",
        action="store_true",
        help="Prompt for MinIO release credentials (access key + secret key)",
    )
    parser.add_argument(
        "--minio-access-key",
        default="",
        help="MinIO access key used with --ask-release-credentials",
    )
    parser.add_argument(
        "--auth-mode",
        choices=["env", "flags", "ask-release"],
        default="env",
        help=(
            "Credential source: env=VISUAL_MINIO_* (default), "
            "flags=--access-key/--secret-key, ask-release=interactive prompt"
        ),
    )
    parser.add_argument("--secure", action="store_true", help="Use HTTPS")
    parser.add_argument("--insecure", action="store_true", help="Use HTTP")
    parser.add_argument("--src-key", required=True, help="Source object key used for stat/copy tests")
    parser.add_argument("--dst-key", required=True, help="Destination object key used for copy test")
    parser.add_argument(
        "--check-profile",
        choices=["readonly", "release", "auto"],
        default="auto",
        help=(
            "readonly validates list/get; release validates list/get/copy/delete; "
            "auto runs release checks only when write permissions are available"
        ),
    )
    parser.add_argument(
        "--scratch-prefix",
        default="_debug",
        help="Prefix used for temporary release write check objects",
    )
    parser.add_argument(
        "--test-delete",
        action="store_true",
        help="Force explicit delete check in readonly mode as well",
    )
    return parser


def _normalize_endpoint(raw_endpoint: str) -> str:
    endpoint = str(raw_endpoint).strip()
    if not endpoint:
        raise ValueError("missing endpoint")
    parsed = urlsplit(endpoint if "://" in endpoint else f"//{endpoint}")
    if parsed.path not in {"", "/"}:
        raise ValueError("endpoint path is not allowed; use host[:port] only")
    if parsed.query or parsed.fragment:
        raise ValueError("endpoint query/fragment is not allowed")
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        raise ValueError("endpoint scheme must be http or https")
    host_port = parsed.netloc.strip()
    if not host_port:
        raise ValueError("endpoint host is missing")
    if "@" in host_port:
        raise ValueError("credentials inside endpoint are not allowed")
    return host_port


def _run_check(name: str, func, *, required_perm: str) -> bool:
    try:
        func()
        print(f"PASS  {name}")
        return True
    except Exception as exc:
        print(f"FAIL  {name}: {exc}")
        print(f"      likely missing permission: {required_perm}")
        return False


def _resolve_credentials(args, *, env_access_key: str, env_secret_key: str) -> tuple[str, str]:
    mode = str(getattr(args, "auth_mode", "env")).strip().lower()
    ask_flag = bool(getattr(args, "ask_release_credentials", False))
    if ask_flag:
        mode = "ask-release"

    if mode == "env":
        access_key = str(env_access_key).strip()
        secret_key = str(env_secret_key).strip()
        return access_key, secret_key

    if mode == "flags":
        access_key = str(getattr(args, "access_key", "") or "").strip()
        secret_key = str(getattr(args, "secret_key", "") or "").strip()
        return access_key, secret_key

    if mode != "ask-release":
        raise ValueError(f"unsupported auth mode: {mode}")

    access_key = str(getattr(args, "minio_access_key", "") or "").strip()
    if not access_key:
        access_key = str(getattr(args, "access_key", "") or "").strip()
    if not access_key:
        access_key = input("MinIO release access key: ").strip()
    if not access_key:
        raise ValueError("missing MinIO release access key")

    secret_key = getpass("MinIO release secret key: ").strip()
    if not secret_key:
        raise ValueError("missing MinIO release secret key")

    return access_key, secret_key


def _build_release_destination_key(*, src_key: str, scratch_prefix: str) -> str:
    cleaned_prefix = str(scratch_prefix).strip().strip("/")
    if not cleaned_prefix:
        raise ValueError("scratch prefix cannot be empty")
    owner = os.getenv("USERNAME") or os.getenv("USER") or "unknown-user"
    run_id = str(int(time()))
    return f"{cleaned_prefix}/{owner}/{run_id}/{src_key.lstrip('/')}"


def _is_access_denied_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "access denied" in text or "accessdenied" in text


def _mask_secret(value: str, *, mask_ratio: float = 0.8) -> str:
    raw = str(value or "")
    if not raw:
        return "<empty>"

    length = len(raw)
    mask_count = max(1, int(round(length * mask_ratio)))
    if mask_count >= length:
        mask_count = length - 1

    visible = length - mask_count
    left_visible = (visible + 1) // 2
    right_visible = visible // 2
    masked_middle = "*" * mask_count
    right_part = raw[-right_visible:] if right_visible > 0 else ""
    return f"{raw[:left_visible]}{masked_middle}{right_part}"


def main() -> int:
    args = _build_parser().parse_args()
    env = load_env()

    endpoint_raw = str(args.endpoint or env.visual_minio_endpoint).strip()
    bucket = str(args.bucket or env.visual_minio_bucket).strip()
    try:
        access_key, secret_key = _resolve_credentials(
            args,
            env_access_key=str(env.visual_minio_access_key),
            env_secret_key=str(env.visual_minio_secret_key),
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    src_key = str(args.src_key).strip()
    dst_key = str(args.dst_key).strip()

    if not bucket:
        print("error: missing bucket (--bucket or VISUAL_MINIO_BUCKET)", file=sys.stderr)
        return 2
    if not access_key or not secret_key:
        print("error: missing credentials (--access-key/--secret-key or VISUAL_MINIO_* vars)", file=sys.stderr)
        return 2
    if args.secure and args.insecure:
        print("error: use only one of --secure/--insecure", file=sys.stderr)
        return 2

    secure = env.visual_minio_secure
    if args.secure:
        secure = True
    if args.insecure:
        secure = False

    print("loaded config (env/settings)")
    print(f"env.visual_minio_endpoint={str(env.visual_minio_endpoint).strip() or '<empty>'}")
    print(f"env.visual_minio_bucket={str(env.visual_minio_bucket).strip() or '<empty>'}")
    print(f"env.visual_minio_access_key={_mask_secret(str(env.visual_minio_access_key).strip())}")
    print(f"env.visual_minio_secret_key={_mask_secret(str(env.visual_minio_secret_key).strip())}")
    print(f"env.visual_minio_secure={bool(env.visual_minio_secure)}")
    print("effective credentials")
    print(f"effective.access_key={_mask_secret(access_key)}")
    print(f"effective.secret_key={_mask_secret(secret_key)}")

    try:
        endpoint = _normalize_endpoint(endpoint_raw)
    except ValueError as exc:
        print(f"error: invalid endpoint: {exc}", file=sys.stderr)
        return 2

    print("minio debug")
    print(f"endpoint={endpoint}")
    print(f"bucket={bucket}")
    print(f"secure={secure}")
    print(f"src_key={src_key}")
    print(f"dst_key={dst_key}")
    print(f"test_delete={bool(args.test_delete)}")
    print(f"ask_release_credentials={bool(args.ask_release_credentials)}")
    print(f"auth_mode={args.auth_mode}")
    print(f"check_profile={args.check_profile}")

    try:
        from minio import Minio
        from minio.commonconfig import CopySource
    except Exception as exc:
        print(f"error: minio package is not available: {exc}", file=sys.stderr)
        return 2

    client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    checks: list[tuple[str, bool]] = []
    checks.append(
        (
            "list bucket",
            _run_check(
                "ListBucket",
                lambda: next(client.list_objects(bucket, recursive=True), None),
                required_perm="s3:ListBucket",
            ),
        )
    )
    checks.append(
        (
            "read source",
            _run_check(
                "GetObject (stat src)",
                lambda: client.stat_object(bucket, src_key),
                required_perm="s3:GetObject",
            ),
        )
    )
    profile_mode = str(args.check_profile).lower()
    should_check_release_writes = profile_mode in {"release", "auto"}
    release_dst_key = dst_key
    if should_check_release_writes:
        try:
            release_dst_key = _build_release_destination_key(src_key=src_key, scratch_prefix=str(args.scratch_prefix))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"release_dst_key={release_dst_key}")

        copy_ok = True
        try:
            client.copy_object(bucket, release_dst_key, CopySource(bucket, src_key))
            print("PASS  PutObject via copy")
        except Exception as exc:
            if profile_mode == "auto" and _is_access_denied_error(exc):
                print(f"SKIP  release checks: {exc}")
                print("      info: credentials look readonly, release checks skipped")
                copy_ok = False
                should_check_release_writes = False
            else:
                print(f"FAIL  PutObject via copy: {exc}")
                print("      likely missing permission: s3:PutObject (and s3:GetObject on src)")
                checks.append(("copy source to destination", False))
                copy_ok = False

        if copy_ok:
            checks.append(("copy source to destination", True))

    if (should_check_release_writes and profile_mode in {"release", "auto"}) or args.test_delete:
        checks.append(
            (
                "delete destination",
                _run_check(
                    "DeleteObject (dst)",
                    lambda: client.remove_object(bucket, release_dst_key),
                    required_perm="s3:DeleteObject",
                ),
            )
        )

    ok = all(passed for _, passed in checks)
    print("result=PASS" if ok else "result=FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
