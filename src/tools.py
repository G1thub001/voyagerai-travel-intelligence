import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import urllib.request
import urllib.parse

from src.rag import search_guides, ensure_index
from src.ai_assistant import client, MODEL


def budget_breakdown(destination: str, days: int, budget_usd: float) -> str:
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
    try:
        # Step 1: Geocode city
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
            geo_data = json.loads(response.read().decode())

        if "results" not in geo_data:
            return f"Could not find location: {city}"

        location = geo_data["results"][0]

        lat = location["latitude"]
        lon = location["longitude"]
        location_name = location["name"]
        country = location.get("country", "")

        # Step 2: Fetch weather
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
            weather_data = json.loads(response.read().decode())

        current = weather_data["current"]

        temp = current["temperature_2m"]
        code = current["weather_code"]

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

        return (
            f"{location_name}, {country}: "
            f"{description}, {temp}°C"
        )

    except Exception as error:
        return f"Weather error: {type(error).__name__}: {error}"


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


def run_agent(user_question: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a travel planning agent. Use the available tools to help users plan trips. Always use a tool if it can answer the question more accurately — especially for real-time data or guide content.",
        },
        {"role": "user", "content": user_question},
    ]

    for _ in range(5):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=1024,
            timeout=30,
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        messages.append(msg)

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)

            print(f"[Tool call] {name}({args})")

            if name == "budget_breakdown":
                result = budget_breakdown(**args)
            elif name == "get_weather":
                result = get_weather(**args)
            elif name == "search_guides_tool":
                result = search_guides_tool(**args)
            else:
                result = f"Unknown tool: {name}"

            print(f"[Tool result] {result[:120]}...")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return "Agent reached maximum iterations."


if __name__ == "__main__":
    print(budget_breakdown("Tokyo", 7, 1400))
    print(get_weather("Tokyo"))
    print(search_guides_tool("things to do in Tokyo"))