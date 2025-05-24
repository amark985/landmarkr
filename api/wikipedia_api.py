import requests
import csv
import os
import time
import json
from bs4 import BeautifulSoup
from tqdm import tqdm


BASE_URL = "https://en.wikipedia.org"
MAIN_URL = "https://en.wikipedia.org/wiki/List_of_U.S._National_Historic_Landmarks_by_state"

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

with open(os.path.join(DATA_DIR, "landmark_states.json"), "r", encoding="utf-8") as f:
    PARK_STATE_MAP = json.load(f)

# --- NATURAL LANDMARKS VIA REST API (National Parks) ---

national_parks = [
    "Acadia National Park", "Arches National Park", "Badlands National Park", "Big Bend National Park",
    "Biscayne National Park", "Black Canyon of the Gunnison National Park", "Bryce Canyon National Park",
    "Canyonlands National Park", "Capitol Reef National Park", "Carlsbad Caverns National Park",
    "Channel Islands National Park", "Congaree National Park", "Crater Lake National Park",
    "Cuyahoga Valley National Park", "Death Valley National Park", "Denali National Park and Preserve",
    "Dry Tortugas National Park", "Everglades National Park", "Gates of the Arctic National Park and Preserve",
    "Gateway Arch National Park", "Glacier Bay National Park and Preserve", "Glacier National Park (U.S.)",
    "Grand Canyon National Park", "Grand Teton National Park", "Great Basin National Park",
    "Great Sand Dunes National Park and Preserve", "Great Smoky Mountains National Park",
    "Guadalupe Mountains National Park", "Haleakalā National Park", "Hawaiʻi Volcanoes National Park",
    "Hot Springs National Park", "Indiana Dunes National Park", "Isle Royale National Park",
    "Joshua Tree National Park", "Katmai National Park and Preserve", "Kenai Fjords National Park",
    "Kings Canyon National Park", "Kobuk Valley National Park", "Lake Clark National Park and Preserve",
    "Lassen Volcanic National Park", "Mammoth Cave National Park", "Mesa Verde National Park",
    "Mount Rainier National Park", "New River Gorge National Park and Preserve", "North Cascades National Park",
    "Olympic National Park", "Petrified Forest National Park", "Pinnacles National Park",
    "Redwood National and State Parks", "Rocky Mountain National Park", "Saguaro National Park",
    "Sequoia National Park", "Shenandoah National Park", "Theodore Roosevelt National Park",
    "Virgin Islands National Park", "Voyageurs National Park", "White Sands National Park",
    "Wind Cave National Park", "Wrangell–St. Elias National Park and Preserve", "Yellowstone National Park",
    "Yosemite National Park", "Zion National Park"
]

def fetch_wiki_data(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "name": data.get("title"),
            "description": data.get("extract"),
            "latitude": data.get("coordinates", {}).get("lat"),
            "longitude": data.get("coordinates", {}).get("lon"),
            "image_url": data.get("thumbnail", {}).get("source"),
            "type": "natural",
            "source": url,
            "state": PARK_STATE_MAP.get(title)
        }
    return None

def scrape_natural_landmarks():
    results = []
    
    for park in national_parks:
        print(f"Fetching: {park}")
        data = fetch_wiki_data(park)
        if data and data["latitude"] and data["longitude"]:
            results.append(data)
        time.sleep(0.5) 

    path = os.path.join(DATA_DIR, "natural_landmarks.csv")
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} natural landmarks to {path}")


# --- MANMADE LANDMARKS VIA SCRAPING TABLES ---

def get_state_links():
    response = requests.get(MAIN_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    state_links = []
    for a in soup.select("a[href^='/wiki/List_of_National_Historic_Landmarks_in_']"):
        href = a.get("href")
        if href and href.startswith("/wiki/List_of_National_Historic_Landmarks_in_"):
            full_url = BASE_URL + href
            if full_url not in state_links:
                state_links.append(full_url)
    return state_links

def extract_landmarks_from_state(url):
    print(f"Scraping {url}")

    # --- Get state name from URL ---
    state = url.split("_in_")[-1].replace("_", " ")

    try:
        resp = requests.get(url, headers={"User-Agent": "LandmarkScraperBot/1.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    landmarks = []
    tables = soup.find_all("table", class_="wikitable")

    for table in tables:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            name = cols[0].get_text(strip=True)
            description = cols[1].get_text(strip=True)

            img_tag = cols[0].find("img")
            img_url = "https:" + img_tag["src"] if img_tag and img_tag.get("src") else None

            geo_span = row.find("span", class_="geo")
            latitude = longitude = None
            if geo_span:
                coords = geo_span.get_text(strip=True).split(',')
                if len(coords) == 2:
                    try:
                        latitude = float(coords[0].strip())
                        longitude = float(coords[1].strip())
                    except ValueError:
                        latitude = longitude = None

            # Crude type detection
            desc_lower = description.lower()
            if any(word in desc_lower for word in ["park", "forest", "river", "natural", "canyon", "preserve"]):
                landmark_type = "natural"
            else:
                landmark_type = "manmade"

            landmarks.append({
                "name": name,
                "description": description,
                "latitude": latitude,
                "longitude": longitude,
                "image_url": img_url,
                "type": landmark_type,
                "state": state
            })
    return landmarks


def backfill_image_from_wikipedia(title):
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    try:
        resp = requests.get(api_url, headers={"User-Agent": "LandmarkScraperBot/1.0"})
        if resp.status_code == 200:
            data = resp.json()
            return data.get("thumbnail", {}).get("source")
    except Exception as e:
        print(f"Image backfill failed for {title}: {e}")
    return None


def scrape_manmade_landmarks():
    all_landmarks = []
    state_links = get_state_links()

    for url in state_links:
        landmarks = extract_landmarks_from_state(url)
        all_landmarks.extend(landmarks)

    manmade_landmarks = [lm for lm in all_landmarks if lm["type"] == "manmade"]

    print("Backfilling missing images...")
    for lm in tqdm(manmade_landmarks, desc="Backfilling"):
        if not lm["image_url"]:
            lm["image_url"] = backfill_image_from_wikipedia(lm["name"])
            time.sleep(1.0)  # be polite to Wikipedia API

    fieldnames = ["name", "description", "latitude", "longitude", "state", "image_url", "type"]
    path = os.path.join(DATA_DIR, "manmade_landmarks.csv")
    with open(path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lm in manmade_landmarks:
            writer.writerow({key: lm.get(key, "") for key in fieldnames})

    print(f"Saved {len(manmade_landmarks)} manmade landmarks to {path}")
    print(f"Found {len(state_links)} state links")



# --- Run Both ---

if __name__ == "__main__":
    scrape_natural_landmarks()
    scrape_manmade_landmarks()
