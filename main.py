# main.py
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# --- FastAPI App Initialization ---
app = FastAPI()

# --- CORS Configuration ---
# This allows your React app (running on localhost:3000 or similar)
# to make requests to this backend (running on localhost:8000).
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", # Common port for Vite React projects
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- OpenSky Network API Endpoint ---
OPENSKY_URL = "https://opensky-network.org/api/states/all"

# --- API Endpoint to Get Planes ---
@app.get("/api/planes")
def get_planes_near_me(
    lat: float = Query(..., description="User's latitude"),
    lon: float = Query(..., description="User's longitude")
):
    """
    Fetches plane data from OpenSky Network for a bounding box around the user's location.
    The bounding box is roughly 2 degrees, which is over 200km.
    Filtering by exact radius is done on the frontend.
    """
    # Define a bounding box around the user's location
    # 1 degree of latitude is approx. 111km, so +/- 1 degree gives a large area
    params = {
        'lamin': lat - 1.0,
        'lomin': lon - 1.0,
        'lamax': lat + 1.0,
        'lomax': lon + 1.0,
    }

    try:
        # Fetch data from OpenSky Network
        response = requests.get(OPENSKY_URL, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        
        # --- Parse and Format the Data ---
        planes = []
        if data['states']:
            for state in data['states']:
                # See OpenSky API docs for state vector format
                plane_data = {
                    "icao24": state[0],
                    "callsign": state[1].strip() if state[1] else None,
                    "lon": state[5],
                    "lat": state[6],
                    "altitude_m": state[7],  # Barometric altitude in meters
                    "velocity_ms": state[9], # Speed in meters/second
                }
                # Ensure we have essential data and the plane is not on the ground
                if all(v is not None for v in [plane_data['lat'], plane_data['lon'], plane_data['altitude_m']]):
                    planes.append(plane_data)
        
        return {"planes": planes}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching from OpenSky Network: {e}")
        raise HTTPException(status_code=503, detail="Could not fetch data from OpenSky Network.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# A simple root endpoint to confirm the server is running
@app.get("/")
def read_root():
    return {"status": "V-Compass Backend is running"}