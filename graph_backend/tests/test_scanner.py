from app.scanner.filesystem import SourceScanner


def test_scanner_collects_python_and_skips_ignored_dirs() -> None:
    from pathlib import Path

    test_root = Path(__file__).resolve().parent / "fixtures" / "scanner"

    files = SourceScanner().scan(test_root)

    assert files == [(test_root / "app.py").resolve()]
