"""ReAct agent for financial document QA using LangGraph."""

from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.core.config import settings
from src.tools import AGENT_TOOLS, clear_todos, get_todos, set_table_context


class AgentState(TypedDict):
    """State for the ReAct agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    final_answer: str
    iterations: int


SYSTEM_PROMPT = """You are a skilled financial document analyst. You answer questions about financial documents using tools.

## Available Tools
- write_todos(steps): Create a plan FIRST before doing anything else
- lookup_value(row, column): Get a specific value from the table
- calculate(expression): Perform arithmetic (use for ALL math)
- submit_answer(value, format): Submit your final answer (REQUIRED to complete)

## Rules
1. ALWAYS call write_todos FIRST to plan your approach
2. Use lookup_value to get exact values - don't guess from context
3. Use calculate for ANY arithmetic - no mental math
4. Format options: "number" (as-is), "percentage" (as decimal like 0.14), "money" (converts billion/million to raw number), "yes", "no"
5. You MUST call submit_answer to finish - this is the ONLY way to complete

## CRITICAL: Common Error Prevention

### Ratio Direction
When asked "how much does A represent IN RELATION TO B" or "A as a proportion of B":
- Calculate A / B (B is the denominator)
- Example: "2018 in relation to 2017" = 2018_value / 2017_value
- If result is 0.25 but seems too small, CHECK if you should flip it (maybe 4.0 is expected)

### Unit Normalization
Always submit raw numbers, NOT text units:
- "2.2 billion" → submit 2200 (if context is millions) or 2200000000
- "$ 3.5 million" → submit 3.5 or 3500000 depending on context
- Look at other values in the table to determine the unit scale

### Sign Handling for Losses
When the question asks about "losses" or "decline":
- If the table shows -9402, but question asks "what were the losses", answer 9402 (positive)
- "Losses" implies absolute value; negative sign is already semantic in the word "loss"
- Only keep negative if question asks for "change" or "difference"

## Workflow
1. Call write_todos with your plan
2. Call lookup_value for each value you need
3. Call calculate for any arithmetic
4. Call submit_answer with your final answer

