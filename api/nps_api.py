import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from model import db, connect_to_db, Landmark
from server import app  # or your Flask app file
from env.config import NPS_API_KEY

# Define the NPS API endpoint and your API key
NPS_API_URL = "https://developer.nps.gov/api/v1/places?limit=50"
API_KEY = NPS_API_KEY 

# Parameters for fetching historical landmarks (you can adjust these)
params = {
    "api_key": API_KEY,
    "q": "historic",  # Searching for historical landmarks
    "limit": 50,  # Number of results per request
}

def fetch_historical_landmarks():
    """Fetch historical landmark info from the National Park Service API."""
    response = requests.get(NPS_API_URL, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get("data", [])
    else:
        print(f"Error fetching data: {response.status_code}")
        return []

def save_landmarks_to_db():
    """Loop through the historical landmarks, fetch info, and save to the database."""
    landmarks_data = fetch_historical_landmarks()

    if not landmarks_data:
        print("No data found or failed to fetch data.")
        return

    for landmark_data in landmarks_data:
        name = landmark_data.get("name", "No name")
        description = landmark_data.get("description", "No description")
        latitude = landmark_data.get("latitude")
        longitude = landmark_data.get("longitude")
        images = landmark_data.get("images", [])
        image_url = images[0]["url"] if images else "No image"
        state = landmark_data.get("state", "No state")
        city = landmark_data.get("city", "No city")
        type = "manmade"  # Since we filtered by "manmade"

        # Ensure latitude and longitude are available
        if latitude and longitude:
            landmark = Landmark(
                name=name,
                description=description,
                latitude=latitude,
                longitude=longitude,
                image_url=image_url,
                type=type,
                state=state,
                city=city
            )
            db.session.add(landmark)

    db.session.commit()
    print(f"{len(landmarks_data)} manmade landmarks saved!")


if __name__ == "__main__":
    with app.app_context():
        connect_to_db(app)
        save_landmarks_to_db()
