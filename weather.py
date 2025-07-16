import streamlit as st
import requests
import json

# --- Configuration ---
WEATHER_API_KEY = "f8ebc5c410b25e7e0a43a01f9c360dff"
LLM_API_URL = "http://192.168.1.121:1234/v1/chat/completions"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Weather API Function ---
def get_weather(city):
    """Get current weather data for a city"""
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "pressure": data["main"]["pressure"]
                }
            }
        else:
            return {
                "success": False,
                "error": f"City not found or API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }

# --- LLM with Function Calling ---
def ask_llm_with_tools(messages):
    """Send request to LLM with function calling capability"""

    # Define the weather function for the LLM
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather information for a specified city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The name of the city to get weather for"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    payload = {
        "model": "llama 8B",
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.3
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(LLM_API_URL, data=json.dumps(payload), headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            assistant_message = result['choices'][0]['message']

            # Check if LLM wants to call a function
            if assistant_message.get('tool_calls'):
                return handle_function_calls(messages, assistant_message)
            else:
                # Regular response without function calling
                return assistant_message['content']
        else:
            return f"LLM error: {response.status_code} - {response.text}"

    except Exception as e:
        return f"LLM request failed: {str(e)}"

def handle_function_calls(original_messages, assistant_message):
    """Handle function calls made by the LLM"""

    # Add the assistant's message with tool calls to conversation
    messages = original_messages + [assistant_message]

    # Process each function call
    for tool_call in assistant_message['tool_calls']:
        function_name = tool_call['function']['name']
        function_args = json.loads(tool_call['function']['arguments'])

        if function_name == "get_weather":
            # Call the actual weather function
            weather_result = get_weather(function_args['city'])

            # Add function result to conversation
            function_message = {
                "role": "tool",
                "tool_call_id": tool_call['id'],
                "content": json.dumps(weather_result)
            }
            messages.append(function_message)

    # Send the conversation back to LLM to generate final response
    return get_final_response(messages)

def get_final_response(messages):
    """Get the final response from LLM after function calls"""
    payload = {
        "model": "llama 8B",
        "messages": messages,
        "temperature": 0.3
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(LLM_API_URL, data=json.dumps(payload), headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Error getting final response: {response.status_code}"

    except Exception as e:
        return f"Final response request failed: {str(e)}"

# --- Streamlit UI ---
st.set_page_config(page_title="Smart Weather Chatbot", page_icon="🌦️")
st.title("🌦️ Smart Weather Chatbot")
st.markdown("Ask me about weather in any city, or chat about anything else!")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
query = st.chat_input("Ask me about weather or anything else...")

if query:
    # Display user message
    st.chat_message("user").markdown(query)
    st.session_state.chat_history.append({"role": "user", "content": query})

    # Prepare messages for LLM (include recent chat history for context)
    recent_messages = [
        {"role": "system", "content": """You are a helpful assistant with access to weather information.
        When users ask about weather, use the get_weather function to retrieve current weather data.
        Provide friendly, informative responses about weather conditions.
        For non-weather questions, respond normally as a helpful assistant."""}
    ]

    # Add recent chat history (last 10 messages to avoid token limits)
    recent_messages.extend(st.session_state.chat_history[-10:])

    # Get response from LLM
    with st.spinner("Thinking..."):
        response = ask_llm_with_tools(recent_messages)

    # Display assistant response
    st.chat_message("assistant").markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# --- Sidebar with Info ---
with st.sidebar:
    st.header("About")
    st.markdown("""
    This chatbot can:
    - 🌤️ Get current weather for any city
    - 💬 Have general conversations
    - 🧠 Intelligently decide when to fetch weather data

    **Examples:**
    - "What's the weather in Tokyo?"
    - "Compare weather between London and Paris"
    - "Is it raining in Mumbai right now?"
    """)

    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()