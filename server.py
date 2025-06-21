from flask import Flask, render_template, request, redirect, session, jsonify, url_for, flash
from model import connect_to_db, db, SavedLandmark
from api.wikipedia_api import fetch_wiki_data
from api.weather_api import get_current_weather, get_forecast_weather
import crud
from werkzeug.security import check_password_hash, generate_password_hash
from env.config import GOOGLE_MAPS_API_KEY, FLASK_SECRET_KEY


app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY  

connect_to_db(app)

# Welcome homepage with guest/login/signup options
@app.route("/")
def home():
    return render_template("home.html")


# Main landmark map
@app.route("/map")
def landmark_map():
    is_logged_in = "user_id" in session

    all_locations = sorted(set(l.state for l in crud.get_all_landmarks()))
    special_regions = {"U.S. Virgin Islands", "the District of Columbia", "New York City"}
    states = [loc for loc in all_locations if loc not in special_regions]
    special_regions_list = [loc for loc in all_locations if loc in special_regions]

    return render_template(
        "homepage.html", GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY, is_logged_in=is_logged_in, states=states, special_regions=special_regions_list)


# Route to login user
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # If form is missing input, show form again with error message
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        user = crud.get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("Logged in successfully!", "success")
            return redirect("/map")
        else:
            flash("Invalid login credentials.", "danger")
            return render_template("login.html")
    return render_template("login.html")


# Route to sign up user
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # If form is missing input, show form again with error message
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("signup.html")

        existing_user = crud.get_user_by_email(email)
        if existing_user:
            flash("Account already exists. Please log in.", "warning")
            return redirect("/login")
        
        # After successful signup
        password_hash = generate_password_hash(password)
        user = crud.create_user(email, password_hash)
        session["user_id"] = user.id
        flash("Account created successfully! Welcome!", "success")
        return redirect("/map")
    return render_template("signup.html")


# Route to logout users.
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    return redirect('/')


# Route to get landmarks.
@app.route("/api/landmarks")
def get_landmarks():
    name = request.args.get("name")
    state = request.args.get("state")
    landmark_type = request.args.get("type")

    # Clean up filters by removing any that are None or empty
    filters = {
        key: value for key, value in {
            "name": name,
            "state": state,
            "type": landmark_type
        }.items() if value
    }

    user_id = session.get("user_id")

    # Helper in crud.py for filtering
    landmarks = crud.get_landmarks_by_filters(filters)

    return jsonify([landmark.to_dict(user_id=user_id) for landmark in landmarks])


# Route to save landmarks for logged-in users
@app.route("/save", methods=["POST"])
def save_landmark():
    user_id = session.get("user_id")
    landmark_id = request.form.get("landmark_id")
    
    if not user_id or not landmark_id:
        return jsonify({"success": False, "message": "Unauthorized or missing data"}), 400
    
    existing = crud.save_landmark_for_user(user_id, landmark_id)

    if isinstance(existing, SavedLandmark):
        return jsonify({'success': True, 'message': 'Landmark saved!'}), 200
    else:
        return jsonify({'success': False, 'message': 'Landmark already saved'}), 200


# Route to get saved landmarks for logged-in user.
@app.route("/my_landmarks")
def my_landmarks():
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    # Get all saved landmarks for user
    saved_landmarks = crud.get_user_saved_landmarks(user_id)

    # Split into bucket list and regular saves
    bucket_list = [entry.landmark for entry in saved_landmarks if entry.is_bucket_list]
    regular_saves = [entry.landmark for entry in saved_landmarks if not entry.is_bucket_list]

    for saved in saved_landmarks:
        saved.landmark.visited = saved.visited
        
    return render_template("saved_landmarks.html", bucket_list=bucket_list, regular_saves=regular_saves)


# Route to view landmark details.
@app.route("/landmark/<int:landmark_id>")
def landmark_detail(landmark_id):
    landmark = crud.get_landmark_by_id(landmark_id)

    if not landmark:
        return "Landmark not found", 404

    wikipedia_url = f"https://en.wikipedia.org/wiki/{landmark.name.replace(' ', '_')}"
  
    user_id = session.get("user_id")

    # Fetch weather
    units = request.args.get("units", "imperial")
    weather_current = get_current_weather(landmark.latitude, landmark.longitude, units=units)
    weather_forecast = get_forecast_weather(landmark.latitude, landmark.longitude, units=units)

    return render_template("landmark_detail.html", landmark=landmark, user_id=user_id, wikipedia_url=wikipedia_url, weather_current=weather_current, weather_forecast=weather_forecast)


# Route to unsave landmarks for logged-in users
@app.route("/unsave", methods=["POST"])
def unsave_landmark():
    user_id = session.get("user_id")
    landmark_id = request.form.get("landmark_id")

    if not user_id or not landmark_id:
        return jsonify({'error': 'Invalid request'}), 400

    success = crud.unsave_landmark_for_user(user_id, landmark_id)
    if success:
        return jsonify({'message': 'Landmark removed!'})
    else:
        return jsonify({'error': 'Landmark not found'}), 404

# Route to fetch weather
@app.route("/api/weather")
def api_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lng", type=float)
    units = request.args.get("units", default="imperial")

    if lat is None or lon is None:
        return jsonify({"error": "Missing coordinates"}), 400

    current = get_current_weather(lat, lon, units=units)
    forecast = get_forecast_weather(lat, lon, units=units)

    if not current or not forecast:
        return jsonify({"error": "Weather data unavailable"}), 500

    return jsonify({
        "current": {
            "temperature": current.get("main", {}).get("temp"),
            "description": current.get("weather", [{}])[0].get("description"),
            "icon": current.get("weather", [{}])[0].get("icon"),
        },
        "forecast": forecast.get("list", [])
    })

# Route to allow user to save landmark to a bucket list under Saved Landmarks.
@app.route("/toggle-bucket/<int:landmark_id>", methods=["POST"])
def toggle_bucket_list(landmark_id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    saved = SavedLandmark.query.filter_by(user_id=user_id, landmark_id=landmark_id).first()

    if saved:
        saved.is_bucket_list = not saved.is_bucket_list
        db.session.commit()
        new_state = saved.is_bucket_list
    else:
        saved = SavedLandmark(user_id=user_id, landmark_id=landmark_id, is_bucket_list=True)
        db.session.add(saved)
        db.session.commit()
        new_state = True

    return jsonify({ 
        "success": True,
        "is_bucket_list": new_state,
        "landmark_id": landmark_id
    })

# Route to toggle the visited status for a saved landmark
@app.route("/toggle-visited/<int:landmark_id>", methods=["POST"])
def toggle_visited(landmark_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    saved = SavedLandmark.query.filter_by(user_id=user_id, landmark_id=landmark_id).first()
    if not saved:
        return jsonify({"error": "Landmark not saved"}), 400

    saved.visited = not saved.visited
    db.session.commit()

    # Calculate visited count for rewards
    visited_count = SavedLandmark.query.filter_by(user_id=user_id, visited=True).count()

    return jsonify({
        "success": True,
        "visited": saved.visited,
        "landmark_id": landmark_id,
        "visited_count": visited_count
    })


if __name__ == "__main__":
    app.run(debug=True)
