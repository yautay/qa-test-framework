from __future__ import annotations

from dataclasses import dataclass

from framework.env import RuntimeEnv


@dataclass(frozen=True)
class MinioObject:
    object_key: str
    size_bytes: int


class MinioOps:
    def __init__(self, env: RuntimeEnv) -> None:
        if not env.visual_minio_endpoint:
            raise ValueError("VISUAL_MINIO_ENDPOINT is required for --with-minio")
        self._bucket = env.visual_minio_bucket
        try:
            from minio import Minio
            from minio.commonconfig import CopySource
        except Exception as exc:
            raise RuntimeError("minio package is not available") from exc

        self._copy_source_cls = CopySource
        self._client = Minio(
            env.visual_minio_endpoint,
            access_key=env.visual_minio_access_key,
            secret_key=env.visual_minio_secret_key,
            secure=env.visual_minio_secure,
        )

    def list_objects(self, prefix: str) -> list[MinioObject]:
        out: list[MinioObject] = []
        for item in self._client.list_objects(self._bucket, prefix=prefix, recursive=True):
            if not str(item.object_name).lower().endswith(".png"):
                continue
            out.append(MinioObject(object_key=str(item.object_name), size_bytes=int(item.size or 0)))
        return out

    def copy_object(self, source_key: str, target_key: str) -> None:
        source = self._copy_source_cls(self._bucket, source_key)
        self._client.copy_object(self._bucket, target_key, source)
