"""Research Agent Wrapper — simplified entry point for red-teaming and scripts.
"""

from backend.orchestrator import compile_graph, create_initial_state

def run_agent(question: str) -> str:
    """Invoke the full multi-agent research pipeline for a given question."""
    initial_state, team = create_initial_state(question, max_iterations=3)
    graph = compile_graph(team)
    
    final_state = graph.invoke(
        initial_state,
        config={"recursion_limit": 50}
    )
    
    return final_state.get("answer", "") or final_state.get("final_answer", "")
