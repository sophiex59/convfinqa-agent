"""LangGraph agent state definitions."""

from typing import Annotated
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages


class ConversationState(BaseModel):
    """State maintained across conversation turns."""

    # Document context
    record_id: str = Field(default="", description="Current record ID")
    pre_text: str = Field(default="", description="Text before table")
    post_text: str = Field(default="", description="Text after table")
    table: dict = Field(default_factory=dict, description="Table data")

    # Conversation history
    messages: Annotated[list, add_messages] = Field(
        default_factory=list,
        description="Conversation messages"
    )

    # Current turn
    current_question: str = Field(default="", description="Current user question")
    current_answer: str = Field(default="", description="Agent's answer")
    reasoning_trace: str = Field(default="", description="Step-by-step reasoning")

    # Evaluation tracking
    turn_index: int = Field(default=0, description="Current turn in dialogue")
    answers_history: list[str] = Field(
        default_factory=list,
        description="Previous answers in this conversation"
    )