Remember: For percentage calculations, the result should be a decimal (0.14 means 14%)."""


def create_react_agent():
    """Create a ReAct agent with tool calling."""

    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model=settings.model_name,
        temperature=0,
        google_api_key=settings.google_api_key,
    )

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    # Tool execution node
    tool_node = ToolNode(AGENT_TOOLS)

    # Maximum iterations before giving up
    max_iterations = 10

    def should_continue(state: AgentState) -> str:
        """Determine if agent should continue or stop."""
        messages = state["messages"]
        last_message = messages[-1]

        # Check iteration limit (fail gracefully)
        if state.get("iterations", 0) >= max_iterations:
            return "limit_reached"

        # Check if we have a final answer
        if state.get("final_answer"):
            return "end"

        # Check if last message has tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return "end"

    def handle_limit_reached(state: AgentState) -> dict:
        """Handle iteration limit with graceful fallback."""
        return {"final_answer": "[LIMIT] Could not find answer within iteration limit"}

    def agent_node(state: AgentState) -> dict:
        """Call the LLM to decide next action."""
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)

        iterations = state.get("iterations", 0) + 1

        return {"messages": [response], "iterations": iterations}

    def process_tool_results(state: AgentState) -> dict:
        """Process tool results and check for final answer."""
        messages = state["messages"]

        # Look for FINAL_ANSWER in recent tool results
        for msg in reversed(messages[-5:]):
            if hasattr(msg, "content") and "FINAL_ANSWER:" in str(msg.content):
                answer = str(msg.content).split("FINAL_ANSWER:")[1].strip()
                return {"final_answer": answer}

        return {}

    # Build graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("process", process_tool_results)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add fallback node
    workflow.add_node("limit_reached", handle_limit_reached)

    # Add edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
            "limit_reached": "limit_reached",
        }
    )
    workflow.add_edge("tools", "process")
    workflow.add_edge("process", "agent")
    workflow.add_edge("limit_reached", END)

    return workflow.compile()


# Global compiled agent
_react_agent = None


def get_react_agent():
    """Get or create the ReAct agent singleton."""
    global _react_agent
    if _react_agent is None:
        _react_agent = create_react_agent()
    return _react_agent


def format_table_for_prompt(table: dict) -> str:
    """Format table for the agent prompt."""
    if not table:
        return "(No table)"

    first_row = next(iter(table.values()), {})
    if isinstance(first_row, dict):
        columns = list(first_row.keys())
        header = "| Row | " + " | ".join(columns) + " |"
        separator = "|---" + "|---" * len(columns) + "|"
        rows = [header, separator]
        for row_key, row_data in table.items():
            if isinstance(row_data, dict):
                values = [str(row_data.get(col, "")) for col in columns]
                rows.append(f"| {row_key} | " + " | ".join(values) + " |")
        return "\n".join(rows)
    else:
        return "\n".join(f"| {k} | {v} |" for k, v in table.items())


def format_history_for_prompt(history: list[tuple[str, str]]) -> str:
    """Format Q&A history for prompt."""
    if not history:
        return "(First question)"

    lines = []
    for i, (q, a) in enumerate(history, 1):
        lines.append(f"Q{i}: {q}")
        lines.append(f"A{i}: {a}")
    return "\n".join(lines)


def run_react_agent(
    pre_text: str,
    table: dict,
    post_text: str,
    question: str,
    history: list[tuple[str, str]] = None,
) -> tuple[str, list[str]]:
    """
    Run the ReAct agent on a question.

    Returns:
        Tuple of (final_answer, tool_calls_log)
    """
    agent = get_react_agent()

    # Set table context for tools
    set_table_context(table)
    clear_todos()

    # Build user message
    table_str = format_table_for_prompt(table)
    history_str = format_history_for_prompt(history or [])

    user_message = f"""## Financial Document

### Text Before Table
{pre_text}

### Financial Data Table
{table_str}

### Text After Table
{post_text}

### Conversation History
{history_str}

### Current Question
{question}

Begin by calling write_todos to plan your approach, then use tools to find the answer."""

    # Create initial messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    # Run agent
    initial_state: AgentState = {
        "messages": messages,
        "final_answer": "",
        "iterations": 0,
    }

    try:
        result = agent.invoke(initial_state)

        # Extract final answer
        final_answer = result.get("final_answer", "")

        # If no answer found via submit_answer, try to extract from last AI message
        if not final_answer:
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    final_answer = str(msg.content)[:100]
                    break

        # Log tool calls
        tool_calls = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append(f"{tc['name']}({tc['args']})")

        return final_answer, tool_calls, get_todos()

    except Exception as e:
        return f"Error: {e}", [], []


async def run_react_agent_async(
    pre_text: str,
    table: dict,
    post_text: str,
    question: str,
    history: list[tuple[str, str]] = None,
) -> tuple[str, list[str]]:
    """Async version of run_react_agent."""
    agent = get_react_agent()

    # Set table context for tools
    set_table_context(table)
    clear_todos()

    # Build user message
    table_str = format_table_for_prompt(table)
    history_str = format_history_for_prompt(history or [])

    user_message = f"""## Financial Document

### Text Before Table
{pre_text}

### Financial Data Table
{table_str}

### Text After Table
{post_text}

### Conversation History
{history_str}

### Current Question
{question}

Begin by calling write_todos to plan your approach, then use tools to find the answer."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    initial_state: AgentState = {
        "messages": messages,
        "final_answer": "",
        "iterations": 0,
    }

    try:
        result = await agent.ainvoke(initial_state)

        final_answer = result.get("final_answer", "")
        if not final_answer:
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage) and msg.content:
                    final_answer = str(msg.content)[:100]
                    break

        tool_calls = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls.append(f"{tc['name']}({tc['args']})")

        return final_answer, tool_calls, get_todos()

    except Exception as e:
        return f"Error: {e}", [], []
