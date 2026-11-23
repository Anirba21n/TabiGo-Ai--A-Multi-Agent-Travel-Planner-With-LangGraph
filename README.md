✈️ TabGo AI — A Multi-Agent Travel Planner with LangGraph

An open-source travel planning engine powered by LangGraph, LangChain, and FastAPI. Give it a single plain-English prompt, and a team of specialized AI agents will coordinate to fetch real-time flight options, scout top-rated accommodations, and assemble a realistic day-by-day travel schedule.

🎯 The Problem & Solution
Organizing a vacation typically means juggling dozens of open browser tabs—comparing flight times on one site, cross-referencing hotel reviews on another, and manually piecing together daily activities in a notes app.

WanderFlow eliminates that tab-switching fatigue by delegating the work to an automated pipeline of four collaborative agents:

1.Flight Scout Agent: Queries live aviation data for routes and schedules.

2.Stay Curator Agent: Searches the web for tailored lodging options matching your vibe and budget.

3.Route Architect Agent: Maps out logical, time-aware daily activities.

4.Concierge Synthesizer: Merges all gathered intelligence into a clean, actionable travel brief.

Tech Stack

    Python 3.10+
    FastAPI
    Jinja2 + HTML/CSS/JavaScript frontend
    LangGraph
    LangChain
    Groq LLMs
    PostgreSQL
    Tavily API
    AviationStack API

Project Structure

.
├── app.py                # FastAPI app entry point
├── backend.py            # LangGraph travel workflow
├── requirements.txt      # Python dependencies
├── static/               # Static frontend assets
├── templates/            # HTML templates
└── tools/                # Flight and web search integrations

Prerequisites

Before running the project locally, make sure you have:

    Python 3.10 or newer installed
    PostgreSQL running and accessible
    API keys for:
        Groq
        Tavily
        AviationStack

Environment Variables

Create a .env file in the project root with the following variables:

DATABASE_URL=postgresql://user:password@localhost:5432/travel_db
GROQ_API_KEY=your_groq_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
TAVILY_API_KEY=your_tavily_api_key
DEFAULT_ORIGIN_IATA=DAC

Installation

python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

Running the App

Start the FastAPI server:

python app.py

Then open your browser at:

http://127.0.0.1:8000/

API Endpoints

    GET /health - Health check
    POST /api/travel - Submit a travel request

Example request:

curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 3-day trip to Tokyo with a budget of $1200"}'

How the Workflow Works

    The user submits a travel request.
    The flight agent gathers flight-related information.
    The hotel agent searches for accommodation suggestions.
    The itinerary agent creates a practical travel plan.
    The final agent formats the result into a polished response.

Contributing

Contributions are welcome. If you want to improve the app, add new travel features, or fix issues:

    Fork the repository
    Create a feature branch
    Make your changes
    Open a pull request

Acknowledgments

This project is built with the help of modern LLM tooling and travel APIs, and it is intended as a practical example of combining LangGraph agents with real-world applications.