from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask import session

db = SQLAlchemy()

class User(db.Model): 
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)

    saved_landmarks = relationship('SavedLandmark', backref='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class Landmark(db.Model):
    __tablename__ = 'landmarks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String)  # 'natural' or 'manmade'
    state = db.Column(db.String)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("landmark_categories.id"), nullable=False)

    category = relationship('LandmarkCategory', backref='landmarks')
    saved_by_users = relationship('SavedLandmark', backref='landmark', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Landmark id={self.id} name='{self.name}' state={self.state} type={self.type}>"
    
    def to_dict(self, user_id=None):
        saved = False
        bucketed = False

        if user_id:
            saved = db.session.query(
                db.exists().where(
                    (SavedLandmark.user_id == user_id) & 
                    (SavedLandmark.landmark_id == self.id)
                )
            ).scalar()

            bucketed = db.session.query(
                db.exists().where(
                    (SavedLandmark.user_id == user_id) & 
                    (SavedLandmark.landmark_id == self.id) & 
                    (SavedLandmark.is_bucket_list == True)
                )
            ).scalar()

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "state": self.state,
            "lat": self.latitude,
            "lng": self.longitude,
            "image_url": self.image_url,
            "is_saved": saved,
            "on_bucket_list": bucketed
        }


class SavedLandmark(db.Model): 
    __tablename__ = 'saved_landmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    landmark_id = db.Column(db.Integer, db.ForeignKey("landmarks.id"), nullable=False)
    is_bucket_list = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<SavedLandmark id={self.id} user_id={self.user_id} landmark_id={self.landmark_id} bucket={self.is_bucket_list}>"


class LandmarkCategory(db.Model): 
    __tablename__ = 'landmark_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    def __repr__(self):
        return f"<LandmarkCategory id={self.id} name='{self.name}'>"


def connect_to_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///landmarkr'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.app_context().push()
    db.app = app
    db.init_app(app)
