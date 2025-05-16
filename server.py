from flask import Flask, render_template, request, redirect, session, jsonify
from model import connect_to_db, db
import crud
from werkzeug.security import check_password_hash, generate_password_hash
from env.config import GOOGLE_MAPS_API_KEY, FLASK_SECRET_KEY


app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY  

connect_to_db(app)

# Homepage route with Login and Signup
@app.route("/", methods=["GET", "POST"])
def homepage():
    if request.method == "POST":
        # Handle login or signup
        email = request.form["email"]
        password = request.form["password"]

        # Check if it's a login or signup action
        action = request.form["action"]

        if action == "login":
            # Attempt login
            user = crud.get_user_by_email(email)
            if user and check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                return redirect("/")  # Redirect to the homepage after login
            else:
                return "Invalid credentials, please try again."

        elif action == "signup":
            # Handle signup
            existing_user = crud.get_user_by_email(email)
            if existing_user:
                return "Account already exists."

            # In production, hash the password!
            password_hash = generate_password_hash(password)
            user = crud.create_user(email, password_hash)
            session["user_id"] = user.id
            return redirect("/")  # Redirect to the homepage after signup

    # If it's a GET request, render the homepage with login/signup form
    return render_template("homepage.html", GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY)

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
    
    if not user_id:
        return redirect("/")  # Redirect to the homepage if the user is not logged in
    
    if not landmark_id:
        return "Missing landmark ID", 400

    crud.save_landmark_for_user(user_id, landmark_id)
    return render_template("saved_landmarks.html")
    #return redirect("/")  # Redirect to the homepage after saving the landmark

if __name__ == "__main__":
    app.run(debug=True)
