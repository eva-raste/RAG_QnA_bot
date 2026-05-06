from app.analysis.call_chain import find_call_chain
from app.analysis.cycles import find_import_cycles
from app.analysis.unused import find_unused_functions
from app.graph.models import Edge, Node
from app.graph.repository import InMemoryGraphRepository


def test_analysis_helpers() -> None:
    repository = InMemoryGraphRepository()
    for node_id, node_type in [
        ("a.py", "file"),
        ("b.py", "file"),
        ("a.py:one", "function"),
        ("a.py:two", "function"),
        ("a.py:unused", "function"),
    ]:
        repository.add_node(Node(id=node_id, type=node_type, properties={"name": node_id}))
    repository.add_edge(Edge(src="a.py", dst="b.py", type="IMPORTS"))
    repository.add_edge(Edge(src="b.py", dst="a.py", type="IMPORTS"))
    repository.add_edge(Edge(src="a.py:one", dst="a.py:two", type="CALLS"))

    assert find_import_cycles(repository) == [["a.py", "b.py", "a.py"]]
    assert find_call_chain(repository, "a.py:one", "a.py:two") == [
        "a.py:one",
        "a.py:two",
    ]
    unused_names = {node.id for node in find_unused_functions(repository)}
    assert "a.py:unused" in unused_names
