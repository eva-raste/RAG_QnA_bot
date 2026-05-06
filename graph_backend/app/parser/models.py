from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ParsedImport:
    module: str
    names: list[str]
    level: int = 0


@dataclass(frozen=True)
class ParsedClass:
    name: str
    lineno: int
    end_lineno: int | None


@dataclass(frozen=True)
class ParsedFunction:
    name: str
    qualified_name: str
    lineno: int
    end_lineno: int | None
    calls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    imports: list[ParsedImport]
    classes: list[ParsedClass]
    functions: list[ParsedFunction]
