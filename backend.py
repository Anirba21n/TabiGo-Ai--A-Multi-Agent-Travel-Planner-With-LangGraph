import os
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict, Annotated
import operator
import uuid
from pydantic import BaseModel, Field

import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq
from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from tools.weather_geo_tool import get_live_weather, geocode_itinerary_spots


def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your Render PostgreSQL External Database URL to .env"
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Please add it to your .env file.")


# =========================
# LLM
# =========================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY
)


# =========================
# Structured Output Schema for Map Pins
# =========================

class DaySpot(BaseModel):
    day: int = Field(description="Day number of the trip (e.g., 1, 2, 3)")
    place: str = Field(
        description="Specific landmark name including city and country for geocoding, e.g. 'Swayambhunath Temple, Kathmandu, Nepal'"
    )


class LandmarkList(BaseModel):
    spots: list[DaySpot]


# =========================
# State
# =========================

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    flight_results: str
    hotel_results: str
    weather_results: str
    itinerary: str
    map_locations: list[dict]
    llm_calls: Annotated[int, operator.add]


# =========================
# Flight Agent (Runs in Parallel)
# =========================

def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)

    return {
        "flight_results": flight_data,
        "messages": [
            AIMessage(content="Flight results fetched.")
        ],
        "llm_calls": 1
    }


# =========================
# Hotel Agent (Runs in Parallel)
# =========================

def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched.")
        ],
        "llm_calls": 1
    }


# =========================
# Weather Agent (Runs in Parallel)
# =========================

def weather_agent(state: TravelState):
    extract_prompt = (
        f"Extract ONLY the main destination city or country name from this travel query: "
        f"'{state['user_query']}'. Return just the place name with no extra words."
    )
    destination = llm.invoke([HumanMessage(content=extract_prompt)]).content.strip()
    weather_data = get_live_weather(destination)

    return {
        "weather_results": weather_data,
        "messages": [
            AIMessage(content="Live weather forecast fetched.")
        ],
        "llm_calls": 1
    }


# =========================
# Itinerary Agent (Weather-Aware & Geo-Clustered)
# =========================

def itinerary_agent(state: TravelState):
    prompt = f"""
Create a complete travel itinerary.

User Query:
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results:
{state['hotel_results']}

Live Weather Forecast:
{state['weather_results']}

Planning Rules:
1. Make the itinerary practical, budget-aware, and easy to follow.
2. Geo-Cluster Attractions: Group nearby landmarks on the same day so the traveler avoids backtracking across the city.
3. Weather-Adaptive Scheduling: Schedule outdoor sightseeing on clear/mild days and indoor museums/markets on high-rain or extreme-heat days.
4. Include a brief weather-based packing tip.
"""

    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner specializing in geographic route optimization."),
        HumanMessage(content=prompt)
    ])

    return {
        "itinerary": response.content,
        "messages": [response],
        "llm_calls": 1
    }


# =========================
# Geo Agent (Extracts Lat/Lon Pins for Frontend Map)
# =========================

def geo_agent(state: TravelState):
    try:
        structured_llm = llm.with_structured_output(LandmarkList, method="json_schema")
        extraction_prompt = f"""
Extract up to 12 key tourist landmarks/attractions per day from the itinerary below so they can be pinned on an interactive map.
Always include the city and country in each place name.

Itinerary:
{state['itinerary']}
"""
        extracted = structured_llm.invoke(extraction_prompt)
        spots_payload = [{"day": s.day, "place": s.place} for s in extracted.spots[:12]]
        pinned_locations = geocode_itinerary_spots(spots_payload)
    except Exception as e:
        print(f"Geo extraction skipped due to error: {e}")
        pinned_locations = []

    return {
        "map_locations": pinned_locations,
        "messages": [
            AIMessage(content=f"Mapped {len(pinned_locations)} itinerary locations.")
        ],
        "llm_calls": 1
    }


# =========================
# Final Response Agent
# =========================

def final_agent(state: TravelState):
    final_prompt = f"""
Generate the final travel response for the user.

User Request:
{state['user_query']}

Flights:
{state['flight_results']}

Hotels:
{state['hotel_results']}

Live Weather Forecast:
{state['weather_results']}

Itinerary:
{state['itinerary']}

Format the final answer beautifully using these sections:

1. Trip Summary
2. Live Weather & Packing Guide
3. Flight Information
4. Hotel Suggestions
5. Day-by-Day Geo-Clustered Itinerary
6. Estimated Budget
7. Final Recommendations

Important:
- Be clear and practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Keep the response useful for real travel planning.
"""

    response = llm.invoke([
        SystemMessage(content="You are a professional AI travel booking assistant."),
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": 1
    }


# =========================
# Build Graph (Parallel Fan-Out -> Fan-In)
# =========================

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("weather_agent", weather_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("geo_agent", geo_agent)
graph.add_node("final_agent", final_agent)

# Run Flight, Hotel, and Weather concurrently
graph.add_edge(START, "flight_agent")
graph.add_edge(START, "hotel_agent")
graph.add_edge(START, "weather_agent")

# Wait for all 3 before building the itinerary
graph.add_edge("flight_agent", "itinerary_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("weather_agent", "itinerary_agent")

# Geocode spots -> Generate final response
graph.add_edge("itinerary_agent", "geo_agent")
graph.add_edge("geo_agent", "final_agent")
graph.add_edge("final_agent", END)


# =========================
# PostgreSQL Checkpointer
# =========================

DATABASE_URL = get_database_url()

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

travel_graph = graph.compile(checkpointer=checkpointer)


# =========================
# Function for FastAPI
# =========================

def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "weather_results": "",
            "itinerary": "",
            "map_locations": [],
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "weather_results": result.get("weather_results", ""),
        "itinerary": result.get("itinerary", ""),
        "map_locations": result.get("map_locations", []),
        "llm_calls": result.get("llm_calls", 0),
    }