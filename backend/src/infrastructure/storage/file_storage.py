"""T088 — Local file storage for uploaded documents."""
from __future__ import annotations

import os
import shutil
import uuid


class FileStorage:
    """Saves and deletes files under ``./uploads/{kb_id}/{uuid}_{filename}``."""

    BASE_DIR: str = "./uploads"

    def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        kb_id: str,
    ) -> str:
        """Persist *file_bytes* and return the path where the file was saved."""
        dir_path = os.path.join(self.BASE_DIR, str(kb_id))
        os.makedirs(dir_path, exist_ok=True)

        unique_name = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(dir_path, unique_name)

        with open(file_path, "wb") as fh:
            fh.write(file_bytes)

        return file_path

    def delete_file(self, path: str) -> None:
        """Remove a file if it exists; silently ignores missing files."""
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    def delete_kb_dir(self, kb_id: str) -> None:
        """Remove all uploaded files for a knowledge base if the directory exists."""
        dir_path = os.path.join(self.BASE_DIR, str(kb_id))
        shutil.rmtree(dir_path, ignore_errors=True)
