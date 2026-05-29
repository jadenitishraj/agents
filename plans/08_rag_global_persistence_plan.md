# Global Persistent RAG Refactor Plan

## Context & Objective
The current RAG system is ephemeral: every time a question is asked, it creates a temporary, isolated database just for that question. The goal is to completely decouple **Uploading** (Ingestion) from **Searching** (Retrieval) by shifting to a **Global Persistent Database**. 

Additionally, we will remove all Pydantic/Dataclass structures (the `models.py` file) to keep the data flow as raw, simple Python dictionaries.

## Step 1: Remove Pydantic Models & Simplify Structures
- **Action**: Delete `backend/rag/models.py`.
- **Action**: Refactor `parser.py`, `chunker.py`, `indexer.py`, `pipeline.py`, and `retriever.py` to use standard Python `dict` and `list` instead of `IndexedCorpus`, `Source`, `ClassifiedSource`, and `StorageBundle`.
- **Goal**: Make the code purely functional with basic Python types, avoiding unnecessary class overhead.

## Step 2: Establish the Global Database (Indexer)
- **Action**: Update `indexer.py` to target a single, persistent folder: `backend/rag/.storage/global_db`.
- **Action**: The vector index (ChromaDB) and graph index (SimpleGraphStore) will permanently save to this global folder.
- **Action**: **BM25 Persistence**: We will create a dedicated `bm25_index.json` file inside the global storage. When new chunks are indexed, their text and metadata will be appended to this file so the BM25 retriever can instantly reconstruct its full index on server restart.

## Step 3: Decouple Ingestion (The Upload Pipeline)
- **Action**: In `pipeline.py`, replace `build_corpus` with `ingest_document(file_path: str) -> dict`.
- **Flow**:
  1. **Loader**: Read the uploaded file.
  2. **Parser**: Classify the document type.
  3. **Chunker**: Split the document using the dynamic strategies.
  4. **Indexer**: Run the chunks through OpenAI to get embeddings, and insert them into the global ChromaDB, the global Graph store, and append to the `bm25_index.json` file.
- **Action**: Add a `POST /ingest` endpoint in `api.py` that triggers this pipeline.

## Step 4: Decouple Retrieval (The Search Pipeline)
- **Action**: In `pipeline.py`, update `read_with_rag(query: str) -> dict`.
- **Flow**:
  1. The function immediately connects to the existing global `VectorStoreIndex`, `KnowledgeGraphIndex`, and loads nodes from `bm25_index.json` to initialize the `BM25Retriever`.
  2. Runs HyDE, Hybrid Fusion, and LLM Reranking against the *entire* database.
  3. Evaluates with Ragas (if needed).
  4. Returns a simple dictionary with the answer, contexts, and citations.
- **Action**: Ensure the `POST /research` (or `/search`) endpoint simply calls this function without any indexing steps.

## Step 5: Update the Frontend UI
- **Action**: Update `rag.html` (or create a new `index.html`) to have two distinct tabs:
  - **Upload Tab**: A simple file uploader that calls `POST /ingest`. Once uploaded, it shows a success message.
  - **Search Tab**: A search bar that calls `POST /search`. It searches the entire global database and returns the RAG answer.
- **Action**: Update `rag.js` to handle the two isolated workflows (uploading vs searching).

## Completion Criteria
1. `models.py` is completely deleted and no Pydantic models remain in the RAG module.
2. Indexing a file permanently stores it in `.storage/global_db`.
3. A clear, explicit `bm25_index.json` file exists on the hard drive alongside Chroma and the graph store.
4. Searching queries all previously uploaded documents, not just the current session.
5. The frontend cleanly separates the Upload and Search experiences.
