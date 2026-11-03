"""
Automated tests for the VoyagerAI agent.
Run with: pytest -v
"""

import json
import urllib.error
from types import SimpleNamespace
from unittest.mock import Mock, patch

from openai import OpenAIError

from src.tools import run_agent, _execute_tool_call, get_weather


# --------------------------------------------------
# Input validation tests
# --------------------------------------------------

def test_run_agent_rejects_empty_question():
    result = run_agent("")
    assert result == "Please provide a travel question or request."


def test_run_agent_rejects_whitespace_question():
    result = run_agent("   ")
    assert result == "Please provide a travel question or request."


# --------------------------------------------------
# Tool execution tests
# --------------------------------------------------

def test_execute_tool_call_rejects_invalid_json():
    result = _execute_tool_call("budget_breakdown", "{invalid json}")
    assert "malformed JSON" in result


def test_execute_tool_call_rejects_unknown_tool():
    result = _execute_tool_call("unknown_tool", "{}")
    assert result == "Unknown tool: unknown_tool"


def test_execute_tool_call_runs_budget_tool():
    result = _execute_tool_call(
        "budget_breakdown",
        '{"destination": "Tokyo", "days": 7, "budget_usd": 1400}'
    )

    assert "7-day Tokyo budget" in result
    assert "$200.00" in result


def test_execute_tool_call_rejects_non_object_arguments():
    result = _execute_tool_call("budget_breakdown", "[]")
    assert result == "Invalid tool arguments: expected a JSON object."


def test_execute_tool_call_rejects_missing_arguments():
    result = _execute_tool_call("budget_breakdown", "{}")
    assert "Invalid tool arguments" in result


def test_execute_tool_call_handles_unexpected_exception():
    with patch(
        "src.tools.budget_breakdown",
        side_effect=RuntimeError("Unexpected failure")
    ):
        result = _execute_tool_call(
            "budget_breakdown",
            '{"destination": "Tokyo", "days": 7, "budget_usd": 1400}'
        )

    assert result == "Tool execution failed unexpectedly. Please try again."


# --------------------------------------------------
# API configuration and response tests
# --------------------------------------------------

def test_run_agent_handles_missing_api_key():
    with patch(
        "src.tools.get_client",
        side_effect=RuntimeError("OPENROUTER_API_KEY is not configured.")
    ):
        result = run_agent("Plan a trip to Tokyo")

    assert result == "OPENROUTER_API_KEY is not configured."


def test_run_agent_returns_successful_ai_response():
    mock_client = Mock()

    mock_message = SimpleNamespace(
        content="Tokyo is a wonderful destination.",
        tool_calls=None,
    )

    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=mock_message)]
    )

    mock_client.chat.completions.create.return_value = mock_response

    with patch("src.tools.get_client", return_value=mock_client):
        result = run_agent("Tell me about Tokyo")

    assert result == "Tokyo is a wonderful destination."
    mock_client.chat.completions.create.assert_called_once()


def test_run_agent_handles_api_failure():
    mock_client = Mock()

    mock_client.chat.completions.create.side_effect = OpenAIError(
        "Service unavailable"
    )

    with patch("src.tools.get_client", return_value=mock_client):
        result = run_agent("Plan a trip to Tokyo")

    assert "AI service is currently unavailable" in result


def test_run_agent_handles_empty_api_response():
    mock_client = Mock()

    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[]
    )

    with patch("src.tools.get_client", return_value=mock_client):
        result = run_agent("Plan a trip to Tokyo")

    assert result == "The AI service returned an empty response."


# --------------------------------------------------
# Multi-tool orchestration tests
# --------------------------------------------------

def test_run_agent_executes_multiple_tool_calls():
    mock_client = Mock()

    budget_call = SimpleNamespace(
        id="call_budget",
        function=SimpleNamespace(
            name="budget_breakdown",
            arguments=json.dumps({
                "destination": "Tokyo",
                "days": 7,
                "budget_usd": 1400,
            }),
        ),
    )

    weather_call = SimpleNamespace(
        id="call_weather",
        function=SimpleNamespace(
            name="get_weather",
            arguments=json.dumps({"city": "Tokyo"}),
        ),
    )

    first_message = SimpleNamespace(
        content=None,
        tool_calls=[budget_call, weather_call],
    )

    first_response = SimpleNamespace(
        choices=[SimpleNamespace(message=first_message)]
    )

    final_message = SimpleNamespace(
        content="Here is your Tokyo travel plan.",
        tool_calls=None,
    )

    second_response = SimpleNamespace(
        choices=[SimpleNamespace(message=final_message)]
    )

    mock_client.chat.completions.create.side_effect = [
        first_response,
        second_response,
    ]

    with patch("src.tools.get_client", return_value=mock_client), \
         patch("src.tools.budget_breakdown", return_value="Budget result"), \
         patch("src.tools.get_weather", return_value="Weather result"):

        result = run_agent("Plan a trip to Tokyo with the weather and budget.")

    assert result == "Here is your Tokyo travel plan."
    assert mock_client.chat.completions.create.call_count == 2

    second_call_messages = (
        mock_client.chat.completions.create.call_args_list[1]
        .kwargs["messages"]
    )

    tool_messages = [
        message for message in second_call_messages
        if isinstance(message, dict) and message.get("role") == "tool"
    ]

    assert len(tool_messages) == 2
    assert {message["tool_call_id"] for message in tool_messages} == {
        "call_budget",
        "call_weather",
    }


# --------------------------------------------------
# Weather service tests
# --------------------------------------------------

def test_get_weather_rejects_empty_city():
    try:
        get_weather("")
        assert False, "Expected ValueError for empty city."
    except ValueError as error:
        assert str(error) == "City name cannot be empty."


def test_get_weather_handles_network_failure():
    with patch(
        "src.tools.urllib.request.urlopen",
        side_effect=urllib.error.URLError("Network unavailable")
    ):
        result = get_weather("Nairobi")

    assert result == "Unable to reach the weather service. Please try again later."


def test_get_weather_handles_unknown_city():
    mock_response = Mock()
    mock_response.read.return_value = b'{"results": null}'

    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_response)
    mock_context.__exit__ = Mock(return_value=False)

    with patch(
        "src.tools.urllib.request.urlopen",
        return_value=mock_context
    ):
        result = get_weather("UnknownPlace123")

    assert result == "Could not find location: UnknownPlace123"
