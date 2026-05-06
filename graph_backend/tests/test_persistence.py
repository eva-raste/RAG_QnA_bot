from pathlib import Path

from app.graph.models import Edge, Node
from app.graph.repository import InMemoryGraphRepository
from app.persistence.json_store import JsonGraphPersistence


def test_json_persistence_round_trip() -> None:
    test_root = Path(__file__).resolve().parent / "runtime_data"
    repository = InMemoryGraphRepository()
    repository.add_node(Node(id="file.py", type="file", properties={"name": "file.py"}))
    repository.add_node(Node(id="file.py:run", type="function"))
    repository.add_edge(Edge(src="file.py", dst="file.py:run", type="DEFINES"))

    persistence = JsonGraphPersistence(test_root)
    persistence.save(repository)

    loaded = InMemoryGraphRepository()
    persistence.load_into(loaded)

    assert loaded.get_all_nodes() == repository.get_all_nodes()
    assert loaded.get_all_edges() == repository.get_all_edges()
