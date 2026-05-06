import ast
from pathlib import Path

from app.parser.models import ParsedClass, ParsedFile, ParsedFunction, ParsedImport


class PythonAstParser:
    def parse(self, file_path: Path) -> ParsedFile:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        visitor = _PythonDefinitionVisitor()
        visitor.visit(tree)
        return ParsedFile(
            path=file_path.resolve(),
            imports=visitor.imports,
            classes=visitor.classes,
            functions=visitor.functions,
        )


class _PythonDefinitionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: list[ParsedImport] = []
        self.classes: list[ParsedClass] = []
        self.functions: list[ParsedFunction] = []
        self._class_stack: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(ParsedImport(module=alias.name, names=[]))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        names = [alias.name for alias in node.names]
        self.imports.append(
            ParsedImport(module=node.module or "", names=names, level=node.level)
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(
            ParsedClass(
                name=node.name,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", None),
            )
        )
        self._class_stack.append(node.name)
        for child in node.body:
            self.visit(child)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualified_name = ".".join([*self._class_stack, node.name])
        calls = _CallCollector.collect(node)
        self.functions.append(
            ParsedFunction(
                name=node.name,
                qualified_name=qualified_name,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", None),
                calls=calls,
            )
        )


class _CallCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []

    @classmethod
    def collect(cls, node: ast.AST) -> list[str]:
        collector = cls()
        for child in ast.iter_child_nodes(node):
            collector.visit(child)
        return collector.calls

    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._call_name(node.func)
        if call_name:
            self.calls.append(call_name)
        self.generic_visit(node)

    def _call_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parts: list[str] = [node.attr]
            value = node.value
            while isinstance(value, ast.Attribute):
                parts.append(value.attr)
                value = value.value
            if isinstance(value, ast.Name):
                parts.append(value.id)
            return ".".join(reversed(parts))
        return None
