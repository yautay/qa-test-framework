from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from framework.env import load_env
from framework.logger import configure_tools_logging
from tools.visual.debug_checks import run_permission_checks
from tools.visual.debug_helpers import mask_secret, normalize_endpoint, resolve_credentials


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


def main() -> int:
    log_path = configure_tools_logging("visual_debug")
    logger.debug("tools_log_file", path=str(log_path), script="visual_debug")

    args = _build_parser().parse_args()
    env = load_env()

    endpoint_raw = str(args.endpoint or env.visual_minio_endpoint).strip()
    bucket = str(args.bucket or env.visual_minio_bucket).strip()
    try:
        access_key, secret_key = resolve_credentials(
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
    print(f"env.visual_minio_access_key={mask_secret(str(env.visual_minio_access_key).strip())}")
    print(f"env.visual_minio_secret_key={mask_secret(str(env.visual_minio_secret_key).strip())}")
    print(f"env.visual_minio_secure={bool(env.visual_minio_secure)}")
    print("effective credentials")
    print(f"effective.access_key={mask_secret(access_key)}")
    print(f"effective.secret_key={mask_secret(secret_key)}")

    try:
        endpoint = normalize_endpoint(endpoint_raw)
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

    profile_mode = str(args.check_profile).lower()
    try:
        checks = run_permission_checks(
            client,
            bucket=bucket,
            src_key=src_key,
            dst_key=dst_key,
            profile_mode=profile_mode,
            scratch_prefix=str(args.scratch_prefix),
            test_delete=bool(args.test_delete),
            copy_source_cls=CopySource,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    ok = all(passed for _, passed in checks)
    print("result=PASS" if ok else "result=FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
