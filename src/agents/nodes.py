"""LangGraph node implementations for conversational QA."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agents.state import ConversationState
from src.core.config import settings


def get_llm() -> ChatGoogleGenerativeAI:
    """Get configured Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=settings.model_name,
        temperature=settings.temperature,
        google_api_key=settings.google_api_key,
    )


def format_document_context(state: ConversationState) -> str:
    """Format document for LLM context."""
    table_str = ""
    if state.table:
        # Format table as markdown
        rows = []
        for row_key, row_data in state.table.items():
            if isinstance(row_data, dict):
                row_values = " | ".join(str(v) for v in row_data.values())
                rows.append(f"| {row_key} | {row_values} |")
        table_str = "\n".join(rows)

    return f"""## Document Context

### Text Before Table
{state.pre_text}

### Table
{table_str}

### Text After Table
{state.post_text}
"""


def format_conversation_history(state: ConversationState) -> str:
    """Format previous Q&A turns for context."""
    if not state.answers_history:
        return ""

    history = []
    for i, answer in enumerate(state.answers_history):
        history.append(f"Turn {i + 1} Answer: {answer}")

    return "### Previous Answers in This Conversation\n" + "\n".join(history)


REASONING_PROMPT = """You are a financial document analyst. Answer questions about the provided financial document.

{document_context}

{conversation_history}

## Current Question
{question}

## Instructions
1. First, identify what information you need from the document
2. Extract relevant numbers or facts from the text and table
3. If calculation is needed, show your step-by-step work
4. If the answer is numeric, for example a percentage, money, or a number, provide the value only. Percentages should be provided as decimals. Do not include any additional text.
5. If the answer is yes/no, provide the value only. Do not include any additional text.

## Response Format
REASONING:
[Your step-by-step analysis]

ANSWER:
[Your final answer - just the value or brief response]
"""


def reasoning_node(state: ConversationState) -> dict:
    """Main reasoning node - analyzes document and answers question."""
    llm = get_llm()

    document_context = format_document_context(state)
    conversation_history = format_conversation_history(state)

    prompt = REASONING_PROMPT.format(
        document_context=document_context,
        conversation_history=conversation_history,
        question=state.current_question,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    response_text = response.content

    # Parse response into reasoning and answer
    reasoning = ""
    answer = response_text

    if "REASONING:" in response_text and "ANSWER:" in response_text:
        parts = response_text.split("ANSWER:")
        reasoning = parts[0].replace("REASONING:", "").strip()
        answer = parts[1].strip()

    return {
        "reasoning_trace": reasoning,
        "current_answer": answer,
        "messages": [
            HumanMessage(content=state.current_question),
            AIMessage(content=answer),
        ],
    }


def update_history_node(state: ConversationState) -> dict:
    """Update conversation history after answering."""
    new_history = state.answers_history + [state.current_answer]
    return {
        "answers_history": new_history,
        "turn_index": state.turn_index + 1,
    }
