# Codebase Graph Visualizer - Backend API

This is the backend API for the Codebase Graph Visualizer. It is responsible for statically analyzing Python codebases, building relationship graphs (files, classes, functions), and serving this data to the frontend along with advanced graph analysis tools.

## Features
- **Codebase Parsing**: Scans a provided folder path and parses Python abstract syntax trees (ASTs) to map out functions, classes, and their relationships.
- **Graph Generation**: Identifies structural edges, including:
  - Which files import which other files/modules.
  - Which functions call which other functions.
- **Static Analysis Endpoints**:
  - `GET /analysis/cycles`: Detects cyclic imports or calls within the generated graph.
  - `GET /analysis/unused-functions`: Identifies functions that have no incoming "CALLS" references across the analyzed codebase.
  - `GET /analysis/call-chain`: Calculates the execution path between two specific functions.

## Tech Stack
- Python 3
- [FastAPI](https://fastapi.tiangolo.com/)

## Setup & Running Locally

1. **Environment Setup**
   Ensure you have Python 3 installed. It is recommended to create a virtual environment:
   ```bash
   cd graph_backend
   python -m venv .venv
   
   # On Windows:
   .venv\Scripts\activate
   
   # On macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install Requirements**
   Install the dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the API Server**
   Run the FastAPI application via `uvicorn`:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Verify the API**
   The backend should now be running. You can check the health endpoint at `http://localhost:8000/health` (if implemented) or navigate to the interactive Swagger UI docs at `http://localhost:8000/docs` to see all available API routes.
