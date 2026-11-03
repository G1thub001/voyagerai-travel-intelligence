# VoyagerAI — AI-Powered Travel Intelligence Assistant

VoyagerAI is an AI-powered travel planning assistant built with Python, Streamlit, OpenRouter, Retrieval-Augmented Generation (RAG), and external weather data.

It combines LLM-based reasoning, function calling, semantic document retrieval, and external API integration to help users explore destinations, plan travel budgets, and access relevant travel information.

## Problem

Travel planning often involves gathering information from different sources, including destination guides, weather conditions, and budget estimates.

VoyagerAI explores how an AI agent can bring these capabilities together through a conversational interface, using specialized tools to provide more context-aware travel assistance.

## Features

### AI-Powered Travel Assistance
Conversational travel assistance powered by an OpenRouter-hosted language model through an OpenAI-compatible API.

### Intelligent Tool Calling
The agent can select and execute specialized tools based on a user's request:

- **Budget Planning:** Calculates daily and category-based budget allocations.
- **Weather Information:** Retrieves current weather conditions using the Open-Meteo API.
- **Travel Guide Search:** Retrieves relevant destination information from a local semantic knowledge base.

### Retrieval-Augmented Generation (RAG)
A ChromaDB-backed retrieval pipeline uses Sentence Transformers to generate embeddings and retrieve relevant travel guide content through semantic similarity search.

The knowledge base currently includes starter guides for Japan, Italy, and Kenya.

### External Weather Integration
Uses Open-Meteo geocoding and forecast endpoints to retrieve city coordinates and current weather conditions.

### Conversational Interface
A Streamlit interface provides an accessible way to interact with the travel assistant.

## Architecture

```text
                  ┌──────────────────────┐
                  │     Streamlit UI     │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │     AI Agent         │
                  │     OpenRouter       │
                  └──────────┬───────────┘
                             │
                  ┌──────────┴───────────┐
                  │    Tool Selection    │
                  └──────────┬───────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
      ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
      │   Budget    │ │   Weather   │ │  Travel RAG  │
      │ Calculator  │ │  Open-Meteo │ │  ChromaDB    │
      └─────────────┘ └─────────────┘ └──────┬───────┘
                                             │
                                    ┌────────▼────────┐
                                    │ Sentence        │
                                    │ Transformers    │
                                    └─────────────────┘

                  Agent synthesizes results
                             │
                             ▼
                  Conversational response
```

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| Frontend | Streamlit |
| LLM integration | OpenRouter |
| LLM SDK | OpenAI Python SDK |
| Vector database | ChromaDB |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Weather data | Open-Meteo API |
| Testing | Pytest |

## Project Structure

```text
voyagerai-travel-intelligence/
│
├── app.py
├── README.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
│
├── data/
│   └── travel_guides/
│       ├── japan.md
│       ├── italy.md
│       └── kenya.md
│
├── src/
│   ├── __init__.py
│   ├── ai_assistant.py
│   ├── main.py
│   ├── rag.py
│   └── tools.py
│
└── tests/
    └── test_agent.py
```

## Getting Started

### Prerequisites

- Python 3.13
- Git
- An OpenRouter API key

### 1. Clone the repository

```bash
git clone https://github.com/G1thub001/voyagerai-travel-intelligence.git
cd voyagerai-travel-intelligence
```

### 2. Create a virtual environment

```bash
python3.13 -m venv .venv
```

Activate it:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local environment file:

```bash
cp .env.example .env
```

Add your OpenRouter API key to `.env`:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Never commit your `.env` file or expose API credentials.

### 5. Run the application

```bash
streamlit run app.py
```

The application will be available at the local URL displayed by Streamlit.

## Running Tests

Run the automated test suite:

```bash
pytest -v
```

The tests cover agent execution, tool handling, input validation, API error handling, and weather-related scenarios.

## Knowledge Base

Travel guide documents are stored in:

```text
data/travel_guides/
```

The RAG pipeline:

1. Reads the available Markdown travel guides.
2. Splits documents into overlapping text chunks.
3. Generates embeddings using Sentence Transformers.
4. Stores document chunks and metadata in ChromaDB.
5. Detects modified documents using SHA-256 content hashes.
6. Retrieves semantically relevant chunks for user queries.

The local ChromaDB database is generated automatically and stored under:

```text
storage/chroma/
```

This generated database is excluded from version control and is rebuilt from the source travel guides when required.

## Current Scope and Limitations

- The knowledge base currently contains starter guides for Japan, Italy, and Kenya.
- Weather integration provides current conditions rather than a complete travel forecast.
- Budget allocations use predefined percentage estimates and do not represent live accommodation, transport, or activity prices.
- Travel information generated by an LLM should be independently verified before making bookings or travel decisions.
- An OpenRouter API key is required for AI-powered interactions.

## Future Development

Potential areas for further development include:

- Expansion of the destination knowledge base.
- More advanced itinerary generation.
- Integration of additional travel and accommodation data sources.
- Improved retrieval evaluation and ranking.
- Enhanced conversational context management.
- Expanded automated testing and observability.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
