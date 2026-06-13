"""Internal Search Agent — uses the global RAG v2 database."""

from __future__ import annotations

import json
from langsmith import traceable
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode

from backend.llm import get_llm

@traceable(name="internal_search_agent", run_type="chain")
def internal_search_agent(question: str, tools: list[BaseTool]) -> dict:
    """Agent that chooses tools, executes them via LangGraph ToolNode, and extracts facts."""
    print("    Internal Search -> Deciding which tool to use via LLM...")
    
    llm = get_llm(agent_name="InternalSearcher")
    llm_with_tools = llm.bind_tools(tools)
    
    prompt = f"""You are an intelligent research assistant.
You must answer the user's question using the provided tools.
If the question is about internal company documents, architecture, or proprietary knowledge, call the global_db_search tool.
If the question requires general external knowledge or real-time web results, call the web_search tool.

Question: {question}"""
    
    messages = [HumanMessage(content=prompt)]
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    contexts = []
    
    if response.tool_calls:  #its not empty, its not null,   
        print(f"    Internal Search -> LLM chose tools. Executing via ToolNode...")
        
        # 1. Use LangGraph's prebuilt ToolNode to automatically execute all tool calls
        tool_node = ToolNode(tools)
        tool_node_result = tool_node.invoke({"messages": messages})
        
        tool_messages = tool_node_result["messages"]
        messages.extend(tool_messages)
        
        # Save the raw stringified context for the writer agent
        contexts = [msg.content for msg in tool_messages]
        
        # 2. Ask the LLM to read the ToolNode's output and extract the final facts
        fact_prompt = """Based on the tool results above, extract 3 to 5 concise facts that answer the original question.
Return one fact per line with no numbering."""
        messages.append(HumanMessage(content=fact_prompt))
        
        print("    Internal Search -> Extracting facts from tool results...")
        final_response = llm.invoke(messages)
        text = final_response.content
    else:
        print("    Internal Search -> LLM did not choose any tool.")
        text = response.content
    
    facts = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    
    return {
        "facts": facts,
        "contexts": contexts,
    }
