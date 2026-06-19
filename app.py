import streamlit as st
from src.tools import run_agent

# Page configuration
st.set_page_config(
    page_title="Travel Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
.main {
    padding-top: 1rem;
}

[data-testid="stChatMessage"] {
    border-radius: 15px;
    padding: 10px;
}

h1 {
    color: #1f77b4;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("✈️ Travel Assistant")
    st.markdown("---")
    st.markdown("### Quick Prompts")
    
    if st.button("🌤️ Weather in Paris"):
        st.session_state.quick_prompt = "What's the weather in Paris?"
        
    if st.button("💰 Budget for Tokyo"):
        st.session_state.quick_prompt = "Create a 7-day budget for Tokyo with $2000"
        
    if st.button("🏝️ Bali Guide"):
        st.session_state.quick_prompt = "Best things to do in Bali"
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Hero section
st.markdown("""
# ✈️ AI Travel Assistant

Plan smarter trips with:
- 🌍 Destination recommendations
- 🌤️ Real-time weather
- 💰 Budget planning
- 📚 Travel guides
""")

# Initialize messages with welcome message
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": """
👋 Welcome!

I can help you with:

🌍 Trip planning  
🌤️ Weather forecasts  
💰 Travel budgets  
📚 Destination guides

Try:
- "Plan a 5-day trip to Rome"
- "Weather in Tokyo"
- "Budget for Paris with $1500"
"""
        }
    ]

# Chat container
chat_container = st.container(height=500)

# Display messages
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Where would you like to travel?")

# Handle quick prompts
if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
    prompt = st.session_state.quick_prompt
    st.session_state.quick_prompt = None

# Process user input
if prompt:
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("✈️ Planning your trip..."):
                response = run_agent(prompt)

            st.markdown(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )
    
    st.rerun()