export type NodeType = "file" | "class" | "function";
export type EdgeType = "CALLS" | "IMPORTS" | "DEFINES";

export interface GraphNode {
  id: string;
  type: NodeType;
  properties: Record<string, string | number | null | undefined>;
}

export interface GraphEdge {
  src: string;
  dst: string;
  type: EdgeType;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface BuildMetadata {
  status: "cache_hit" | "incremental" | "full_rebuild";
  storage_dir: string;
  files_added: number;
  files_changed: number;
  files_deleted: number;
  files_unchanged: number;
}

export interface BuildGraphResponse extends GraphResponse {
  metadata: BuildMetadata;
}

export interface NodeDetails {
  node: GraphNode;
  outgoing_neighbors: GraphNode[];
  incoming_neighbors: GraphNode[];
  connected_edges: GraphEdge[];
}
