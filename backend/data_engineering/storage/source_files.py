"""Private storage for original uploaded source files.

Local storage is intended for development and should be mounted on a persistent
Docker volume. S3-compatible storage is available when explicitly configured.
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import BinaryIO, Iterator

from app.core.config import settings


_OBJECT_KEY = re.compile(r"^[0-9a-f]{32}/[0-9a-f]{32}\.pdf$")


class SourceFileStorage:
    def __init__(self) -> None:
        self.backend = settings.SOURCE_STORAGE_BACKEND.strip().lower()

    def _validate_key(self, key: str) -> None:
        if not _OBJECT_KEY.fullmatch(key):
            raise ValueError("Invalid source object key")

    def save_pdf(self, content: bytes) -> str:
        key = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}.pdf"
        if self.backend == "local":
            target = self._local_path(key)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            return key
        if self.backend == "s3":
            bucket = settings.SOURCE_STORAGE_BUCKET
            if not bucket:
                raise RuntimeError("SOURCE_STORAGE_BUCKET is required for S3 storage")
            self._s3_client().put_object(
                Bucket=bucket, Key=key, Body=content, ContentType="application/pdf"
            )
            return key
        raise RuntimeError(f"Unsupported source storage backend: {self.backend}")

    def open_pdf(self, key: str) -> BinaryIO:
        self._validate_key(key)
        if self.backend == "local":
            return self._local_path(key).open("rb")
        if self.backend == "s3":
            bucket = settings.SOURCE_STORAGE_BUCKET
            if not bucket:
                raise RuntimeError("SOURCE_STORAGE_BUCKET is required for S3 storage")
            return self._s3_client().get_object(Bucket=bucket, Key=key)["Body"]
        raise RuntimeError(f"Unsupported source storage backend: {self.backend}")

    def delete(self, key: str) -> None:
        self._validate_key(key)
        if self.backend == "local":
            self._local_path(key).unlink(missing_ok=True)
        elif self.backend == "s3":
            bucket = settings.SOURCE_STORAGE_BUCKET
            if not bucket:
                raise RuntimeError("SOURCE_STORAGE_BUCKET is required for S3 storage")
            self._s3_client().delete_object(Bucket=bucket, Key=key)
        else:
            raise RuntimeError(f"Unsupported source storage backend: {self.backend}")

    def _local_path(self, key: str) -> Path:
        self._validate_key(key)
        root = Path(settings.SOURCE_STORAGE_ROOT).resolve()
        path = (root / key).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Invalid source object key")
        return path

    @staticmethod
    def _s3_client():
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("Install boto3 to use S3-compatible source storage") from exc
        return boto3.client(
            "s3",
            endpoint_url=settings.SOURCE_STORAGE_ENDPOINT_URL or None,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        )


def stream_file(file: BinaryIO, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    try:
        while chunk := file.read(chunk_size):
            yield chunk
    finally:
        file.close()
