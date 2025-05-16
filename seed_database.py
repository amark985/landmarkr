import csv
import json
from flask import Flask
from model import connect_to_db, db, Landmark
from crud import create_landmark_category


# Load the landmark-to-state mapping from JSON
with open("data/landmark_states.json", "r", encoding="utf-8") as f:
    name_to_state = json.load(f)

def load_landmarks_from_csv(filepath, category_id):
    """Load landmarks from a CSV and return Landmark objects."""
    landmarks = []
    with open(filepath, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        # Strip whitespace from fieldnames
        reader.fieldnames = [field.strip() for field in reader.fieldnames]

        for row in reader:
             # Strip whitespace from each key in the row
            row = {k.strip(): v for k, v in row.items()}
            
            try:
                name = row["name"]
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                state = name_to_state.get(name)

                if not state:
                    print(f"Skipping row with missing state: {row}")
                    continue
                
                # Skip duplicates
                existing = Landmark.query.filter_by(name=name).first()
                if existing:
                    print(f"Skipping duplicate landmark: {name}")
                    continue

                landmark = Landmark(
                    name=name,
                    description=row["description"],
                    type=row.get("type", "Unknown"),
                    state=state,
                    latitude=lat,
                    longitude=lon,
                    image_url=row.get("image_url", None),
                    category_id=category_id
                )
                landmarks.append(landmark)
            except Exception as e:
                print(f"Skipping row due to error: {e}")
    return landmarks

def seed():
    # Create a Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///landmarkr' 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Connect to DB and create tables
    connect_to_db(app)

    with app.app_context():
        print("Dropping and recreating tables...")
        db.drop_all()
        db.create_all()

        try:
            # Create categories
            natural = create_landmark_category("Natural")
            manmade = create_landmark_category("Manmade")

            all_landmarks = []

            # Load and insert landmarks
            all_landmarks.extend(load_landmarks_from_csv("data/natural_landmarks.csv", natural.id))
            all_landmarks.extend(load_landmarks_from_csv("data/manmade_landmarks.csv", manmade.id))

            db.session.add_all(all_landmarks)
            db.session.commit()
            print(f"Seeded {len(all_landmarks)} landmarks successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")

if __name__ == "__main__":
    seed()
