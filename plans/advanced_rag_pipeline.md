# Feature: Advanced Hybrid & Graph RAG Pipeline with Ragas Evaluation

**Date:** 2026-05-26
**Status:** 🔲 Planned

## Description

Implement a state-of-the-art RAG pipeline for the Multi-Agent Research System using **LlamaIndex** (for data ingestion, parsing, chunking, and dual-indexing) and **Ragas** (for dynamic LLM-as-a-judge evaluation). To keep the repository highly pedagogical and accessible for students from diverse backgrounds (CS and Management), the design enforces strict **hyper-modularity** (no Python file over 50 lines), **package-first utility** (no custom search/index math), and **zero-friction local setups** with automatic database fallbacks (local ChromaDB and JSON graph stores).

## Checklist

- [ ] **Step 1: Hot-Folder Ingestion & Classification (`backend/rag/classifier.py`)**
  - Configure the strictly self-contained directory structures: `backend/rag/data/need-processing/` for incoming files and `backend/rag/data/processed/` for completed files.
  - Implement dynamic document classification that scans raw files inside `backend/rag/data/need-processing/` and categorizes them (YouTube transcripts, clean paragraphs, or messy logs) before parsing.
- [ ] **Step 2: Hyper-Modular Parsing (`backend/rag/parser.py`)**
  - Implement a dynamic chunking switch in LlamaIndex to apply one of the **Top 5 Chunking Strategies** based on the classified file type (e.g., MarkdownNodeParser for docs, SentenceSplitter for clean text, SemanticSplitter for essays, TokenTextSplitter as fallback, and Hierarchical for dense reference reports). Apply dynamic metadata tags (file category, source, dates).
  - **The Top 5 Chunking Strategies to Implement**:
    1. **Fixed-Size Token Chunking (`TokenTextSplitter`)**: Splits text strictly by token size (e.g., 512 tokens) with an overlap window (e.g., 50 tokens). Fast but prone to splitting sentences.
    2. **Recursive Character Chunking (`SentenceSplitter`)**: Splits along nested priority delimiters (`\n\n`, `\n`, ` `, `""`) to keep paragraphs and sentences whole.
    3. **Semantic Chunking (`SemanticSplitterNodeParser`)**: Splits when semantic similarity between consecutive sentences falls below a percentile threshold. Coherent but requires embeddings.
    4. **Hierarchical (Parent-Child) Chunking (`HierarchicalNodeParser`)**: Indexes small overlap chunks (child nodes) for precision search but retrieves larger context blocks (parent nodes) for generation.
    5. **Structural / Layout-Aware Chunking (`MarkdownNodeParser` / `HTMLNodeParser`)**: Splits along formatting rules (like `#` header tags in markdown) to group sections cleanly.
- [ ] **Step 3: Storage Context & Upgrades (`backend/rag/store.py`)**
  - Setup local persistent ChromaDB client for vector storage.
  - Setup `SimpleGraphStore` (local JSON) with automatic upgrade to `Neo4jGraphStore` if credentials exist in `.env`.
  - **Dynamic Ingestion Logic**:
    - Default to LlamaIndex's local `SimpleGraphStore` if `NEO4J_URI` is not present in `.env`.
    - If `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` are present, dynamically initialize `Neo4jGraphStore` to upgrade the pipeline to the cloud graph DB without breaking local setups.
- [ ] **Step 4: Unified Ingestion Pipeline (`backend/rag/indexer.py`)**
  - Setup and execute a single native LlamaIndex `IngestionPipeline` to run all parsing, chunking, metadata extraction, and embedding transformations in one unified run.
  - **LlamaIndex Class Integration**:
    - Import and compose the dynamic **chunker/parser** (from `parser.py`), the classified **metadata stamper** (from `classifier.py`), and the **embedding model** (e.g., `Settings.embed_model` or `OpenAIEmbedding`) as `transformations` inside a single `IngestionPipeline`.
    - Run the pipeline with `pipeline.run(documents=documents)` to generate final fully-embedded, metadata-stamped nodes.
    - Insert the processed nodes directly into the local `ChromaVectorStore` and `SimpleGraphStore` / `Neo4jGraphStore` storage context, and write the index to persistence storage.
  - **Post-Ingestion Hot-Folder Cleanup**:
    - Once the database persistence completes successfully, use Python's `shutil.move()` to move all successfully processed raw files from `backend/rag/data/need-processing/` to `backend/rag/data/processed/` to keep the ingestion directory empty for future batches.
- [ ] **Step 5: Advanced Query Translation (`backend/rag/query_transform.py`)**
  - Implement HyDE (Hypothetical Document Embeddings) and query rephrasing using pure native LlamaIndex classes.
  - **LlamaIndex Class Integration**:
    - Use `HyDEQueryTransform(include_original=True)` to convert the incoming query into a hypothetical model-generated answer before vector lookup.
    - Wrap the core query engine in a `TransformQueryEngine` to automatically intercept queries and apply the HyDE transformation.
