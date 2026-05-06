from pathlib import Path
import json

from app.graph.builder import GraphBuilder
from app.parser.python_parser import PythonAstParser
from app.persistence.project_store import ProjectGraphPersistence
from app.scanner.filesystem import SourceScanner


def _store() -> ProjectGraphPersistence:
    scanner = SourceScanner()
    parser = PythonAstParser()
    return ProjectGraphPersistence(scanner, parser, GraphBuilder(scanner, parser))


def _runtime_project(name: str) -> Path:
    root = Path(__file__).resolve().parent / "runtime_data" / name
    return root


def test_project_store_full_rebuild_cache_hit_and_gitignore() -> None:
    root = _runtime_project("cache")
    (root / "a.py").write_text(
        "def one():\n    return two()\n\ndef two():\n    return 'two'\n",
        encoding="utf-8",
    )

    first = _store().build_or_load(root, force_rebuild=True)
    second = _store().build_or_load(root)

    assert first.metadata.status == "full_rebuild"
    assert second.metadata.status == "cache_hit"
    assert (root / ".codebase-graph" / "nodes.json").exists()
    assert (root / ".codebase-graph" / "edges.json").exists()
    assert (root / ".codebase-graph" / "manifest.json").exists()
    assert (root / ".gitignore").read_text(encoding="utf-8").count(".codebase-graph/") == 1


def test_project_store_incremental_changed_deleted_and_force_rebuild() -> None:
    root = _runtime_project("incremental")
    (root / "a.py").write_text(
        "from b import helper\n\ndef one():\n    return helper()\n",
        encoding="utf-8",
    )
    (root / "b.py").write_text("def helper():\n    return 'old'\n", encoding="utf-8")

    store = _store()
    store.build_or_load(root, force_rebuild=True)
    (root / "b.py").write_text(
        "def helper():\n    return replacement()\n\ndef replacement():\n    return 'new'\n",
        encoding="utf-8",
    )
    incremental = store.build_or_load(root)

    assert incremental.metadata.status == "incremental"
    assert incremental.metadata.files_changed == 1
    assert any(
        node.properties.get("name") == "replacement"
        for node in incremental.repository.get_all_nodes()
    )

    manifest_path = root / ".codebase-graph" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing_entry = next(iter(manifest["files"].values()))
    manifest["files"][str(root / "deleted.py")] = {
        **existing_entry,
        "path": str(root / "deleted.py"),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    deleted = store.build_or_load(root)

    assert deleted.metadata.files_deleted == 1

    forced = store.build_or_load(root, force_rebuild=True)
    assert forced.metadata.status == "full_rebuild"
