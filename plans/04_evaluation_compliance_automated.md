# Feature: Automated DeepEval Verification for LangGraph Agents

**Date:** 2026-05-26
**Status:** 🔲 Planned

## Description

To build a robust automated testing and verification framework for our LangGraph agent team, we will integrate **DeepEval**. All evaluation logic will be stored inside the `backend/agent_evaluation/` directory. Each validation layer is separated into its own clean file to preserve modularity.

In strict adherence to project guidelines:

1. **DeepEval-Only Engine**: No custom raw evaluation scripts or custom metric code will be written. All tests must leverage DeepEval's native metrics (`BleuMetric`, `RougeMetric`, `HallucinationMetric`, `FaithfulnessMetric`, and `GEval`).
2. **Pedagogical Extensibility**: Each file will include a detailed `TODO` comment listing additional agentic metrics (like `ToolCorrectnessMetric`, `StepEfficiencyMetric`, and `TaskCompletionMetric`) that students can implement to evaluate LangGraph-specific tracing.

---

## Directory Structure

All files will reside inside the new evaluation folder:

```
backend/
└── agent_evaluation/
    ├── __init__.py
    ├── lexical_code.py     # BLEU, ROUGE, and Code Correctness (G-Eval)
    ├── hallucination.py    # Hallucination and Faithfulness Metrics
    └── compliance.py       # EU AI Act and Indian DPDP compliance (G-Eval)
```

---

## Detailed Plan Checklist

### 1. Inception & Workspace Setup

- [ ] **Step 1.1: Environment Alignment**
  - Add `deepeval` to `backend/requirements.txt` if not already present.
  - Create the `backend/agent_evaluation/` directory and include a blank `__init__.py`.

### 2. Lexical & Functional Correctness (`lexical_code.py`)

- [ ] **Step 2.1: Native Lexical Metrics**
  - Implement a verification module using DeepEval's native `BleuMetric` and `RougeMetric` to assert lexical alignment with expected outputs.
- [ ] **Step 2.2: Functional Code Correctness via G-Eval**
  - Instead of writing custom Python execution sandboxes, define a `GEval` metric designed to audit code block outputs:
    - **Criteria**: Checks generated Python code snippets inside the output for syntactical correctness, absence of runtime bugs, and coverage of specified functional parameters.
- [ ] **Step 2.3: Student Extensibility TODO**
  - Add a comprehensive `TODO` code block comment explaining how to configure DeepEval tracing to monitor LangGraph agent intermediate states and collect system logs.

### 3. Factual Alignment & Hallucination Gates (`hallucination.py`)

- [ ] **Step 3.1: Hallucination & Faithfulness Verification**
  - Implement DeepEval's native `HallucinationMetric` and `FaithfulnessMetric`.
  - Pass the **Searcher Agent's web sources** and **Reader Agent's parsed facts** as `retrieved_contexts`.
  - Pass the **Writer Agent's final answer** as the `actual_output`.
  - Configure thresholds strictly to fail any agent outputs with factual errors or claims not present in the sources.
- [ ] **Step 3.2: Student Extensibility TODO**
  - Add a detailed comment listing additional agent evaluation metrics like **`TaskCompletionMetric`** (to evaluate whether the agent completed the original task description) and **`StepEfficiencyMetric`** (to penalize agents that run into circular reasoning loops).

### 4. Regulatory Safety Scanners (`compliance.py`)

- [ ] **Step 4.1: EU AI Act Risk Grader**
  - Implement a `GEval` metric with criteria checking for prohibited use-cases (e.g. social scoring, subliminal techniques, workplace emotion tracking) and high-risk categorizations under the EU AI Act.
- [ ] **Step 4.2: Indian DPDP Sanitization Scanner**
  - Implement a `GEval` metric with criteria ensuring that personal identifiers (such as Aadhaar, PAN, voter cards, passport numbers, and plain +91 mobile numbers) are masked/redacted in the agent's output.
- [ ] **Step 4.3: Student Extensibility TODO**
  - Add a `TODO` comment detailing how to expand compliance auditing using DeepEval's native **`BiasMetric`** and **`ToxicityMetric`** to ensure agents remain safe, neutral, and respectful during collaboration.

---

## Future Extensibility: LangGraph Agentic Metrics TODO List

_To be embedded in each file as standard guidelines for students:_

- **`ToolCorrectnessMetric`**: Assesses whether the Searcher agent successfully called `search_web()` with properly formatted parameters.
- **`StepEfficiencyMetric`**: Grades whether the graph completed the Writer-Critic loop efficiently or went through redundant iterations.
- **`TaskCompletionMetric`**: Measures whether the final response meets the complete intent of the initial prompt.
- **`BiasMetric` & `ToxicityMetric`**: Automated safety gates to ensure generated agent reasoning is unbiased, ethical, and safe.
