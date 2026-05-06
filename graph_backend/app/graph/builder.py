from collections import defaultdict
from pathlib import Path

from app.graph.models import Edge, Node
from app.graph.repository import InMemoryGraphRepository
from app.parser.models import ParsedFile, ParsedFunction, ParsedImport
from app.parser.python_parser import PythonAstParser
from app.scanner.filesystem import SourceScanner


class GraphBuilder:
    def __init__(self, scanner: SourceScanner, parser: PythonAstParser) -> None:
        self.scanner = scanner
        self.parser = parser

    def build(self, folder_path: str | Path) -> InMemoryGraphRepository:
        root = Path(folder_path).expanduser().resolve()
        files = self.scanner.scan(root)
        parsed_files = [self.parser.parse(file_path) for file_path in files]
        return self.build_from_parsed(root, parsed_files)

    def build_from_parsed(
        self, root: str | Path, parsed_files: list[ParsedFile]
    ) -> InMemoryGraphRepository:
        resolved_root = Path(root).expanduser().resolve()
        repository = InMemoryGraphRepository()
        function_index = self._build_function_index(parsed_files)

        for parsed in parsed_files:
            file_id = self.file_id(parsed.path)
            repository.add_node(
                Node(
                    id=file_id,
                    type="file",
                    properties={
                        "name": parsed.path.name,
                        "path": file_id,
                        "language": "python",
                    },
                )
            )
            self._add_definitions(repository, parsed, function_index)

        for parsed in parsed_files:
            self._add_import_edges(repository, resolved_root, parsed)
            self._add_call_edges(repository, parsed, function_index)

        return repository

    @staticmethod
    def file_id(file_path: Path) -> str:
        return str(file_path.resolve())

    @classmethod
    def function_id(cls, file_path: Path, qualified_name: str) -> str:
        return f"{cls.file_id(file_path)}:{qualified_name}"

    @classmethod
    def class_id(cls, file_path: Path, class_name: str) -> str:
        return f"{cls.file_id(file_path)}:{class_name}"

    def _add_definitions(
        self,
        repository: InMemoryGraphRepository,
        parsed: ParsedFile,
        function_index: dict[str, list[str]],
    ) -> None:
        file_id = self.file_id(parsed.path)
        for parsed_class in parsed.classes:
            class_id = self.class_id(parsed.path, parsed_class.name)
            repository.add_node(
                Node(
                    id=class_id,
                    type="class",
                    properties={
                        "name": parsed_class.name,
                        "path": file_id,
                        "lineno": parsed_class.lineno,
                        "end_lineno": parsed_class.end_lineno,
                    },
                )
            )
            repository.add_edge(Edge(src=file_id, dst=class_id, type="DEFINES"))

        for function in parsed.functions:
            function_id = self.function_id(parsed.path, function.qualified_name)
            repository.add_node(
                Node(
                    id=function_id,
                    type="function",
                    properties={
                        "name": function.name,
                        "path": file_id,
                        "lineno": function.lineno,
                        "end_lineno": function.end_lineno,
                        "qualified_name": function.qualified_name,
                    },
                )
            )
            repository.add_edge(Edge(src=file_id, dst=function_id, type="DEFINES"))

    def _add_import_edges(
        self, repository: InMemoryGraphRepository, root: Path, parsed: ParsedFile
    ) -> None:
        file_id = self.file_id(parsed.path)
        for parsed_import in parsed.imports:
            target = self._resolve_import(root, parsed.path, parsed_import)
            if target is not None:
                repository.add_edge(Edge(src=file_id, dst=self.file_id(target), type="IMPORTS"))

    def _add_call_edges(
        self,
        repository: InMemoryGraphRepository,
        parsed: ParsedFile,
        function_index: dict[str, list[str]],
    ) -> None:
        for function in parsed.functions:
            src = self.function_id(parsed.path, function.qualified_name)
            for call in function.calls:
                target = self._resolve_call(parsed, call, function_index)
                if target is not None and target != src:
                    repository.add_edge(Edge(src=src, dst=target, type="CALLS"))

    def _build_function_index(self, parsed_files: list[ParsedFile]) -> dict[str, list[str]]:
        index: dict[str, list[str]] = defaultdict(list)
        for parsed in parsed_files:
            for function in parsed.functions:
                node_id = self.function_id(parsed.path, function.qualified_name)
                keys = {function.name, function.qualified_name}
                for key in keys:
                    index[key].append(node_id)
        return index

    def _resolve_call(
        self,
        parsed: ParsedFile,
        call: str,
        function_index: dict[str, list[str]],
    ) -> str | None:
        call_tail = call.split(".")[-1]
        local_by_qualified = {
            function.qualified_name: self.function_id(parsed.path, function.qualified_name)
            for function in parsed.functions
        }
        for qualified_name, node_id in local_by_qualified.items():
            if qualified_name == call or qualified_name.endswith(f".{call_tail}"):
                return node_id

        global_matches = function_index.get(call) or function_index.get(call_tail) or []
        if len(global_matches) == 1:
            return global_matches[0]
        return None

    def _resolve_import(
        self,
        root: Path,
        current_file: Path,
        parsed_import: ParsedImport,
    ) -> Path | None:
        if parsed_import.level:
            base = current_file.parent
            for _ in range(max(parsed_import.level - 1, 0)):
                base = base.parent
            module_parts = parsed_import.module.split(".") if parsed_import.module else []
            candidates = self._module_candidates(base, module_parts)
        else:
            module_parts = parsed_import.module.split(".") if parsed_import.module else []
            candidates = self._module_candidates(root, module_parts)

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                try:
                    candidate.resolve().relative_to(root)
                except ValueError:
                    continue
                return candidate.resolve()
        return None

    def _module_candidates(self, base: Path, module_parts: list[str]) -> list[Path]:
        if not module_parts:
            return []
        module_path = base.joinpath(*module_parts)
        return [module_path.with_suffix(".py"), module_path / "__init__.py"]
