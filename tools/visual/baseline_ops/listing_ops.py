from __future__ import annotations

from framework.env import RuntimeEnv

from .minio_ops import MinioOps
from .paths import local_baseline_root, parse_object_key, repo_root
from .scanner import list_local_versions as _list_local_versions


def list_local_versions(env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> list[str]:
    root = local_baseline_root(repo_root())
    return _list_local_versions(root, profile=profile, suites=suites)


def list_minio_versions(env: RuntimeEnv, *, profile: str, suites: set[str] | None) -> list[str]:
    ops = MinioOps(env)
    versions: set[str] = set()
    suite_list = sorted(suites) if suites else [""]

    for suite_id in suite_list:
        prefix = f"{suite_id}/{profile}/" if suite_id else ""
        for obj in ops.list_objects(prefix):
            try:
                parsed_suite, parsed_profile, version, _rest = parse_object_key(obj.object_key)
            except ValueError:
                continue
            if parsed_profile != profile:
                continue
            if suites and parsed_suite not in suites:
                continue
            versions.add(version)

    return sorted(versions)
