"""Writer agent — synthesizes findings into a clear answer.

Accepts optional critic feedback (or Reflexion lessons) to improve rewrites.
"""

from __future__ import annotations

from langsmith import traceable

from backend.llm import call_llm
from backend.content_policy.policy_loader import load_policy, wrap_user_input

Source = dict[str, str]

from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from backend.llm import get_llm

@traceable(name="writer_agent", run_type="chain")
def writer_agent(
    question: str,
    sources: list[Source],
    facts: list[str],
    internal_facts: list[str] = None,
    internal_contexts: list[str] = None,
    disclaimer: str = "",
    critic_feedback: str = "",
    tools: list[BaseTool] = None,
) -> str:
    """Write a clear, well-structured answer (150-300 words) to the question."""
    policy = load_policy()
    sources_text = "\n".join(
        f"- {s['title']} ({s['url']})" for s in sources[:8]
    )
    all_facts = list(facts)
    if internal_facts:
        all_facts.extend([f"[Internal DB] {f}" for f in internal_facts])
    facts_text = "\n".join(f"- {f}" for f in all_facts) if all_facts else "(none)"
    feedback_text = ""
    if critic_feedback:
        feedback_text = (
            "\n\nPREVIOUS CRITIC FEEDBACK TO ADDRESS:\n"
            f"{critic_feedback}"
        )

    disclaimer_line = (
        f"Include this disclaimer at the end: {disclaimer}" if disclaimer else ""
    )

    chunks_text = ""
    if internal_contexts and len(internal_contexts) > 0:
        chunks_text = "\n\nRAG Contexts:\n" + "\n\n".join(f"[Chunk {i+1}] {c}" for i, c in enumerate(internal_contexts))
        
    tool_instructions = ""
    if tools:
        tool_names = [t.name for t in tools]
        tool_instructions = f"\n\nYou have access to the following tools: {', '.join(tool_names)}.\nYou MUST dynamically select and use these tools to fulfill the user's request.\nFor mathematical computations, use the math tools.\nIf the user asks about Notion, quotes, or their personal workspace (including questions like 'what can you see', 'what pages do I have', or 'do you have access'), you MUST call the 'search_notion' tool first. Do NOT state that you cannot access Notion or refuse the request without first executing the 'search_notion' tool."

    prompt = f"""{policy}

Write a clear, well-structured answer (150-300 words) to the question.
Use the facts, contexts, and cite sources where appropriate.{tool_instructions}
{disclaimer_line}

Question: {wrap_user_input(question)}

Facts:
{facts_text}

Sources:
{wrap_user_input(sources_text)}{chunks_text}{feedback_text}"""
    
    if not tools:
        return call_llm(prompt, max_tokens=600, agent_name="Writer")
        
    llm = get_llm(agent_name="Writer")
    llm_with_tools = llm.bind_tools(tools)
    
    messages = [HumanMessage(content=prompt)]
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    if response.tool_calls:
        from langchain_core.messages import ToolMessage
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            # Find the matching tool object
            tool_obj = next((t for t in tools if t.name == tool_name), None)
            if tool_obj:
                print(f"  [WRITER] Manually invoking tool {tool_name} with args {tool_args}...")
                try:
                    tool_output = tool_obj.invoke(tool_args)
                except Exception as e:
                    tool_output = f"Error executing tool: {str(e)}"
                
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_id, name=tool_name))
            else:
                messages.append(ToolMessage(content=f"Error: Tool '{tool_name}' not found in registry.", tool_call_id=tool_id, name=tool_name))
        
        # Ask for final answer after tools
        messages.append(HumanMessage(content="State the final answer in a clear sentence."))
        final_response = llm.invoke(messages)
        return final_response.content
        
    return response.content or ""
    # Teaching note:
    # This project builds the writer prompt as one explicit string so students can
    # see the full prompt contract in a single place. LangGraph does not require
    # any special prompt format here: each node is just Python code that receives
    # state, prepares context, calls the model, and returns an output. In this
    # node, the writer agent takes upstream state produced by other nodes
    # (question, facts, sources, disclaimer, critic feedback), combines it with a
    # reusable policy loaded from disk, and sends that final prompt to the LLM.
    #
    # The <user_input> wrapping is only a text delimiter. It is not a privileged
    # LangChain or model-level role. We use it here because it makes the prompt
    # easier to read in logs and easier for students to reason about: policy and
    # instructions live outside the tags, while user-provided content is wrapped
    # inside them.
    #
    # In industry, the more standard approach is usually:
    # 1. put policy / safety / style rules in a system message
    # 2. put the user question in a human message
    # 3. pass facts and sources as structured context in additional messages or
    #    template variables
    # 4. keep prompt assembly separate from model invocation with
    #    ChatPromptTemplate or equivalent abstractions
    #
    # That structured-message approach is generally more robust because it gives
    # clearer separation between instruction layers. This teaching project keeps
    # the prompt inline on purpose so students can inspect exactly what the node
    # sends to the model without first learning the full prompt-template stack.