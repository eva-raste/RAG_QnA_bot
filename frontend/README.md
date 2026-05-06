# Codebase Graph Visualizer - Frontend

This is the frontend component for the Codebase Graph Visualizer, built to interactively render and analyze the dependency structures of Python projects.

## Features
- **Interactive Graph Rendering**: Uses [Cytoscape.js](https://js.cytoscape.org/) to visualize files, classes, and functions and the "imports" / "calls" relationships between them.
- **Project Building**: Tell the backend which folder to scan, and dynamically load the generated graph.
- **Graph Analysis**:
  - Automatically identifies import cycles in the parsed project.
  - Highlights unused functions (functions with no incoming "CALLS" edges).
  - Finds call chains (paths) between a specific source and target function.
- **Search & Inspection**: Search for specific nodes and click on nodes to inspect their details, incoming edges, and outgoing edges.
- **Theming**: Native support for light and dark modes (automatically matching system preference, or toggleable).

## Tech Stack
- React 19
- TypeScript
- Vite
- Cytoscape.js

## Setup & Running Locally

1. **Install Dependencies**
   Navigate to the `frontend` directory and install the necessary npm packages:
   ```bash
   npm install
   ```

2. **Run the Development Server**
   Start the Vite dev server:
   ```bash
   npm run dev
   ```

3. **View the Application**
   Open your browser and navigate to `http://localhost:5173`. Make sure the `graph_backend` API is also running (defaulting to `http://localhost:8000`) for data fetching to work correctly.
