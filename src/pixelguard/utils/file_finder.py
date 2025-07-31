from pathlib import Path
from typing import Set, List, Iterator


class FileFinder:
    DEFAULT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}

    def __init__(self, extensions: Set[str] = None):
        self.extensions = extensions or self.DEFAULT_EXTENSIONS

    def find_images(self, folder_path, recursive=True) -> List[Path]:
        folder = Path(folder_path)
        if recursive:
            files = folder.rglob("*")
        else:
            files = folder.glob("*")
        return [
            file
            for file in files
            if file.suffix.lower() in self.extensions and file.is_file()
        ]

    def iter_images(self, folder_path, recursive=True) -> Iterator[Path]:
        return iter(self.find_images(folder_path, recursive))

    def count_images(self, folder_path, recursive=True) -> int:
        return len(self.find_images(folder_path, recursive))

    def get_extension_statistics(self, folder_path) -> dict:
        files = self.find_images(folder_path)
        stats = {}
        for file in files:
            ext = file.suffix.lower()
            stats[ext] = stats.get(ext, 0) + 1
        return stats
