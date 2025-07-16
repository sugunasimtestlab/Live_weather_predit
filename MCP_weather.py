from fastmcp import FastMCP
import os
import requests

# Load your OpenWeather API key from environment
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "f8ebc5c410b25e7e0a43a01f9c360dff")

# Instantiate your MCP server
mcp = FastMCP("Weather MCP Server")

@mcp.tool(name="get_weather", description="Fetch current weather for a given city")
def get_weather(city: str) -> dict:
    """
    Queries OpenWeatherMap for the current weather in `city` and returns a structured response.
    """
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_API_KEY}&units=metric"
    )
    response = requests.get(url, timeout=10)
    data = response.json()

    if response.status_code != 200:
        # Let the MCP host handle errors
        raise Exception(f"API error: {data.get('message', 'unknown error')}")

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
    }

if __name__ == "__main__":
    # Run the server using stdio transport for MCP
    mcp.run()
