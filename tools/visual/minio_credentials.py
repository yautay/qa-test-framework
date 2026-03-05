from __future__ import annotations

from getpass import getpass

from tools.visual.baseline_ops.minio_ops import MinioCredentials


def resolve_runtime_minio_credentials(args, *, dry_run: bool, apply_flag: str) -> MinioCredentials | None:
    with_minio = bool(getattr(args, "with_minio", False))
    ask = bool(getattr(args, "ask_release_credentials", False))
    if ask and not with_minio:
        raise ValueError("--ask-release-credentials requires --with-minio")
    if ask and dry_run:
        raise ValueError(f"--ask-release-credentials is allowed only with {apply_flag}")
    if not ask:
        return None

    access_key = str(getattr(args, "minio_access_key", "")).strip()
    if not access_key:
        access_key = input("MinIO release access key: ").strip()
    if not access_key:
        raise ValueError("missing MinIO release access key")
    secret_key = getpass("MinIO release secret key: ").strip()
    if not secret_key:
        raise ValueError("missing MinIO release secret key")
    return MinioCredentials(access_key=access_key, secret_key=secret_key)
