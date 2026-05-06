from pathlib import Path

from app.parser.python_parser import PythonAstParser


def test_python_parser_extracts_imports_classes_functions_and_calls() -> None:
    source = Path(__file__).resolve().parent / "fixtures" / "parser" / "module.py"

    parsed = PythonAstParser().parse(source)

    assert [item.module for item in parsed.imports] == ["os", "pkg"]
    assert [item.name for item in parsed.classes] == ["Service"]
    assert {item.qualified_name for item in parsed.functions} == {"Service.run", "build"}
    build = next(item for item in parsed.functions if item.name == "build")
    assert "Service" in build.calls
    assert "run" in build.calls
