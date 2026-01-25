from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from src.agents.react_agent import run_react_agent


@pytest.fixture
def mock_llm_response():
    """Mock LLM response sequence."""
    # 1. Thought: Need to lookup value
    msg1 = AIMessage(content="", tool_calls=[
        {"name": "write_todos", "args": {"steps": ["find revenue"]}, "id": "call_1"}
    ])
    # 2. Thought: Lookup
    msg2 = AIMessage(content="", tool_calls=[
        {"name": "lookup_value", "args": {"row": "Revenue", "column": "2018"}, "id": "call_2"}
    ])
    # 3. Thought: Submit
    msg3 = AIMessage(content="", tool_calls=[
        {"name": "submit_answer", "args": {"value": "100", "format": "number"}, "id": "call_3"}
    ])
    return [msg1, msg2, msg3]

@patch("src.agents.react_agent.ChatGoogleGenerativeAI")
def test_run_react_agent_success(mock_llm_class, mock_llm_response):
    # Setup mock LLM
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    # Mock the invoke method to return messages in sequence
    # Note: StateGraph loop calls invoke multiple times.
    # We need to simulate the agent returning different messages based on state.
    # Ideally we mock the 'invoke' of the compiled graph or the LLM.
    # Mocking the compiled graph (agent) is easier for unit testing valid logic flow.

    # But wait, run_react_agent calls get_react_agent which calls create_react_agent
    # which instantiates ChatGoogleGenerativeAI.

    # Let's mock the 'agent.invoke' directly to avoiding dealing with LangGraph internals in a unit test.
    # True integration test would run LangGraph but mock the LLM calls.

    mock_compiled_agent = MagicMock()

    # Simulate a successful run
    # The agent returns a state dict
    mock_compiled_agent.invoke.return_value = {
        "messages": [
            AIMessage(content="FINAL_ANSWER: 100")
        ],
        "final_answer": "100"
    }

    with patch("src.agents.react_agent.get_react_agent", return_value=mock_compiled_agent):
        answer, tools, todos = run_react_agent(
            pre_text="PRE",
            table={"Revenue": {"2018": "100"}},
            post_text="POST",
            question="What is revenue?",
        )

        assert answer == "100"
        # Since we mocked the agent result directly, tool logs might be empty unless we populate messages
        # checking basic success flow here.

@patch("src.agents.react_agent.ChatGoogleGenerativeAI")
def test_run_react_agent_error(mock_llm_class):
    # Test error handling when agent raises exception
    mock_compiled_agent = MagicMock()
    mock_compiled_agent.invoke.side_effect = Exception("API Error")

    with patch("src.agents.react_agent.get_react_agent", return_value=mock_compiled_agent):
        answer, tools, todos = run_react_agent("P", {}, "P", "Q")
        assert "Error: API Error" in answer
