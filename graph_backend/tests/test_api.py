from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_api_build_graph_and_query_sample_project() -> None:
    sample_root = Path(__file__).resolve().parent / "runtime_data" / "api"
    (sample_root / "main.py").write_text(
        "def run():\n    return process_order()\n\n"
        "def process_order():\n    return 'ok'\n\n"
        "def unused_entrypoint():\n    return None\n",
        encoding="utf-8",
    )
    client = TestClient(create_app())

    response = client.post("/build-graph", json={"folder_path": str(sample_root)})
    assert response.status_code == 200
    graph = response.json()
    assert graph["nodes"]
    assert graph["edges"]
    assert graph["metadata"]["storage_dir"].endswith(".codebase-graph")
    assert graph["metadata"]["status"] in {"full_rebuild", "incremental", "cache_hit"}

    search = client.get("/search", params={"query": "process_order"})
    assert search.status_code == 200
    assert any(node["properties"]["name"] == "process_order" for node in search.json())

    unused = client.get("/analysis/unused-functions")
    assert unused.status_code == 200
    assert any(node["properties"]["name"] == "unused_entrypoint" for node in unused.json())
