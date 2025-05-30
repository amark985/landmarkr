import requests
from bs4 import BeautifulSoup
import csv
import time
import os

BASE_URL = "https://en.wikipedia.org"
MAIN_URL = "https://en.wikipedia.org/wiki/List_of_U.S._National_Historic_Landmarks_by_state"
WIKI_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "manmade_landmarks_with_descriptions.csv")


def get_state_links():
    """Get links to all individual state landmark pages."""
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


def enrich_landmark(name):
    """Use the Wikipedia API to get metadata for a landmark."""
    try:
        url = WIKI_API_URL + name.replace(" ", "_")
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()

            if data.get("type") == "disambiguation":
                print(f"⚠️ Skipping disambiguation: {name}")
                return None
            
            lat = data.get("coordinates", {}).get("lat")
            lon = data.get("coordinates", {}).get("lon")
            
            return {
                "name": data.get("title"),
                "description": data.get("extract"),
                "latitude": lat,
                "longitude": lon,
                "image_url": data.get("thumbnail", {}).get("source"),
                "type": "Manmade"
            }
        else:
            print(f"⚠️ API error for {name}: Status {resp.status_code}")
    except Exception as e:
        print(f"Error enriching {name}: {e}")
    return None


def extract_landmarks_from_state(url):
    """Scrape and enrich landmark names from a given state page."""
    print(f"Scraping: {url}")
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    landmarks = []

    # Extract the state name from the URL
    state_name = url.split("List_of_National_Historic_Landmarks_in_")[-1].replace("_", " ")

    tables = soup.find_all("table", class_="wikitable")
    if not tables:
        print("No landmark table found.")
        return landmarks
    
    for table in tables:
        rows = table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 1:
                link = cols[0].find("a")
                if link and link.get("href"):
                    page_title = link.get("href").split("/wiki/")[-1]
                    print(f"Attempting to enrich: {page_title}")
                    enriched = enrich_landmark(page_title)

                    if enriched:
                        enriched["state"] = state_name  # Add state
                        landmarks.append(enriched)

            time.sleep(0.5)  

    return landmarks


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    all_landmarks = []
    seen = set()  # Track (name, state) pairs to avoid duplicates
    state_links = get_state_links()
    
    for state_url in state_links:
        landmarks = extract_landmarks_from_state(state_url)
        for landmark in landmarks:
            identifier = (landmark["name"], landmark["state"])
            if identifier not in seen:
                seen.add(identifier)
                all_landmarks.append(landmark)

    if all_landmarks:
        keys = ["name", "description", "latitude", "longitude", "state", "image_url", "type"]
        with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_landmarks)

    print(f"Saved {len(all_landmarks)} unique manmade landmarks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
