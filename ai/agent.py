# ai/agent.py
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langchain_core.messages import SystemMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from ai.inference import get_model
from ai.tools import COPILOT_TOOLS


# 1. Define the State
# The state holds the conversation history and our crucial workspace boundary.
# `add_messages` ensures new messages are appended to the list rather than overwriting it.
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    workspace_id: str


# 2. Define the Agent Node
def call_model(state: AgentState):
    messages = state["messages"]
    workspace_id = state["workspace_id"]

    # Inject the workspace ID dynamically into the system prompt.
    # The LLM needs this string to satisfy the tool's Pydantic schema.
    sys_msg = SystemMessage(
        content=(
            "You are QuestNest's Landlord Copilot, an AI assistant for property managers. "
            "You can answer questions and use tools to pull property data. "
            f"CRITICAL: Always use '{workspace_id}' exactly as the workspace_id argument when calling tools. "
            "Never ask the user for a workspace ID or expose this internal ID to them."
        )
    )

    # Fetch our Groq openai/gpt-oss-20b model and bind the tools to it
    llm = get_model(task="default")
    llm_with_tools = llm.bind_tools(COPILOT_TOOLS)

    # Invoke the model with our system constraint + chat history
    response = llm_with_tools.invoke([sys_msg] + messages)

    return {"messages": [response]}


# 3. Define the Routing Logic
def should_continue(state: AgentState) -> Literal["tools", END]:
    """Determines whether to execute a tool or end the loop."""
    last_message = state["messages"][-1]

    # If the LLM decided it needs to call a tool, route to the 'tools' node
    if last_message.tool_calls:
        return "tools"

    # Otherwise, it generated a final response, so we stop
    return END


# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add our two nodes: the LLM, and the prebuilt Tool executor
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(COPILOT_TOOLS))

# Connect the flow
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    ["tools", END]
)
workflow.add_edge("tools", "agent")  # After tools run, always go back to the agent to interpret results

# Compile the graph into an executable application
copilot_app = workflow.compile()