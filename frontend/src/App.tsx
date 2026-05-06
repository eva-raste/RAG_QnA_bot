import cytoscape, { Core, ElementDefinition } from "cytoscape";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  buildGraph,
  fetchCallChain,
  fetchCycles,
  fetchGraph,
  fetchNode,
  fetchUnusedFunctions,
  searchNodes,
} from "./api";
import type { GraphNode, GraphResponse, NodeDetails } from "./types";

const typeColor: Record<string, string> = {
  file: "#2563eb",
  class: "#d97706",
  function: "#059669",
};

function App() {
  const cyRef = useRef<Core | null>(null);
  const graphRef = useRef<HTMLDivElement | null>(null);
  const [folderPath, setFolderPath] = useState("sample_project");
  const [forceRebuild, setForceRebuild] = useState(false);
  const [graph, setGraph] = useState<GraphResponse>({ nodes: [], edges: [] });
  const [selected, setSelected] = useState<NodeDetails | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<GraphNode[]>([]);
  const [cycles, setCycles] = useState<string[][]>([]);
  const [unused, setUnused] = useState<GraphNode[]>([]);
  const [chainSource, setChainSource] = useState("");
  const [chainTarget, setChainTarget] = useState("");
  const [callChain, setCallChain] = useState<string[] | null>(null);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    return (localStorage.getItem("theme") as "light" | "dark") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const getCyStyle = (isDark: boolean): any[] => [
    {
      selector: "node",
      style: {
        "background-color": (ele: any) => typeColor[ele.data("type")] ?? (isDark ? "#475569" : "#64748b"),
        label: "data(label)",
        color: isDark ? "#f8fafc" : "#111827",
        "font-size": "10px",
        "text-valign": "bottom",
        "text-margin-y": 6,
        "text-wrap": "wrap",
        "text-max-width": "120px",
        width: "24px",
        height: "24px",
        "border-width": 2,
        "border-color": isDark ? "#1e293b" : "#ffffff",
      },
    },
    {
      selector: "edge",
      style: {
        width: "1.5px",
        "line-color": isDark ? "#475569" : "#94a3b8",
        "target-arrow-color": isDark ? "#475569" : "#94a3b8",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        label: "data(label)",
        "font-size": "9px",
        color: isDark ? "#94a3b8" : "#475569",
        "text-background-color": isDark ? "#1e293b" : "#ffffff",
        "text-background-opacity": 0.85,
        "text-background-padding": "2px",
      },
    },
    {
      selector: ".dimmed",
      style: { opacity: 0.16 },
    },
    {
      selector: ".highlighted",
      style: {
        opacity: 1,
        "border-width": 4,
        "border-color": isDark ? "#f8fafc" : "#111827",
        "line-color": isDark ? "#f8fafc" : "#111827",
        "target-arrow-color": isDark ? "#f8fafc" : "#111827",
      },
    },
  ];

  const elements = useMemo<ElementDefinition[]>(() => {
    const nodeElements = graph.nodes.map((node) => ({
      data: {
        id: node.id,
        label: node.properties.qualified_name ?? node.properties.name ?? node.id,
        type: node.type,
      },
    }));
    const edgeElements = graph.edges.map((edge, index) => ({
      data: {
        id: `${edge.src}-${edge.type}-${edge.dst}-${index}`,
        source: edge.src,
        target: edge.dst,
        label: edge.type,
      },
    }));
    return [...nodeElements, ...edgeElements];
  }, [graph]);

  useEffect(() => {
    fetchGraph()
      .then((nextGraph) => {
        setGraph(nextGraph);
        if (nextGraph.nodes.length) {
          setStatus(`Loaded ${nextGraph.nodes.length} nodes`);
        }
      })
      .catch(() => {
        setStatus("No persisted graph loaded");
      });
  }, []);

  useEffect(() => {
    if (!graphRef.current) {
      return;
    }
    cyRef.current?.destroy();
    const isDark = theme === "dark";
    const cy = cytoscape({
      container: graphRef.current,
      elements,
      layout: { name: "cose", animate: false, padding: 42 },
      minZoom: 0.2,
      maxZoom: 2.5,
      style: getCyStyle(isDark),
    });
    cy.on("tap", "node", (event) => {
      const nodeId = event.target.id();
      selectNode(nodeId);
    });
    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [elements]);

  useEffect(() => {
    if (cyRef.current) {
      cyRef.current.style(getCyStyle(theme === "dark"));
    }
  }, [theme]);

  async function refreshAnalysis() {
    const [nextCycles, nextUnused] = await Promise.all([
      fetchCycles(),
      fetchUnusedFunctions(),
    ]);
    setCycles(nextCycles.cycles);
    setUnused(nextUnused);
  }

  async function handleBuild(event: FormEvent) {
    event.preventDefault();
    setError("");
    setStatus("Building graph...");
    try {
      const nextGraph = await buildGraph(folderPath, forceRebuild);
      setGraph(nextGraph);
      setSelected(null);
      setSearchResults([]);
      await refreshAnalysis();
      const metadata = nextGraph.metadata;
      setStatus(
        `${metadata.status}: ${nextGraph.nodes.length} nodes, ${nextGraph.edges.length} edges, ` +
        `${metadata.files_added} added, ${metadata.files_changed} changed, ` +
        `${metadata.files_deleted} deleted, ${metadata.files_unchanged} unchanged`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to build graph");
      setStatus("Build failed");
    }
  }

  async function handleSearch(query: string) {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      setSearchResults(await searchNodes(query));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    }
  }

  async function selectNode(nodeId: string) {
    try {
      const details = await fetchNode(nodeId);
      setSelected(details);
      highlightNode(nodeId);
      setChainSource((current) => current || nodeId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Node lookup failed");
    }
  }

  function highlightNode(nodeId: string) {
    const cy = cyRef.current;
    if (!cy) {
      return;
    }
    const node = cy.getElementById(nodeId);
    const connected = node.closedNeighborhood();
    cy.elements().addClass("dimmed").removeClass("highlighted");
    connected.removeClass("dimmed").addClass("highlighted");
    node.removeClass("dimmed").addClass("highlighted");
    cy.animate({ center: { eles: node }, zoom: Math.max(cy.zoom(), 1.1) }, { duration: 250 });
  }

  async function runCallChain() {
    if (!chainSource || !chainTarget) {
      return;
    }
    try {
      const result = await fetchCallChain(chainSource, chainTarget);
      setCallChain(result.path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Call chain lookup failed");
    }
  }

  const functionNodes = graph.nodes.filter((node) => node.type === "function");

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h1>Codebase Graph Visualizer</h1>
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              type="button"
              className="theme-toggle"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
          </div>
          <p>{status}</p>
        </div>
        <form className="build-form" onSubmit={handleBuild}>
          <input
            value={folderPath}
            onChange={(event) => setFolderPath(event.target.value)}
            aria-label="Project folder path"
          />
          <label className="force-toggle">
            <input
              checked={forceRebuild}
              onChange={(event) => setForceRebuild(event.target.checked)}
              type="checkbox"
            />
            Force
          </label>
          <button type="submit">Build Graph</button>
        </form>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="workspace">
        <aside className="sidebar">
          <label className="field">
            <span>Search</span>
            <input
              value={searchQuery}
              onChange={(event) => handleSearch(event.target.value)}
              placeholder="name, path, or type"
            />
          </label>
          <div className="result-list">
            {searchResults.slice(0, 12).map((node) => (
              <button key={node.id} onClick={() => selectNode(node.id)}>
                <strong>{String(node.properties.qualified_name ?? node.properties.name)}</strong>
                <span>{node.type}</span>
              </button>
            ))}
          </div>

          <section className="panel">
            <h2>Node Details</h2>
            {selected ? (
              <div className="details">
                <strong>{String(selected.node.properties.qualified_name ?? selected.node.properties.name)}</strong>
                <span>{selected.node.type}</span>
                <code>{selected.node.id}</code>
                <h3>Outgoing</h3>
                {selected.outgoing_neighbors.map((node) => (
                  <button key={node.id} onClick={() => selectNode(node.id)}>
                    {String(node.properties.qualified_name ?? node.properties.name)}
                  </button>
                ))}
                <h3>Incoming</h3>
                {selected.incoming_neighbors.map((node) => (
                  <button key={node.id} onClick={() => selectNode(node.id)}>
                    {String(node.properties.qualified_name ?? node.properties.name)}
                  </button>
                ))}
              </div>
            ) : (
              <p>Select a graph node.</p>
            )}
          </section>
        </aside>

        <div className="graph-panel">
          <div className="legend">
            <span><i className="file" />file</span>
            <span><i className="class" />class</span>
            <span><i className="function" />function</span>
          </div>
          <div ref={graphRef} className="graph-canvas" />
        </div>

        <aside className="analysis">
          <section className="panel">
            <h2>Import Cycles</h2>
            {cycles.length ? (
              cycles.map((cycle) => <code key={cycle.join("->")}>{cycle.join(" -> ")}</code>)
            ) : (
              <p>No cycles loaded.</p>
            )}
          </section>

          <section className="panel">
            <h2>Unused Functions</h2>
            {unused.slice(0, 10).map((node) => (
              <button key={node.id} onClick={() => selectNode(node.id)}>
                {String(node.properties.qualified_name ?? node.properties.name)}
              </button>
            ))}
          </section>

          <section className="panel">
            <h2>Call Chain</h2>
            <select value={chainSource} onChange={(event) => setChainSource(event.target.value)}>
              <option value="">Source</option>
              {functionNodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {String(node.properties.qualified_name ?? node.properties.name)}
                </option>
              ))}
            </select>
            <select value={chainTarget} onChange={(event) => setChainTarget(event.target.value)}>
              <option value="">Target</option>
              {functionNodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {String(node.properties.qualified_name ?? node.properties.name)}
                </option>
              ))}
            </select>
            <button onClick={runCallChain}>Find Chain</button>
            {callChain && <code>{callChain.join(" -> ")}</code>}
            {callChain === null && chainSource && chainTarget && <p>No chain selected or found.</p>}
          </section>
        </aside>
      </section>
    </main>
  );
}

export default App;
