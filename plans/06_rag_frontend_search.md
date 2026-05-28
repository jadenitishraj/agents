# 🔍 Plan: RAG Document Search Frontend

Upload a file → index it → ask questions → get **pure retrieval results** (top 5 chunks with citations, **no LLM generation**).

---

## What exists today

| Layer | Current state |
|-------|---------------|
| **Backend RAG pipeline** | Full hybrid pipeline in `backend/rag/` (classifier → parser → store → indexer → retriever). Currently only triggered by the `/research` endpoint which feeds web-search sources into RAG. No standalone "upload a file and search" endpoint. |
| **Frontend** | Single page (`frontend/index.html`) with one text input hitting `POST /research`. No file upload, no separate RAG page. |
| **File ingestion** | Hot-folder system exists (`folders.py`, `ingestion.py`). Files placed in `backend/rag/data/need-processing/` get picked up by `load_local_sources()`. |

## What we need to build

### 1. Two new API endpoints in `backend/api.py`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rag/upload` | `POST` (multipart) | Accept a PDF/TXT/MD file upload, save it to the hot-folder, run the full indexing pipeline (classify → parse → embed → store in ChromaDB), return a `corpus_id` and chunk count. |
| `/rag/search` | `POST` (JSON) | Accept `{ "query": "...", "top_k": 5 }`, run **retrieval only** (BM25 + Vector fusion + rerank), return top 5 chunks with text, relevance score, source filename, and chunk metadata. **No LLM generation call.** |

### 2. Backend: retrieval-only function (no answer generation)

"No LLM call" means **no LLM to synthesize a final answer**. The retrieval pipeline keeps all its intelligence:

- ✅ **HyDE stays** — LLM expands the query into a hypothetical answer for better embedding search
- ✅ **Multi-query fusion stays** — LLM rewrites the query into 3 variants
- ✅ **BM25 + Vector fusion stays** — hybrid keyword + semantic retrieval
- 🔄 **Reranker: swap `LLMRerank` → BERT cross-encoder** — the current `LLMRerank` sends every chunk to GPT-4o-mini which is slow and expensive. A local **cross-encoder** (`cross-encoder/ms-marco-MiniLM-L-6-v2`) runs on CPU, is free, faster (~50ms vs ~2s), and is actually more accurate for relevance scoring since it was specifically trained for that task.
- ❌ **No answer synthesis** — we return the raw top 5 chunks with scores and citations, no LLM writes a paragraph.

**Changes:**

1. **Edit `backend/rag/retriever.py`** — swap `LLMRerank` → `SentenceTransformerRerank`:
   ```python
   from llama_index.core.postprocessor import SentenceTransformerRerank
   reranker = SentenceTransformerRerank(
       model="cross-encoder/ms-marco-MiniLM-L-6-v2", top_n=5
   )
   ```

2. **New file `backend/rag/search.py`** (~40 lines) — `search_corpus(corpus, query, top_k=5)`:
   - Calls existing `build_query_bundle()` (HyDE)
   - Runs BM25 + Vector fusion
   - Runs cross-encoder rerank
   - Returns list of `{ text, score, title, chunk_strategy, category }` — no answer generation

3. **Add `sentence-transformers` to `backend/requirements.txt`** (needed for the cross-encoder model)

### 3. In-memory corpus registry

The current flow builds a corpus per request and throws it away. For the search feature we need to keep the indexed corpus alive in memory so multiple queries can hit it.

New file: **`backend/rag/registry.py`** (~25 lines)
- Simple module-level dict: `_corpora: dict[str, IndexedCorpus] = {}`
- `register(corpus_id, corpus)` / `get(corpus_id)` / `list_ids()`

### 4. Frontend: new RAG search page

New file: **`frontend/rag.html`** — standalone page, same dark theme as `index.html`.

UI sections:
1. **Upload area** — drag-and-drop or click to pick a PDF/TXT/MD file. Shows progress + chunk count after indexing.
2. **Search bar** — text input + "Search" button (only enabled after a file is indexed).
3. **Results panel** — top 5 cards, each showing:
   - Relevance score badge (e.g. `0.87`)
   - Source filename
   - Category + chunk strategy pills
   - Full chunk text (expandable if long)

New file: **`frontend/rag.js`** — handles upload fetch, search fetch, result rendering.

### 5. Test with a dummy PDF

- Create a small test PDF (`backend/rag/tests/test_doc.pdf`) containing 2-3 pages of known facts (e.g. "Company XYZ was founded in 2019 in Bangalore").
- Upload it via curl: `curl -F "file=@test_doc.pdf" http://localhost:8000/rag/upload`
- Query it: `curl -X POST http://localhost:8000/rag/search -H "Content-Type: application/json" -d '{"query": "When was Company XYZ founded?"}'`
- Verify the top result contains the correct chunk.

---

## File changes summary

| File | Action |
|------|--------|
| `backend/rag/search.py` | **New** — pure retrieval function (no LLM) |
| `backend/rag/registry.py` | **New** — in-memory corpus store |
| `backend/api.py` | **Edit** — add `/rag/upload` and `/rag/search` endpoints |
| `frontend/rag.html` | **New** — upload + search UI page |
| `frontend/rag.js` | **New** — frontend logic for RAG page |
| `backend/rag/tests/test_doc.pdf` | **New** — dummy PDF for testing |

---

## Execution order

- [ ] 1. Create `backend/rag/registry.py` (in-memory corpus store)
- [ ] 2. Create `backend/rag/search.py` (pure retrieval, no LLM rerank)
- [ ] 3. Add `/rag/upload` and `/rag/search` endpoints to `backend/api.py`
- [ ] 4. Create `frontend/rag.html` and `frontend/rag.js`
- [ ] 5. Generate a dummy test PDF, start the server, upload via curl, search via curl
- [ ] 6. Run Ragas scorecard evaluation against the same PDF — feed the retrieved contexts + a known ground-truth answer into `scorecard.py` and verify all 4 scores (Faithfulness, Answer Relevance, Context Precision, Context Recall) are above 0.7
- [ ] 6. Open the frontend page in the browser and do a visual test