- [ ] **Step 6: Retrieval, Fusion & Reranking (`backend/rag/retriever.py`)**
  - Implement hybrid retriever routing queries across BM25, Vector, and Graph RAG, merging, and reranking the results using native LlamaIndex classes—all within a single, highly cohesive file under 50 lines.
  - **LlamaIndex Class Integration**:
    - Configure standard vector retrievers with `vector_index.as_retriever(similarity_top_k=10)`.
    - Setup keyword retrieval with `BM25Retriever.from_defaults` targeting the document nodes.
    - Unify vector and keyword search with `QueryFusionRetriever`. Configure it to expand queries natively using the LLM (`num_queries=3`) and perform Reciprocal Rank Fusion (`mode="reciprocal_rerank"`).
    - Setup `KGTableRetriever` with `retriever_mode="keyword"` to perform multi-hop entity-relation path traversals on the Graph Index.
    - Combine the outputs of the fused BM25/Vector retrieval and the Graph retrieval.
    - Use the native LlamaIndex `LLMRerank` postprocessor, configuring it to process in chunks of 5 (`choice_batch_size=5`) and limit output to the top 3 best nodes (`top_n=3`) to return the final pruned context.
- [ ] **Step 7: Orchestrator Integration (`backend/orchestrator.py`)**
  - Hook the RAG pipeline into the `Reader` agent node, replacing simple search snippets with rich, retrieved document context.
- [ ] **Step 8: Ragas Evaluation (`backend/rag/rag_eval.py`)**
  - Implement Ragas evaluation suite measuring Faithfulness, Answer Relevance, Context Precision, and Context Recall.
- [ ] **Step 9: API & UI Metrics Exposure (`backend/api.py` & `frontend/index.js`)**
  - Expose Ragas evaluation scores to the frontend to render dynamic quality metrics for each research answer.
- [ ] **Step 10: End-to-End RAG & Ragas Pipeline Verification (`backend/rag/test_pipeline.py`)**
  - Create a dedicated validation script to programmatically verify that ingestion, classification, fallbacks, retrieval, and Ragas evaluations work flawlessly as a single cohesive lifecycle.
  - **Verification Steps**:
    1. **Create Test File**: Create a custom document (e.g., `backend/rag/data/need-processing/test_physics_agent.txt` containing obscure custom facts such as *"The Antigravity Research Propulsion Core relies on secondary thermal fusion cells for gravity deflection"*).
    2. **Execute Ingestion**: Run the unified `IngestionPipeline` programmatically and assert that the source file is successfully indexed and automatically moved to `backend/rag/data/processed/`.
    3. **Query & Retrieval Verification**: Query the hybrid retriever with words related *only* to the test file (e.g., *"What does the propulsion core rely on?"*) and assert that the custom facts successfully appear in the retrieved nodes.
    4. **Evaluate with Ragas**: Run the full Ragas scorecard (Faithfulness, Recall, Precision, Relevance) on the context, question, and generated answer, asserting that all scores are returned successfully as valid float metrics between `0.00` and `1.00`.

## Files to be Created/Modified

| File | Action | What Changed / Description |
|------|--------|-------------|
| `backend/requirements.txt` | Modified | Add dependencies (`llama-index`, `llama-index-vector-stores-chroma`, `llama-index-graph-stores-neo4j`, `ragas`, `chromadb`) |
| `backend/rag/__init__.py` | Created | Exports high-level query and index pipelines |
| `backend/rag/classifier.py` | Created | Dynamic content classification logic (<35 lines) |
| `backend/rag/parser.py` | Created | LlamaIndex parsing and metadata stamping (<40 lines) |
| `backend/rag/store.py` | Created | Storage context config with ChromaDB and Neo4j fallback (<45 lines) |
| `backend/rag/indexer.py` | Created | Unified vector, keyword, and graph index build engine (<30 lines) |
| `backend/rag/query_transform.py` | Created | HyDE and multi-query prompt generation wrapper (<35 lines) |
| `backend/rag/retriever.py` | Created | End-to-end retrieval, BM25/Vector fusion, Graph traversal, and LLMRerank pipeline (<48 lines) |
| `backend/rag/rag_eval.py` | Created | Ragas validation framework and score exporter (<45 lines) |
| `backend/rag/test_pipeline.py` | Created | Automated end-to-end pipeline integration test and Ragas asserter (<48 lines) |
| `backend/rag/data/need-processing/test_physics_agent.txt` | Created | Custom obscure fact-filled file used to validate the end-to-end RAG retrieval |
| `backend/api.py` | Modified | Hook up dynamic RAG context retrieval and evaluation metrics |
| `frontend/index.js` | Modified | Update UI to render Ragas scorecard (0.00 to 1.00) on completions |

## Notes

- **The 50-Line Constraint**: Every newly created python module inside `backend/rag/` must strictly adhere to the <50 lines rule to prevent overwhelming students.
- **Dependency Isolation**: All indexing and traversal details are handled by `llama-index` packages, removing raw algorithmic math from the educational codebase.
- **Graceful Neo4j Degradation**: If `NEO4J_URI` is absent from `.env`, the system automatically runs the local `SimpleGraphStore` without errors or crashes.
