from collections import deque

from app.graph.repository import InMemoryGraphRepository


def find_call_chain(
    repository: InMemoryGraphRepository, src: str, dst: str
) -> list[str] | None:
    if repository.get_node(src) is None or repository.get_node(dst) is None:
        return None

    queue: deque[list[str]] = deque([[src]])
    seen = {src}
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == dst:
            return path
        for neighbor in repository.get_neighbors(current, "CALLS"):
            if neighbor.id in seen:
                continue
            seen.add(neighbor.id)
            queue.append([*path, neighbor.id])
    return None
