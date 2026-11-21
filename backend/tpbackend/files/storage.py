"""
Where the bytes of Files are kept, under their id. Only on disk for now, but kept behind
this class so something like S3 can be added without changing the rest
"""

import os
import uuid
from pathlib import Path


class DiskStorage:
    def __init__(self, directory: Path):
        self.directory = directory

    def path(self, file_id: str) -> Path:
        # only uuids, so a path can never leave the directory
        name = str(uuid.UUID(file_id))
        # in subfolders by the first two characters (256 of them), so no folder gets huge
        return self.directory / name[:2] / name

    def save(self, file_id: str, data: bytes):
        path = self.path(file_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        # write to a temporary file first, so a half written file is never served
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def load(self, file_id: str) -> bytes | None:
        path = self.path(file_id)
        if not path.exists():
            return None
        return path.read_bytes()

    def exists(self, file_id: str) -> bool:
        return self.path(file_id).exists()

    def delete(self, file_id: str):
        self.path(file_id).unlink(missing_ok=True)


storage = DiskStorage(Path(os.environ.get("FILES_DIR", "files")))
