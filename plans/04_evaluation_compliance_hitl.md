# Feature: RAG Advanced Evaluation, Regulatory Compliance Scanners, and HITL Pipeline

**Date:** 2026-05-26
**Status:** 🔲 Planned

## Description

To prepare the multi-agent research backend for enterprise deployment and strict compliance environments, we will implement a multi-layered verification system. This feature introduces advanced lexical/functional correctness evaluators (BLEU/ROUGE and a Pass@k code execution checker), advanced hallucination scanners (sentence-level entailment and self-contradiction checkers), regulatory compliance scanners (EU AI Act risk grading and Indian DPDP PII sanitization), and a concrete Human-in-the-Loop (HITL) approval dashboard in both the FastAPI backend (using LangGraph persistent state checking) and the vanilla JS frontend.

---

## Checklist

### 1. Lexical & Code Quality Metrics (`BLEU/ROUGE & Pass@k`)
- [ ] **Step 1.1: Lexical Accuracy Evaluation**
  - Integrate `nltk` and `rouge-score` in `backend/evaluation/rag_eval.py` to calculate exact lexical overlap metrics (BLEU, ROUGE-1, ROUGE-2, ROUGE-L) comparing synthesized answers against high-quality reference/ground-truth summaries.
- [ ] **Step 1.2: Pass@k Code Correctness Simulator**
  - Create a secure sandbox execution utility (`backend/evaluation/pass_k.py`) that extracts generated Python code blocks from answers.
  - Execute code blocks against pre-configured unit test assertions across `k` sample generations to calculate empirical `Pass@k` functional correctness metrics (e.g., `Pass@1`, `Pass@5`).

### 2. Advanced Hallucination Scanners
- [ ] **Step 2.1: Sentence-level Context Entailment Check**
  - Build a claim-extraction model inside `backend/evaluation/hallucination.py` that breaks down synthesized answers into individual atomic sentences/claims.
  - Implement an NLI (Natural Language Inference) check using LLM-as-a-judge to grade each claim's relation to retrieved contexts: `Entailed`, `Neutral`, or `Contradictory`.
- [ ] **Step 2.2: Self-Contradiction Checker**
  - Design a cross-sentence contradiction detector that maps all claims against each other using embedding cosine similarity and LLM logic to identify logical conflicts or contradictory statements inside the generated answer itself.

### 3. Regulatory Compliance Scanners (EU AI Act & Indian DPDP)
- [ ] **Step 3.1: EU AI Act Risk Grader**
  - Create `backend/evaluation/compliance_eu.py` to scan user questions and generated answers.
  - Flag prohibited AI applications under the **EU AI Act** (e.g., subliminal manipulation, social scoring, biometric classification, emotion recognition in workplaces).
  - Assign risk tiers (`Prohibited`, `High-Risk`, `Limited-Risk`, `Minimal-Risk`) with structured reasons.
- [ ] **Step 3.2: Indian DPDP (Digital Personal Data Protection) Sanitizer**
  - Implement an Indian personal data scanner in `backend/evaluation/compliance_dpdp.py`.
  - Use regex and named entity recognition to detect Indian PII: Aadhaar Card (12-digit format), PAN Card, Indian Mobile Numbers (+91), Voter ID, and passport numbers.
  - Automatically mask/redact detected PII and flag whether explicit user consent metadata exists before pipeline ingestion.

### 4. Production-Grade HITL Approval Pipeline
- [ ] **Step 4.1: LangGraph Checkpointed HITL Node**
  - Refactor `backend/orchestrator.py` to use a persistent checkpoint memory saver (e.g., `MemorySaver`).
  - Configure the `human_review_node` as a true interruption gate (using `interrupt_before=["human_review"]`), forcing the graph to pause execution indefinitely instead of auto-approving after 3 seconds.
- [ ] **Step 4.2: FastAPI Interaction Endpoints**
  - Create `/research/pending` in `backend/api.py` to list all graph instances paused at the human review checkpoint.
  - Create `/research/approve` to let a human expert submit an edited draft answer, approve/override compliance flags, and resume graph execution using the state checkpoint ID.
- [ ] **Step 4.3: Vanilla JS Interactive Review Dashboard**
  - Create a new "Human Expert Console" tab in `frontend/index.html` and `index.js`.
  - Render pending graph reviews with side-by-side RAG source references.
  - Embed an interactive Markdown text-editor allowing reviews to live-edit synthesized answers.
  - Render an interactive **Compliance Badge Panel** showing real-time metrics: Ragas scores, BLEU/ROUGE overlap, EU AI Act risk levels, and DPDP sanitization alerts.

---

## Files Touched

| File | Action | Description |
|------|--------|-------------|
| `backend/evaluation/rag_eval.py` | Modified | Integrate BLEU and ROUGE scoring alongside Ragas |
| `backend/evaluation/pass_k.py` | Created | Functional Python sandbox simulator calculating Pass@k metrics |
| `backend/evaluation/hallucination.py` | Created | sentence claim extraction, context entailment, and self-contradiction checkers |
| `backend/evaluation/compliance_eu.py` | Created | Prohibited use-case classification and risk tiering under the EU AI Act |
| `backend/evaluation/compliance_dpdp.py` | Created | Indian PII (Aadhaar, PAN, Voter ID) regex scrubbing and redaction |
| `backend/orchestrator.py` | Modified | Add LangGraph MemorySaver, true HITL interrupt logic |
| `backend/api.py` | Modified | Add `/research/pending` and `/research/approve` FastAPI endpoints |
| `frontend/index.html` | Modified | Design human review panel layout and markdown editor |
| `frontend/index.css` | Modified | Add dashboard cards, compliance badges, and reviewer styles |
| `frontend/index.js` | Modified | Implement pending fetch, approve/edit post requests, and state visualizers |
| `plans/04_evaluation_compliance_hitl.md` | Created | THIS FILE — Complete features checklist and plan |

---

## Notes

- **pedagogical Value**: This feature highlights the real-world operational challenges of deploying RAG: legal liability (EU AI Act/DPDP), logical hallucinations, and why true human oversight (HITL) is mandatory in regulated markets.
- **Local Sandbox Execution**: The Python code executor must be protected against malicious commands (e.g., using safe standard imports and catching/isolating system exit calls).
- **Graceful UI Transition**: The review tab will load asynchronously and present a beautifully styled panel with vibrant indicators (Red for DPDP/Prohibited AI Act, Green for Compliant).
