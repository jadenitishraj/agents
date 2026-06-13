"""Team selector — decides which roles from the taxonomy are needed for a question.

Taxonomy = the full catalog.  Team selection = the active subset for one run.
"""

from __future__ import annotations

from backend.config.taxonomy import TAXONOMY, DEEP_KEYWORDS, SENSITIVE_KEYWORDS


def needs_deep_reading(question: str) -> bool:
    """Return True if the question looks deep or comparative."""
    lowered = question.lower()
    if len(question.split()) > 15:
        return True
    return any(kw in lowered for kw in DEEP_KEYWORDS)


def is_sensitive(question: str) -> bool:
    """Return True if the question touches a sensitive domain."""
    lowered = question.lower()
    return any(kw in lowered for kw in SENSITIVE_KEYWORDS)


def is_arithmetic(question: str) -> bool:
    """Return True if the question involves arithmetic computation."""
    import re
    lowered = question.strip().lower()
    # Pure math expression: "1+1", "2 * 3", "10 / 5"
    if re.search(r'\d+\s*[+\-*/]\s*\d+', lowered):
        return True
    # Math keywords with numbers: "add 2 and 3", "sum of 5 and 10"
    math_kw = ["calculate", "compute", "sum of", "product of", "divide", "multiply", "add", "subtract"]
    if any(kw in lowered for kw in math_kw) and re.search(r'\d', lowered):
        return True
    return False


def is_simple_question(question: str) -> bool:
    """Return True if the question is a simple greeting or general conversational query."""
    lowered = question.strip().lower()

    # Greetings / trivial phrases
    simple_phrases = {
        "hi", "hello", "hey", "how are you", "how are you?", "what's up?", "whats up?",
        "hi there", "good morning", "good afternoon", "good evening", "how's it going",
        "how's it going?"
    }
    if lowered in simple_phrases:
        return True

    # Fallback to a lightweight LLM call to classify
    try:
        from backend.llm import call_llm
        prompt = f"""Classify if the following question/statement is extremely simple and does NOT need any external web search or internal database lookup (e.g. greetings, basic arithmetic, simple conversational query, etc.).
Reply with exactly one word: 'YES' if it is simple/conversational, or 'NO' if it requires research, fact-retrieval, or external lookup.

Question: {question}
Answer:"""
        res = call_llm(prompt, max_tokens=5, agent_name="Classifier").strip().upper()
        return "YES" in res
    except Exception:
        return False


def select_team(question: str) -> list[str]:
    """Select the active team of agents for this question.

    Priority: arithmetic → simple/greeting → full research team.
    """
    if is_arithmetic(question):
        # Arithmetic goes directly to Writer (with MCP tools) → Critic.
        return ["Writer", "Critic"]

    if is_simple_question(question):
        # Simple/conversational questions go directly to Writer and Critic.
        return ["Writer", "Critic"]

    team = [role for role, info in TAXONOMY.items() if info["always"]]

    if needs_deep_reading(question):
        team.append("Reader")

    if is_sensitive(question):
        team.append("Compliance")

    return team

