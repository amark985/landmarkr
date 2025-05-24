import requests
from bs4 import BeautifulSoup
import csv
import time
import os

BASE_URL = "https://en.wikipedia.org"
MAIN_URL = "https://en.wikipedia.org/wiki/List_of_U.S._National_Historic_Landmarks_by_state"
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "manmade_landmarks.csv")


def get_state_links():
    """Get links to all individual state landmark pages."""
    response = requests.get(MAIN_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    state_links = []
    for li in soup.select("div.div-col li a"):
        href = li.get("href")
        if href and href.startswith("/wiki/List_of_National_Historic_Landmarks_in_"):
            state_links.append(BASE_URL + href)

    return state_links


def enrich_landmark(name):
    """Use the Wikipedia API to get metadata for a landmark."""
    try:
        url = WIKI_API_URL + name.replace(" ", "_")
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data.get("title"),
                "description": data.get("extract"),
                "latitude": data.get("coordinates", {}).get("lat"),
                "longitude": data.get("coordinates", {}).get("lon"),
                "image_url": data.get("thumbnail", {}).get("source"),
                "type": "manmade"
            }
    except Exception as e:
        print(f"Error enriching {name}: {e}")
    return None


def extract_landmarks_from_state(url):
    """Scrape and enrich landmark names from a given state page."""
    print(f"Scraping: {url}")
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    landmarks = []

    table = soup.find("table", class_="wikitable")
    if not table:
        print("No landmark table found.")
        return landmarks

    rows = table.find_all("tr")[1:]  # Skip header
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 1:
            raw_name = cols[0].get_text(strip=True)
            enriched = enrich_landmark(raw_name)
            if enriched and enriched["latitude"] and enriched["longitude"]:
                landmarks.append(enriched)
            time.sleep(0.5)  # Be polite to the API

    return landmarks


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    all_landmarks = []
    state_links = get_state_links()

    for state_url in state_links:
        all_landmarks.extend(extract_landmarks_from_state(state_url))

    if all_landmarks:
        keys = ["name", "description", "latitude", "longitude", "image_url", "type"]
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_landmarks)

    print(f"Saved {len(all_landmarks)} manmade landmarks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
