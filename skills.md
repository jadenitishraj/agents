# Student Development Guidelines & Pedagogical Rules

> **Read this file to understand the core development principles.** This guide sets the standards for all code written in this multi-agent and RAG repository, tailored for students from both technical (4th-year CS) and non-technical (Management) backgrounds.

## Core Philosophical Principles

### 1. Build on the Shoulders of Giants (Package-First)
*   **The Rule**: **Never write custom logic if an established, production-grade package can do it.** 
*   **Why**: Writing low-level algorithms for chunking, vector searching, graph indexing, or evaluation is a waste of time in the modern AI ecosystem. It is prone to bugs and hides the real architectural patterns. 
*   **Action**: Use `LlamaIndex` for orchestration and data parsing, `ChromaDB` for vector storage, `Ragas` for evaluation, and `Guardrails AI` for filtering. Only write raw Python logic if no package exists for the task.

### 2. Hyper-Modularity (Strict Line Limits)
*   **The Rule**: **No Python file should exceed 50 lines of code.**
*   **Why**: Large files (code dumps) are overwhelming to read, difficult to trace, and hard to debug. Keeping files small forces students to think in single-responsibility units.
*   **Action**: Split code into distinct, atomic files (e.g., separating `classifier.py`, `parser.py`, `index.py`, and `query.py` instead of dumping them in a single `rag.py`).

### 3. Absolute Readability & Simplicity
*   **The Rule**: **Write the most straightforward, self-documenting code possible.**
*   **Why**: Students come from diverse backgrounds. Management students need to understand the structural logic, while CS students need to learn clean API design.
*   *   Avoid clever one-liners, complex list comprehensions, or dense functional code.
    *   Use highly descriptive variable names (e.g., `vector_retriever` instead of `vr`, `storage_context` instead of `sc`).
    *   Add clear, simple inline comments explaining *why* a configuration is chosen.

### 4. Zero-Friction Local Development
*   **The Rule**: **Always provide a local, zero-setup default fallback.**
*   **Why**: Students should be able to run the entire project out-of-the-box on low-spec laptops with 0 database administration.
*   **Action**: 
    *   Use embedded **ChromaDB** running locally in-memory or on local files.
    *   Default to LlamaIndex’s **SimpleGraphStore** (serializes to a local JSON file) so students don't need to host or configure a local Neo4j database instance.
    *   Provide a transparent upgrade path via `.env` keys (e.g., `NEO4J_URI`) to instantly hook into a free cloud instance (Neo4j Aura) when they are ready.

---

## Technical Skills Taught

| Technical Concept | Library Used | Pedagogical Value |
| :--- | :--- | :--- |
| **Document Classification** | `SimpleDirectoryReader` | Classifying content styles (YouTube scripts vs. clean paragraphs) |
| **Hierarchical Chunking** | `LlamaIndex NodeParsers` | Splitting documents semantically while maintaining parent-child relations |
| **Vector DB Management** | `ChromaDB` | Learning embedded, SQLite-style vector databases for production RAG |
| **Graph RAG & Triplet Extraction** | `LlamaIndex + Neo4j` | Extracting entity-relation triplets and querying structural graphs |
| **Advanced Query Expansion** | `HyDE & QueryTransform` | Rephrasing prompts and generating hypothetical documents for better matches |
| **Context Reranking** | `LLMRerank` | Fusing multiple retrieve sources (Vector + Graph) and pruning noisy nodes |
| **Automated Evaluation** | `Ragas` | Running automated "LLM-as-a-judge" scorecards (Faithfulness, Recall, Precision) |

