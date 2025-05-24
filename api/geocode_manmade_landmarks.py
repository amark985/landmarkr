import csv
import requests
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from env.config import GOOGLE_MAPS_API_KEY

API_KEY = GOOGLE_MAPS_API_KEY
INPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "manmade_landmarks.csv"))
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "manmade_landmarks_with_coords.csv"))

def geocode_place(name, state):
    address = f"{name}, {state}, USA"
    url = f"https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results")
        if results:
            location = results[0]["geometry"]["location"]
            return location["lat"], location["lng"]
    except Exception as e:
        print(f"Failed to geocode {address}: {e}")
    return None, None

def enrich_csv_with_coords():
    with open(INPUT_FILE, "r", encoding="utf-8") as infile, open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["latitude", "longitude"] if "latitude" not in reader.fieldnames else reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if not row.get("latitude") or not row.get("longitude"):
                lat, lon = geocode_place(row["name"], row["state"])
                if lat and lon:
                    row["latitude"] = lat
                    row["longitude"] = lon
                    print(f"Geocoded: {row['name']} -> ({lat}, {lon})")
                else:
                    print(f"No coordinates for: {row['name']}")
                time.sleep(0.2)  # Google rate limit
            writer.writerow(row)

if __name__ == "__main__":
    enrich_csv_with_coords()
