import json
import urllib.request
import urllib.parse

from openai import OpenAIError

from src.rag import search_guides, ensure_index
from src.ai_assistant import get_client, MODEL


def budget_breakdown(destination: str, days: int, budget_usd: float) -> str:
    """Calculate a daily travel budget breakdown."""
    destination = destination.strip()
    if not destination:
        raise ValueError("Destination cannot be empty.")

    if isinstance(days, bool) or not isinstance(days, int) or days <= 0:
        raise ValueError("Number of days must be a positive integer.")

    if isinstance(budget_usd, bool) or not isinstance(budget_usd, (int, float)):
        raise ValueError("Budget must be a valid number.")

    if budget_usd <= 0:
        raise ValueError("Budget must be greater than zero.")

    daily = budget_usd / days

    accommodation = daily * 0.40
    food = daily * 0.30
    transport = daily * 0.15
    activities = daily * 0.15

    return f"""\
{days}-day {destination} budget (${budget_usd:.2f} total)
Daily: ${daily:.2f}
  Accommodation : ${accommodation:.2f}
  Food          : ${food:.2f}
  Transport     : ${transport:.2f}
  Activities    : ${activities:.2f}
"""


def get_weather(city: str) -> str:
    """Retrieve current weather conditions for a city using Open-Meteo."""

    city = city.strip() if isinstance(city, str) else ""

    if not city:
        raise ValueError("City name cannot be empty.")

    try:
        # Step 1: Geocode the city.
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode(
                {
                    "name": city,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                }
            )
        )

        with urllib.request.urlopen(geo_url, timeout=10) as response:
            geo_data = json.loads(response.read().decode("utf-8"))

        if not isinstance(geo_data, dict):
            return "Weather service returned an invalid location response."

        locations = geo_data.get("results")

        if not locations:
            return f"Could not find location: {city}"

        location = locations[0]

        if not isinstance(location, dict):
            return "Weather service returned invalid location data."

        lat = location.get("latitude")
        lon = location.get("longitude")
        location_name = location.get("name")

        if lat is None or lon is None or not location_name:
            return "Location data is incomplete. Please try another city."

        country = location.get("country", "")

        # Step 2: Fetch current weather.
        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,weather_code",
                }
            )
        )

        with urllib.request.urlopen(weather_url, timeout=10) as response:
            weather_data = json.loads(response.read().decode("utf-8"))

        if not isinstance(weather_data, dict):
            return "Weather service returned an invalid forecast response."

        current = weather_data.get("current")

        if not isinstance(current, dict):
            return "Current weather information is unavailable."

        temp = current.get("temperature_2m")
        code = current.get("weather_code")

        if temp is None or code is None:
            return "Current weather information is incomplete."

        weather_code_map = {
            0: "☀️ Clear sky",
            1: "🌤️ Mainly clear",
            2: "⛅ Partly cloudy",
            3: "☁️ Overcast",
            45: "🌫️ Fog",
            48: "🌫️ Fog",
            51: "🌧️ Light drizzle",
            61: "🌧️ Rain",
            63: "🌧️ Rain",
            65: "🌧️ Heavy rain",
            71: "❄️ Snow",
            80: "🌦️ Rain showers",
            95: "⛈️ Thunderstorm",
        }

        description = weather_code_map.get(code, "Unknown conditions")

        location_label = (
            f"{location_name}, {country}" if country else location_name
        )

        return f"{location_label}: {description}, {temp}°C"

    except (urllib.error.URLError, TimeoutError):
        return "Unable to reach the weather service. Please try again later."

    except (json.JSONDecodeError, UnicodeDecodeError):
        return "Weather service returned an invalid response."

    except (KeyError, TypeError, ValueError):
        return "Unable to process the weather information returned by the service."


def search_guides_tool(query: str) -> str:
    ensure_index()
    chunks = search_guides(query, n_results=2)

    if not chunks:
        return "No relevant information found in guides."

    return "\n\n---\n\n".join(chunks)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "budget_breakdown",
            "description": "Calculate a daily budget breakdown for a trip given destination, number of days, and total budget in USD",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "days": {"type": "integer"},
                    "budget_usd": {"type": "number"},
                },
                "required": ["destination", "days", "budget_usd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current real-time weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_guides_tool",
            "description": "Search the local travel guides for tips, recommendations, or information about a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
]


def _execute_tool_call(name: str, arguments: str) -> str:
    """Validate and execute a tool call requested by the AI model."""
    available_tools = {
        "budget_breakdown": budget_breakdown,
        "get_weather": get_weather,
        "search_guides_tool": search_guides_tool,
    }

    if name not in available_tools:
        return f"Unknown tool: {name}"

    try:
        args = json.loads(arguments)

        if not isinstance(args, dict):
            return "Invalid tool arguments: expected a JSON object."

        result = available_tools[name](**args)
        return str(result)

    except json.JSONDecodeError:
        return "Invalid tool arguments: the model returned malformed JSON."

    except (TypeError, ValueError) as error:
        return f"Invalid tool arguments: {error}"

    except Exception:
        return "Tool execution failed unexpectedly. Please try again."


def run_agent(user_question: str) -> str:
    """Run the travel assistant agent with controlled tool execution."""
    if not isinstance(user_question, str) or not user_question.strip():
        return "Please provide a travel question or request."

    # Initialize the client once and handle missing configuration.
    try:
        client = get_client()
    except RuntimeError as error:
        return str(error)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a travel planning agent. Use the available tools "
                "to help users plan trips. Always use a tool if it can "
                "answer the question more accurately, especially for "
                "real-time data or guide content."
            ),
        },
        {"role": "user", "content": user_question.strip()},
    ]

    try:
        for _ in range(5):
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=1024,
                timeout=30,
            )

            if not response.choices:
                return "The AI service returned an empty response."

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content

            messages.append(msg)

            for tc in msg.tool_calls:
                tool_result = _execute_tool_call(
                    tc.function.name, tc.function.arguments
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result,
                    }
                )

        return "Agent reached maximum iterations without a final answer."

    except OpenAIError:
        return (
            "The AI service is currently unavailable or could not "
            "complete the request. Please try again later."
        )


if __name__ == "__main__":
    print(budget_breakdown("Tokyo", 7, 1400))
    print(get_weather("Tokyo"))
    print(search_guides_tool("things to do in Tokyo"))