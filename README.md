# ✈️ AI Travel Assistant

An AI-powered travel planning assistant built with Python, Streamlit, OpenAI-compatible models, Retrieval-Augmented Generation (RAG), and real-time weather data.

## Features

### 🌍 Travel Planning

Get destination recommendations, travel advice, and itinerary suggestions.

### 🌤️ Real-Time Weather

Retrieve current weather information for cities worldwide using Open-Meteo.

### 💰 Budget Planning

Generate travel budget breakdowns based on destination, trip duration, and total budget.

### 📚 Travel Guide Search

Search local travel guides using Retrieval-Augmented Generation (RAG).

### 💬 Conversational Interface

Interactive Streamlit chat interface for natural travel planning conversations.

---

## Tech Stack

* Python
* Streamlit
* OpenAI-Compatible API (OpenRouter)
* Open-Meteo Weather API
* ChromaDB
* Retrieval-Augmented Generation (RAG)

---

## Project Structure

```text
trip_notes/
│
├── app.py
│
├── src/
│   ├── ai_assistant.py
│   ├── main.py
│   ├── rag.py
│   ├── tools.py
│   └── __init__.py
│
├── tests/
│   └── test_agent.py
│
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/G1thub001/Travel-assistant.git
cd Travel-assistant
```

Install dependencies:

```bash
pip install streamlit openai chromadb python-dotenv
```

Create a `.env` file inside the `src` directory:

```env
OPENROUTER_API_KEY=your_api_key_here
```

---

## Running the Application

Launch the Streamlit interface:

```bash
streamlit run app.py
```

The application will open in your browser at:

```text
http://localhost:8501
```

---

## Example Questions

* What is the weather in Nairobi?
* Create a 7-day budget for Tokyo with $2000.
* Recommend things to do in Paris.
* Plan a 5-day trip to Rome.
* Find travel tips for Bali.

---

## Future Improvements

* Flight search integration
* Hotel recommendations
* Currency conversion
* Interactive maps
* Multi-day itinerary generation
* User authentication

---

## Author

Brian Kibagendi

GitHub:
https://github.com/G1thub001
