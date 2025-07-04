import csv
import json
from flask import Flask
from model import connect_to_db, db, Landmark
from crud import create_landmark_category


# Load the landmark-to-state mapping from JSON
with open("data/landmark_states.json", "r", encoding="utf-8") as f:
    name_to_state = json.load(f)

def load_landmarks_from_csv(filepath, category_id, use_name_to_state=False):
    """Load landmarks from a CSV and return Landmark objects."""
    landmarks = []
    with open(filepath, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        # Strip whitespace from fieldnames
        reader.fieldnames = [field.strip() for field in reader.fieldnames]

        for row in reader:
             # Strip whitespace from each key in the row
            row = {k.strip().lower(): v for k, v in row.items()}
            
            try:
                name = row["name"]
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                state = row.get("state")

                if not state or state.strip() == "":
                    print(f"Skipping row with missing state: {row}")
                    continue
                
                # Skip duplicates
                existing = Landmark.query.filter_by(
                    name=name,
                    state=state,
                    latitude=lat,
                    longitude=lon
                    ).first()
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
                print(f"Row data: {row}")

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
            # Use name_to_state mapping only for natural landmarks
            all_landmarks.extend(load_landmarks_from_csv("data/natural_landmarks.csv", natural.id, use_name_to_state=True))
            # For manmade landmarks, just use the CSV 'state' column directly
            all_landmarks.extend(load_landmarks_from_csv("data/manmade_landmarks_with_descriptions.csv", manmade.id, use_name_to_state=False))

            db.session.add_all(all_landmarks)
            db.session.commit()
            print(f"Seeded {len(all_landmarks)} landmarks successfully.")

            featured_info = {
                "Statue of Liberty National Monument": "Statue_of_Liberty_National_Monument.jpg",
                "Grand Canyon National Park": "Grand_Canyon_National_Park.jpg",
                "Martin Luther King Jr. National Historical Park": "Martin_Luther_King_Jr._National_Historical_Park.jpg"
            }

            for name, image_filename in featured_info.items():
                landmark = Landmark.query.filter_by(name=name).first()
                if landmark:
                    landmark.featured = True
                    landmark.featured_image_filename = image_filename

            db.session.commit()
            print("Featured landmarks updated.")

        except Exception as e:
            db.session.rollback()
            print(f"Error during seeding: {e}")

if __name__ == "__main__":
    seed()
