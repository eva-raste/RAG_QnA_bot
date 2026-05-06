from app.graph.models import Node
from app.graph.repository import InMemoryGraphRepository


def find_unused_functions(repository: InMemoryGraphRepository) -> list[Node]:
    unused: list[Node] = []
    for node in repository.get_all_nodes():
        if node.type != "function":
            continue
        callers = repository.get_reverse_neighbors(node.id, "CALLS")
        if not callers:
            unused.append(node)
    return unused
