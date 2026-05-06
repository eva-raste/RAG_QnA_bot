from abc import ABC, abstractmethod
from collections import defaultdict

from app.graph.models import Edge, Node


class GraphRepository(ABC):
    @abstractmethod
    def add_node(self, node: Node) -> None:
        ...

    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        ...

    @abstractmethod
    def get_neighbors(self, node_id: str, relation: str | None = None) -> list[Node]:
        ...

    @abstractmethod
    def get_reverse_neighbors(
        self, node_id: str, relation: str | None = None
    ) -> list[Node]:
        ...

    @abstractmethod
    def get_all_nodes(self) -> list[Node]:
        ...

    @abstractmethod
    def get_all_edges(self) -> list[Edge]:
        ...


class InMemoryGraphRepository(GraphRepository):
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.adjacency: dict[str, list[Edge]] = defaultdict(list)
        self.reverse_adjacency: dict[str, list[Edge]] = defaultdict(list)
        self._edge_keys: set[tuple[str, str, str]] = set()

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        key = (edge.src, edge.dst, edge.type)
        if key in self._edge_keys:
            return
        self._edge_keys.add(key)
        self.adjacency[edge.src].append(edge)
        self.reverse_adjacency[edge.dst].append(edge)

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, relation: str | None = None) -> list[Node]:
        edges = self._filter_edges(self.adjacency.get(node_id, []), relation)
        return [self.nodes[edge.dst] for edge in edges if edge.dst in self.nodes]

    def get_reverse_neighbors(
        self, node_id: str, relation: str | None = None
    ) -> list[Node]:
        edges = self._filter_edges(self.reverse_adjacency.get(node_id, []), relation)
        return [self.nodes[edge.src] for edge in edges if edge.src in self.nodes]

    def get_all_nodes(self) -> list[Node]:
        return sorted(self.nodes.values(), key=lambda node: node.id)

    def get_all_edges(self) -> list[Edge]:
        edges = [edge for edge_list in self.adjacency.values() for edge in edge_list]
        return sorted(edges, key=lambda edge: (edge.src, edge.dst, edge.type))

    def clear(self) -> None:
        self.nodes.clear()
        self.adjacency.clear()
        self.reverse_adjacency.clear()
        self._edge_keys.clear()

    def replace(self, nodes: list[Node], edges: list[Edge]) -> None:
        self.clear()
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    def _filter_edges(self, edges: list[Edge], relation: str | None) -> list[Edge]:
        if relation is None:
            return edges
        return [edge for edge in edges if edge.type == relation]
