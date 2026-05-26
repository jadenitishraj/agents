# Feature: Interactive RAG Pedagogical Jupyter Notebook

**Date:** 2026-05-26
**Status:** 🔲 Planned

## Description

To enhance student learning, we will package the entire Advanced Hybrid & Graph RAG pipeline into a single, self-contained interactive Jupyter Notebook (`backend/rag/interactive_rag_notebook.ipynb`). This notebook will act as a step-by-step laboratory for CS and Management students, allowing them to upload their own files (PDFs, Markdown, or Text), execute each pipeline stage incrementally, inspect intermediate outputs (classification, chunking strategy, vector indexes, knowledge graph triplets, HyDE queries, fusion scores, and reranked nodes), run live Ragas evaluations, and interact with a beautiful, dynamic Search Box interface powered by `ipywidgets`.

## Checklist

- [ ] **Step 1: Environment & Dependency Setup**
  - Verify and list notebook-friendly dependencies (`ipywidgets`, `pypdf`, `pandas`, `ipython`) inside the setup cell.
  - Initialize the local `.env` loader and configure LlamaIndex LLM/Embedding settings locally.
- [ ] **Step 2: Interactive File Upload Interface**
  - Use `ipywidgets.FileUpload` to render a beautiful file uploader button inside the notebook.
  - Automatically write the uploaded file (PDF, TXT, or MD) to the strictly self-contained `backend/rag/data/need-processing/` hot-folder directory.
- [ ] **Step 3: Step-by-Step Parsing & Classification Visualizer**
  - Create cells to trigger the dynamic classification logic and inspect the detected category.
  - Run the parser on the uploaded document and render the chunked text blocks along with their metadata tags in an interactive pandas DataFrame for easy inspection.
- [ ] **Step 4: Vector & Graph Storage Visualizer**
  - Initialize ChromaDB and the fallback Knowledge Graph Index.
  - Extract and display the generated entity-relation-entity triplets from the graph store, demonstrating how unstructured text is mapped into structural graph connections.
- [ ] **Step 5: Query Translation (HyDE) Inspector**
  - Let students type a sample query.
  - Run the `HyDEQueryTransform` and print the expanded hypothetical answer and the generated sub-queries side-by-side.
- [ ] **Step 6: Hybrid Fusion (RRF) & Graph Retrieval Inspector**
  - Execute dense vector retrieval, BM25 keyword retrieval, and Graph keyword retrieval separately.
  - Render the intermediate candidate nodes and demonstrate how Reciprocal Rank Fusion (RRF) blends sparse and dense retrieval lists.
- [ ] **Step 7: Reranking & Context Pruning Inspector**
  - Execute `LLMRerank` on the candidate list.
  - Print a "Before vs. After" comparison showcasing how 10 candidate chunks are pruned down to the 3 most context-dense nodes to minimize LLM token costs.
- [ ] **Step 8: Live Ragas Scorecard Evaluation**
  - Run the Faithfulness, Answer Relevance, Context Precision, and Context Recall metrics using Ragas on the generated response.
  - Output the results in a beautiful, styled pandas scorecard table showing real-time quality scores between `0.00` and `1.00`.
- [ ] **Step 9: Final Dynamic Search Box UI**
  - Use `ipywidgets` to create a beautiful, rich search terminal within the notebook cell consisting of a search box, query button, and output tabs (Answer, Citations, Ragas Metrics, Ingestion Stats).
  - Pressing search runs the entire pipeline end-to-end and renders all RAG metadata dynamically inside the widget.

## Files Touched

| File | Action | Description |
|------|--------|-------------|
| `backend/rag/interactive_rag_notebook.ipynb` | Created | Single self-contained step-by-step jupyter notebook with file upload and search box widgets |
| `plans/rag_interactive_notebook.md` | Created | THIS FILE — Interactive pedagogical RAG notebook plan |

## Notes

- **Self-Contained Rule**: The `.ipynb` notebook file must live strictly inside `backend/rag/` to prevent cluttering the main workspace.
- **Student-Friendly Widgets**: No complex web-app server required. All user-interactions (uploading documents and executing searches) are handled natively inside the Jupyter runtime using `ipywidgets`.
- **Pedagogical Progressions**: Each cell will be richly commented to guide students through *why* we combine Dense-Sparse embeddings and *how* reranking optimizes LLM response precision.
