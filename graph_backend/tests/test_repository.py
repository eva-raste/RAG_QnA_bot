from app.graph.models import Edge, Node
from app.graph.repository import InMemoryGraphRepository


def test_repository_tracks_forward_and_reverse_neighbors() -> None:
    repository = InMemoryGraphRepository()
    file_node = Node(id="file.py", type="file")
    function_node = Node(id="file.py:run", type="function")

    repository.add_node(file_node)
    repository.add_node(function_node)
    repository.add_edge(Edge(src=file_node.id, dst=function_node.id, type="DEFINES"))

    assert repository.get_neighbors(file_node.id, "DEFINES") == [function_node]
    assert repository.get_reverse_neighbors(function_node.id, "DEFINES") == [file_node]
