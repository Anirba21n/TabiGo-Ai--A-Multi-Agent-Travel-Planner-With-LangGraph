# TripMate-Ai---A-Multi-Agent-Travel-Planner-With-LangGraph

## How to run?
1. create the virtual Eviroment 
```bash
conda create -n travel python=3.11 -y
```
2. Activate the Enviroment 
```bash 
conda activate travel
```
3. Install the requirements
```bash
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