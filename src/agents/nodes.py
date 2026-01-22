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
    """Format document for LLM context with proper table structure."""
    table_str = ""
    if state.table:
        # Get all column headers from the first row
        first_row = next(iter(state.table.values()), {})
        if isinstance(first_row, dict):
            columns = list(first_row.keys())
            
            # Build proper markdown table with headers
            header = "| Row | " + " | ".join(columns) + " |"
            separator = "|---" + "|---" * len(columns) + "|"
            
            rows = [header, separator]
            for row_key, row_data in state.table.items():
                if isinstance(row_data, dict):
                    values = [str(row_data.get(col, "")) for col in columns]
                    rows.append(f"| {row_key} | " + " | ".join(values) + " |")
            
            table_str = "\n".join(rows)
        else:
            # Fallback for non-dict row data
            table_str = "\n".join(f"| {k} | {v} |" for k, v in state.table.items())

    return f"""## Document Context

### Text Before Table
{state.pre_text}

### Financial Data Table
{table_str}

### Text After Table
{state.post_text}
"""


def format_conversation_history(state: ConversationState) -> str:
    """Format previous Q&A turns with full context for multi-hop reasoning."""
    if not state.messages:
        return ""

    history = []
    # Messages are pairs of HumanMessage (question) and AIMessage (answer)
    for i, msg in enumerate(state.messages):
        role = "Q" if hasattr(msg, 'type') and msg.type == "human" else "A"
        if not hasattr(msg, 'type'):
            # Fallback: alternate based on position
            role = "Q" if i % 2 == 0 else "A"
        turn_num = (i // 2) + 1
        history.append(f"{role}{turn_num}: {msg.content}")

    return "### Conversation History\n" + "\n".join(history)


REASONING_PROMPT = """You are a skilled financial document analyst. Answer questions about the provided financial document.

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
6. If you still do not know the answer, respond with "I don't know".

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


async def async_reasoning_node(state: ConversationState) -> dict:
    """Async version of reasoning node for parallel evaluation."""
    llm = get_llm()

    document_context = format_document_context(state)
    conversation_history = format_conversation_history(state)

    prompt = REASONING_PROMPT.format(
        document_context=document_context,
        conversation_history=conversation_history,
        question=state.current_question,
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])
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

