from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.analysis.call_chain import find_call_chain
from app.analysis.cycles import find_import_cycles
from app.analysis.unused import find_unused_functions
from app.dependencies import graph_repository, project_persistence
from app.graph.models import Edge, Node
from app.persistence.project_store import BuildMetadata


router = APIRouter()


class BuildGraphRequest(BaseModel):
    folder_path: str
    force_rebuild: bool = False


class GraphResponse(BaseModel):
    nodes: list[Node]
    edges: list[Edge]


class BuildGraphResponse(GraphResponse):
    metadata: BuildMetadata


@router.post("/build-graph", response_model=BuildGraphResponse)
def build_graph(payload: BuildGraphRequest) -> BuildGraphResponse:
    try:
        result = project_persistence.build_or_load(
            payload.folder_path,
            force_rebuild=payload.force_rebuild,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotADirectoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    graph_repository.replace(
        result.repository.get_all_nodes(),
        result.repository.get_all_edges(),
    )
    return BuildGraphResponse(
        nodes=graph_repository.get_all_nodes(),
        edges=graph_repository.get_all_edges(),
        metadata=result.metadata,
    )


@router.get("/graph", response_model=GraphResponse)
def get_graph() -> GraphResponse:
    return GraphResponse(
        nodes=graph_repository.get_all_nodes(),
        edges=graph_repository.get_all_edges(),
    )


@router.get("/node/{node_id:path}")
def get_node(node_id: str, relation: str | None = None) -> dict:
    node = graph_repository.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")

    outgoing = graph_repository.get_neighbors(node_id, relation)
    incoming = graph_repository.get_reverse_neighbors(node_id, relation)
    connected_ids = {neighbor.id for neighbor in outgoing + incoming}
    connected_edges = [
        edge
        for edge in graph_repository.get_all_edges()
        if edge.src == node_id or edge.dst == node_id or edge.src in connected_ids
    ]
    return {
        "node": node,
        "outgoing_neighbors": outgoing,
        "incoming_neighbors": incoming,
        "connected_edges": connected_edges,
    }


@router.get("/search", response_model=list[Node])
def search(query: str = Query(default="")) -> list[Node]:
    normalized = query.strip().lower()
    if not normalized:
        return []

    matches: list[Node] = []
    for node in graph_repository.get_all_nodes():
        searchable = [
            node.id,
            node.type,
            str(node.properties.get("name", "")),
            str(node.properties.get("qualified_name", "")),
            str(node.properties.get("path", "")),
        ]
        if any(normalized in value.lower() for value in searchable):
            matches.append(node)
    return matches


@router.get("/analysis/cycles")
def import_cycles() -> dict:
    return {"cycles": find_import_cycles(graph_repository)}


@router.get("/analysis/unused-functions", response_model=list[Node])
def unused_functions() -> list[Node]:
    return find_unused_functions(graph_repository)


@router.get("/analysis/call-chain")
def call_chain(src: str, dst: str) -> dict:
    return {"path": find_call_chain(graph_repository, src, dst)}
