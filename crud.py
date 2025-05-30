from model import db, User, Landmark, SavedLandmark, LandmarkCategory

"""User CRUD Functions"""

def create_user(email, password_hash):
    user = User(email=email, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def get_user_by_id(user_id):
    return User.query.get(user_id)


"""Landmark CRUD Functions"""


def create_landmark(name, description, type, state, latitude, longitude, image_url, category_id=None):
    existing = Landmark.query.filter_by(name=name).first()
    if existing:
        return existing  # or raise an error, or return None
    landmark = Landmark(
        name=name,
        description=description,
        type=type,
        state=state,
        latitude=latitude,
        longitude=longitude,
        image_url=image_url,
        category_id=category_id
    )
    db.session.add(landmark)
    db.session.commit()
    return landmark

def get_landmark_by_id(landmark_id):
    return Landmark.query.get(landmark_id)

def get_all_landmarks():
    return Landmark.query.all()

def get_landmarks_by_state(state):
    return Landmark.query.filter_by(state=state).all()

def get_landmarks_by_type(landmark_type):
    return Landmark.query.filter_by(type=landmark_type).all()

def get_landmarks_by_name(name):
    return Landmark.query.filter(Landmark.name.ilike(f"%{name}%")).all()

def get_landmarks_by_filters(filters):
    """Return landmarks filtered by optional name, state, and type."""
    query = Landmark.query

    if "name" in filters:
        query = query.filter(Landmark.name.ilike(f"%{filters['name']}%"))

    if "state" in filters:
        query = query.filter(Landmark.state.ilike(filters["state"]))

    if "type" in filters:
        query = query.filter(Landmark.type.ilike(filters["type"]))

    return query.all()


"""Saved Landmark CRUD Functions"""


def save_landmark_for_user(user_id, landmark_id):
    existing = SavedLandmark.query.filter_by(user_id=user_id, landmark_id=landmark_id).first()
    if existing:
        return existing # Already saved, no need to add again
    
    saved = SavedLandmark(user_id=user_id, landmark_id=landmark_id)
    db.session.add(saved)
    db.session.commit()
    return saved
    
def get_user_saved_landmarks(user_id):
    saved = SavedLandmark.query.filter_by(user_id=user_id).all()
    return [entry.landmark for entry in saved]

def unsave_landmark_for_user(user_id, landmark_id):
    saved = SavedLandmark.query.filter_by(user_id=user_id, landmark_id=landmark_id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
        return True
    return False


"""Landmark Category CRUD Functions"""

def create_landmark_category(name):
    category = LandmarkCategory(name=name)
    db.session.add(category)
    db.session.commit()
    return category

def get_all_categories():
    return LandmarkCategory.query.all()

def get_category_by_id(category_id):
    return LandmarkCategory.query.get(category_id)