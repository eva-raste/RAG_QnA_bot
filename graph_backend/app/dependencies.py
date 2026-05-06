from app.graph.builder import GraphBuilder
from app.graph.repository import InMemoryGraphRepository
from app.parser.python_parser import PythonAstParser
from app.persistence.project_store import ProjectGraphPersistence
from app.scanner.filesystem import SourceScanner


graph_repository = InMemoryGraphRepository()
source_scanner = SourceScanner()
python_parser = PythonAstParser()
graph_builder = GraphBuilder(source_scanner, python_parser)
project_persistence = ProjectGraphPersistence(
    source_scanner,
    python_parser,
    graph_builder,
)
