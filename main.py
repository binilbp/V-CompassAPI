# main.py
import requests
import math
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import nearestPlane

# FastAPI App Initialization
app = FastAPI()

# --- CORS Configuration ---
# uncomment the relevant addressed to enable data transfer from it
# others are blocked
origins = [
    "https://v-compass-main.vercel.app",
    "https://v-compass.vercel.app",
    # "http://localhost",
    # "http://localhost:3000",
    # "http://localhost:5173",  # Common port for Vite React projects
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
    lon: float = Query(..., description="User's longitude"),
):
    """
    Fetches plane data from OpenSky Network for a bounding box around the user's location.
    Filtering by exact radius is done on the frontend.
    """
    # Define a bounding box around the user's location
    # 1 degree of latitude is approx. 111km
    # convert 25 km to degrees
    lat_change = 10 / 111.0
    lon_change = 10 / (111.0 * math.cos(math.radians(lat)))
    params = {
        "lamin": lat - lat_change,
        "lomin": lon - lon_change,
        "lamax": lat + lat_change,
        "lomax": lon + lon_change,
    }

    try:
        # Fetch data from OpenSky Network
        response = requests.get(OPENSKY_URL, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()

        # --- Parse and Format the Data ---
        planes = []
        if data["states"]:
            for state in data["states"]:
                # See OpenSky API docs for state vector format
                plane_data = {
                    # unique flight id
                    "icao24": state[0],
                    # strip extra space from name only if not none
                    "callsign": state[1].strip() if state[1] else None,
                    "lon": state[5],  # longitude value
                    "lat": state[6],  # latitude value
                    "altitude_m": state[7],  # Barometric altitude in meters
                    "velocity_ms": state[9],  # Speed in meters/second
                }
                # Ensure we have essential data and the plane is not on the ground
                if all(
                    value is not None
                    for value in [
                        plane_data["lat"],
                        plane_data["lon"],
                        plane_data["altitude_m"],
                    ]
                ):
                    planes.append(plane_data)

        plane, distance = nearestPlane.find_nearest_plane(planes, lat, lon)
        print("return plane value", plane)
        if plane:
            # covert to km and append that too
            plane["distance"] = round(distance / 1000, 1)
            return {"plane": plane}
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching from OpenSky Network: {e}")
        raise HTTPException(
            status_code=503, detail="Could not fetch data from OpenSky Network."
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )


# A simple root endpoint to confirm the server is running
@app.get("/")
def read_root():
    return {"status": "V-Compass Backend is running"}
