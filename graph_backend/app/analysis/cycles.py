from app.graph.repository import InMemoryGraphRepository


def find_import_cycles(repository: InMemoryGraphRepository) -> list[list[str]]:
    graph: dict[str, list[str]] = {}
    for edge in repository.get_all_edges():
        if edge.type == "IMPORTS":
            graph.setdefault(edge.src, []).append(edge.dst)

    cycles: set[tuple[str, ...]] = set()
    path: list[str] = []
    visiting: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            start = path.index(node_id)
            cycle = path[start:] + [node_id]
            cycles.add(_canonical_cycle(cycle))
            return
        visiting.add(node_id)
        path.append(node_id)
        for neighbor in graph.get(node_id, []):
            visit(neighbor)
        path.pop()
        visiting.remove(node_id)

    for node_id in graph:
        visit(node_id)
    return [list(cycle) for cycle in sorted(cycles)]


def _canonical_cycle(cycle: list[str]) -> tuple[str, ...]:
    body = cycle[:-1]
    rotations = [body[index:] + body[:index] for index in range(len(body))]
    smallest = min(rotations)
    return tuple(smallest + [smallest[0]])
