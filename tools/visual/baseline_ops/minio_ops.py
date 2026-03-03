from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from framework.env import RuntimeEnv


@dataclass(frozen=True)
class MinioObject:
    object_key: str
    size_bytes: int
    last_modified_utc: datetime


@dataclass(frozen=True)
class MinioCredentials:
    access_key: str
    secret_key: str


class MinioOps:
    def __init__(self, env: RuntimeEnv, *, credentials: MinioCredentials | None = None) -> None:
        if not env.visual_minio_endpoint:
            raise ValueError("VISUAL_MINIO_ENDPOINT is required for --with-minio")
        self._bucket = env.visual_minio_bucket
        access_key = credentials.access_key if credentials else env.visual_minio_access_key
        secret_key = credentials.secret_key if credentials else env.visual_minio_secret_key
        if not access_key or not secret_key:
            raise ValueError("MinIO access key and secret key are required")
        try:
            from minio import Minio
            from minio.commonconfig import CopySource
        except Exception as exc:
            raise RuntimeError("minio package is not available") from exc

        self._copy_source_cls = CopySource
        self._client = Minio(
            env.visual_minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=env.visual_minio_secure,
        )

    def ensure_bucket_exists(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def list_objects(self, prefix: str) -> list[MinioObject]:
        self.ensure_bucket_exists()
        out: list[MinioObject] = []
        for item in self._client.list_objects(self._bucket, prefix=prefix, recursive=True):
            if not str(item.object_name).lower().endswith(".png"):
                continue
            modified = item.last_modified if isinstance(item.last_modified, datetime) else datetime.now(UTC)
            modified_utc = modified.astimezone(UTC) if modified.tzinfo else modified.replace(tzinfo=UTC)
            out.append(
                MinioObject(
                    object_key=str(item.object_name),
                    size_bytes=int(item.size or 0),
                    last_modified_utc=modified_utc,
                )
            )
        return out

    def list_keys(self, prefix: str) -> set[str]:
        return {item.object_key for item in self.list_objects(prefix)}

    def copy_object(self, source_key: str, target_key: str) -> None:
        self.ensure_bucket_exists()
        source = self._copy_source_cls(self._bucket, source_key)
        self._client.copy_object(self._bucket, target_key, source)

    def remove_object(self, object_key: str) -> None:
        self.ensure_bucket_exists()
        self._client.remove_object(self._bucket, object_key)

    def remove_objects(self, object_keys: Iterable[str]) -> int:
        removed = 0
        for object_key in object_keys:
            self.remove_object(object_key)
            removed += 1
        return removed
