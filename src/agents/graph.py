"""LangGraph conversation graph for ConvFinQA."""

from langgraph.graph import StateGraph, END

from src.agents.state import ConversationState
from src.agents.nodes import reasoning_node, update_history_node


def create_conversation_graph() -> StateGraph:
    """Create the conversation graph for financial QA."""
    # Initialize graph with state schema
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("reasoning", reasoning_node)
    graph.add_node("update_history", update_history_node)

    # Define edges
    graph.set_entry_point("reasoning")
    graph.add_edge("reasoning", "update_history")
    graph.add_edge("update_history", END)

    return graph.compile()


# Singleton compiled graph
conversation_agent = create_conversation_graph()
