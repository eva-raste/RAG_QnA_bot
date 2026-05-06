import type {
  BuildGraphResponse,
  GraphNode,
  GraphResponse,
  NodeDetails,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText);
  }
  return response.json() as Promise<T>;
}

export function buildGraph(
  folderPath: string,
  forceRebuild = false,
): Promise<BuildGraphResponse> {
  return request<BuildGraphResponse>("/build-graph", {
    method: "POST",
    body: JSON.stringify({ folder_path: folderPath, force_rebuild: forceRebuild }),
  });
}

export function fetchGraph(): Promise<GraphResponse> {
  return request<GraphResponse>("/graph");
}

export function fetchNode(nodeId: string): Promise<NodeDetails> {
  return request<NodeDetails>(`/node/${encodeURIComponent(nodeId)}`);
}

export function searchNodes(query: string): Promise<GraphNode[]> {
  return request<GraphNode[]>(`/search?query=${encodeURIComponent(query)}`);
}

export function fetchCycles(): Promise<{ cycles: string[][] }> {
  return request<{ cycles: string[][] }>("/analysis/cycles");
}

export function fetchUnusedFunctions(): Promise<GraphNode[]> {
  return request<GraphNode[]>("/analysis/unused-functions");
}

export function fetchCallChain(
  src: string,
  dst: string,
): Promise<{ path: string[] | null }> {
  const params = new URLSearchParams({ src, dst });
  return request<{ path: string[] | null }>(`/analysis/call-chain?${params}`);
}
