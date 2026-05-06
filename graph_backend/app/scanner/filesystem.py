from pathlib import Path


DEFAULT_SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    ".codebase-graph",
}


class SourceScanner:
    def __init__(
        self,
        source_extensions: set[str] | None = None,
        skip_dirs: set[str] | None = None,
    ) -> None:
        self.source_extensions = source_extensions or {".py"}
        self.skip_dirs = skip_dirs or DEFAULT_SKIP_DIRS

    def scan(self, folder_path: str | Path) -> list[Path]:
        root = Path(folder_path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Folder does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Path is not a folder: {root}")

        source_files: list[Path] = []
        for path in root.rglob("*"):
            if self._is_skipped(path, root):
                continue
            if path.is_file() and path.suffix in self.source_extensions:
                source_files.append(path.resolve())
        return sorted(source_files)

    def _is_skipped(self, path: Path, root: Path) -> bool:
        try:
            relative = path.relative_to(root)
        except ValueError:
            return True
        return any(part in self.skip_dirs for part in relative.parts)
