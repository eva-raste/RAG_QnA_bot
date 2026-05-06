import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from app.graph.builder import GraphBuilder
from app.graph.models import Edge, Node
from app.graph.repository import InMemoryGraphRepository
from app.parser.models import ParsedClass, ParsedFile, ParsedFunction, ParsedImport
from app.parser.python_parser import PythonAstParser
from app.scanner.filesystem import SourceScanner


GRAPH_DIR_NAME = ".codebase-graph"
GITIGNORE_ENTRY = f"{GRAPH_DIR_NAME}/"


class BuildMetadata(BaseModel):
    status: Literal["cache_hit", "incremental", "full_rebuild"]
    storage_dir: str
    files_added: int
    files_changed: int
    files_deleted: int
    files_unchanged: int


@dataclass(frozen=True)
class ProjectBuildResult:
    repository: InMemoryGraphRepository
    metadata: BuildMetadata


class ProjectGraphPersistence:
    def __init__(
        self,
        scanner: SourceScanner,
        parser: PythonAstParser,
        builder: GraphBuilder,
    ) -> None:
        self.scanner = scanner
        self.parser = parser
        self.builder = builder

    def build_or_load(
        self, folder_path: str | Path, force_rebuild: bool = False
    ) -> ProjectBuildResult:
        root = Path(folder_path).expanduser().resolve()
        if not root.exists():
            raise FileNotFoundError(f"Folder does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Path is not a folder: {root}")

        self._ensure_gitignore(root)
        storage_dir = root / GRAPH_DIR_NAME
        nodes_path = storage_dir / "nodes.json"
        edges_path = storage_dir / "edges.json"
        manifest_path = storage_dir / "manifest.json"

        source_files = self.scanner.scan(root)
        current_paths = {str(path): path for path in source_files}
        previous_manifest = self._load_manifest(manifest_path)
        has_cache = (
            not force_rebuild
            and previous_manifest is not None
            and nodes_path.exists()
            and edges_path.exists()
        )

        if not has_cache:
            parsed_files = [self.parser.parse(path) for path in source_files]
            repository = self.builder.build_from_parsed(root, parsed_files)
            manifest = self._manifest_from_parsed_files(parsed_files)
            self._save_all(storage_dir, repository, manifest)
            return ProjectBuildResult(
                repository=repository,
                metadata=BuildMetadata(
                    status="full_rebuild",
                    storage_dir=str(storage_dir),
                    files_added=len(source_files),
                    files_changed=0,
                    files_deleted=0,
                    files_unchanged=0,
                ),
            )

        assert previous_manifest is not None
        previous_files = previous_manifest.get("files", {})
        added: list[Path] = []
        changed: list[Path] = []
        unchanged: list[Path] = []
        next_files: dict[str, dict] = {}

        for file_key, path in sorted(current_paths.items()):
            previous_entry = previous_files.get(file_key)
            if previous_entry is None:
                added.append(path)
                continue

            stat = path.stat()
            if (
                previous_entry.get("size") == stat.st_size
                and previous_entry.get("mtime_ns") == stat.st_mtime_ns
            ):
                unchanged.append(path)
                next_files[file_key] = previous_entry
                continue

            digest = self._sha256(path)
            if digest == previous_entry.get("sha256"):
                unchanged.append(path)
                updated_entry = {**previous_entry}
                updated_entry["size"] = stat.st_size
                updated_entry["mtime_ns"] = stat.st_mtime_ns
                next_files[file_key] = updated_entry
            else:
                changed.append(path)

        deleted_count = len(set(previous_files) - set(current_paths))

        if not added and not changed and deleted_count == 0:
            repository = self._load_repository(nodes_path, edges_path)
            return ProjectBuildResult(
                repository=repository,
                metadata=BuildMetadata(
                    status="cache_hit",
                    storage_dir=str(storage_dir),
                    files_added=0,
                    files_changed=0,
                    files_deleted=0,
                    files_unchanged=len(unchanged),
                ),
            )

        for path in [*added, *changed]:
            parsed = self.parser.parse(path)
            next_files[str(path)] = self._manifest_entry(parsed)

        parsed_files = [
            self._parsed_file_from_entry(next_files[file_key])
            for file_key in sorted(next_files)
        ]
        repository = self.builder.build_from_parsed(root, parsed_files)
        manifest = {"version": 1, "files": next_files}
        self._save_all(storage_dir, repository, manifest)
        return ProjectBuildResult(
            repository=repository,
            metadata=BuildMetadata(
                status="incremental",
                storage_dir=str(storage_dir),
                files_added=len(added),
                files_changed=len(changed),
                files_deleted=deleted_count,
                files_unchanged=len(unchanged),
            ),
        )

    def _ensure_gitignore(self, root: Path) -> None:
        gitignore_path = root / ".gitignore"
        if gitignore_path.exists():
            existing = gitignore_path.read_text(encoding="utf-8")
            entries = {line.strip() for line in existing.splitlines()}
            if GITIGNORE_ENTRY in entries or GRAPH_DIR_NAME in entries:
                return
            suffix = "" if existing.endswith(("\n", "\r\n")) or not existing else "\n"
            gitignore_path.write_text(
                f"{existing}{suffix}{GITIGNORE_ENTRY}\n", encoding="utf-8"
            )
        else:
            gitignore_path.write_text(f"{GITIGNORE_ENTRY}\n", encoding="utf-8")

    def _save_all(
        self,
        storage_dir: Path,
        repository: InMemoryGraphRepository,
        manifest: dict,
    ) -> None:
        storage_dir.mkdir(parents=True, exist_ok=True)
        (storage_dir / "nodes.json").write_text(
            json.dumps([node.model_dump() for node in repository.get_all_nodes()], indent=2),
            encoding="utf-8",
        )
        (storage_dir / "edges.json").write_text(
            json.dumps([edge.model_dump() for edge in repository.get_all_edges()], indent=2),
            encoding="utf-8",
        )
        (storage_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

    def _load_repository(self, nodes_path: Path, edges_path: Path) -> InMemoryGraphRepository:
        repository = InMemoryGraphRepository()
        nodes = [
            Node.model_validate(item)
            for item in json.loads(nodes_path.read_text(encoding="utf-8"))
        ]
        edges = [
            Edge.model_validate(item)
            for item in json.loads(edges_path.read_text(encoding="utf-8"))
        ]
        repository.replace(nodes, edges)
        return repository

    def _load_manifest(self, manifest_path: Path) -> dict | None:
        if not manifest_path.exists():
            return None
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def _manifest_from_parsed_files(self, parsed_files: list[ParsedFile]) -> dict:
        return {
            "version": 1,
            "files": {
                str(parsed.path): self._manifest_entry(parsed)
                for parsed in sorted(parsed_files, key=lambda item: str(item.path))
            },
        }

    def _manifest_entry(self, parsed: ParsedFile) -> dict:
        stat = parsed.path.stat()
        return {
            "path": str(parsed.path),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": self._sha256(parsed.path),
            "parsed": {
                "path": str(parsed.path),
                "imports": [asdict(item) for item in parsed.imports],
                "classes": [asdict(item) for item in parsed.classes],
                "functions": [asdict(item) for item in parsed.functions],
            },
        }

    def _parsed_file_from_entry(self, entry: dict) -> ParsedFile:
        parsed = entry["parsed"]
        return ParsedFile(
            path=Path(parsed["path"]).resolve(),
            imports=[ParsedImport(**item) for item in parsed["imports"]],
            classes=[ParsedClass(**item) for item in parsed["classes"]],
            functions=[ParsedFunction(**item) for item in parsed["functions"]],
        )

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
