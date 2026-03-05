from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .debug_helpers import build_release_destination_key, is_access_denied_error


def run_check(name: str, func: Callable[[], Any], *, required_perm: str) -> bool:
    try:
        func()
        print(f"PASS  {name}")
        return True
    except Exception as exc:
        print(f"FAIL  {name}: {exc}")
        print(f"      likely missing permission: {required_perm}")
        return False


def run_permission_checks(
    client: Any,
    *,
    bucket: str,
    src_key: str,
    dst_key: str,
    profile_mode: str,
    scratch_prefix: str,
    test_delete: bool,
    copy_source_cls: type,
) -> list[tuple[str, bool]]:
    checks: list[tuple[str, bool]] = []
    checks.append(
        (
            "list bucket",
            run_check(
                "ListBucket",
                lambda: next(client.list_objects(bucket, recursive=True), None),
                required_perm="s3:ListBucket",
            ),
        )
    )
    checks.append(
        (
            "read source",
            run_check(
                "GetObject (stat src)",
                lambda: client.stat_object(bucket, src_key),
                required_perm="s3:GetObject",
            ),
        )
    )

    should_check_release_writes = profile_mode in {"release", "auto"}
    release_dst_key = dst_key
    if should_check_release_writes:
        release_dst_key = build_release_destination_key(src_key=src_key, scratch_prefix=scratch_prefix)
        print(f"release_dst_key={release_dst_key}")

        copy_ok = True
        try:
            client.copy_object(bucket, release_dst_key, copy_source_cls(bucket, src_key))
            print("PASS  PutObject via copy")
        except Exception as exc:
            if profile_mode == "auto" and is_access_denied_error(exc):
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

    if (should_check_release_writes and profile_mode in {"release", "auto"}) or test_delete:
        checks.append(
            (
                "delete destination",
                run_check(
                    "DeleteObject (dst)",
                    lambda: client.remove_object(bucket, release_dst_key),
                    required_perm="s3:DeleteObject",
                ),
            )
        )

    return checks
