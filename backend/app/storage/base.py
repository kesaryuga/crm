from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    backend: str

    def put(self, data: bytes, filename: str) -> str: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class LocalStorage:
    backend = "local"

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        key = f"local/{uuid.uuid4().hex}{ext}"
        path = self.root / Path(key).name
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return (self.root / Path(key).name).read_bytes()

    def delete(self, key: str) -> None:
        path = self.root / Path(key).name
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return (self.root / Path(key).name).exists()


class S3CompatibleStorage:
    """Каркас S3: business-logic не должен знать о бэкенде."""

    backend = "s3"

    def __init__(self, bucket: str = "") -> None:
        self.bucket = bucket

    def put(self, data: bytes, filename: str) -> str:
        raise NotImplementedError("S3 storage подключается при деплое")

    def get(self, key: str) -> bytes:
        raise NotImplementedError("S3 storage подключается при деплое")

    def delete(self, key: str) -> None:
        raise NotImplementedError("S3 storage подключается при деплое")

    def exists(self, key: str) -> bool:
        raise NotImplementedError("S3 storage подключается при деплое")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
