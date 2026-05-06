import json
from pathlib import Path

from app.graph.models import Edge, Node
from app.graph.repository import InMemoryGraphRepository


class JsonGraphPersistence:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.nodes_path = data_dir / "nodes.json"
        self.edges_path = data_dir / "edges.json"

    def save(self, repository: InMemoryGraphRepository) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.nodes_path.write_text(
            json.dumps([node.model_dump() for node in repository.get_all_nodes()], indent=2),
            encoding="utf-8",
        )
        self.edges_path.write_text(
            json.dumps([edge.model_dump() for edge in repository.get_all_edges()], indent=2),
            encoding="utf-8",
        )

    def load_into(self, repository: InMemoryGraphRepository) -> None:
        if not self.nodes_path.exists() or not self.edges_path.exists():
            return
        nodes = [
            Node.model_validate(item)
            for item in json.loads(self.nodes_path.read_text(encoding="utf-8"))
        ]
        edges = [
            Edge.model_validate(item)
            for item in json.loads(self.edges_path.read_text(encoding="utf-8"))
        ]
        repository.replace(nodes, edges)
