# ✈️ AI Travel Assistant

An AI-powered travel intelligence assistant built with Python, Streamlit, Retrieval-Augmented Generation (RAG), ChromaDB, OpenRouter, and real-time weather data.

The application combines LLM reasoning, document retrieval, and external API data to provide context-aware travel recommendations, itinerary planning, budget guidance, and destination information.

---

## 🎯 Problem

Travel planning often requires combining information from multiple sources such as destination guides, weather conditions, budgets, and local recommendations.

This project explores how an AI assistant can combine retrieved domain-specific information with real-time external data to produce more useful and context-aware travel responses.

---

## 🚀 Features

### 🌍 Travel Planning

Generate destination recommendations, travel advice, and itinerary suggestions based on user requirements.

### 🌤️ Real-Time Weather

Retrieve current weather information for destinations using the Open-Meteo API.

### 💰 Budget Planning

Generate travel budget breakdowns based on destination, duration, and available budget.

### 📚 Retrieval-Augmented Generation

Search a ChromaDB-backed travel knowledge base and provide retrieved context to the LLM before generating responses.

### 💬 Conversational Interface

Interactive Streamlit interface for natural-language travel planning.

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │    Streamlit UI     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   AI Assistant      │
                    │   Orchestration     │
                    └───────┬─────┬───────┘
                            │     │
                ┌───────────┘     └────────────┐
                ▼                              ▼
       ┌─────────────────┐            ┌─────────────────┐
       │   RAG Pipeline  │            │ External Tools  │
       │                 │            │                 │
       │   ChromaDB      │            │ Open-Meteo      │
       │   Retrieval     │            │ Weather API     │
       └────────┬────────┘            └────────┬────────┘
                │                              │
                └──────────────┬───────────────┘
                               ▼
                    ┌─────────────────────┐
                    │ OpenRouter / LLM    │
                    │ Response Generation │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Streamlit Response  │
                    └─────────────────────┘
