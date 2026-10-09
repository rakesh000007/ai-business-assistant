from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    phone = db.Column(
        db.String(20),
        nullable=True
    )

    password_hash = db.Column(db.String(255), nullable=False)

    reset_token = db.Column(
        db.String(255),
        nullable=True
    )

    reset_token_expires = db.Column(
        db.DateTime,
        nullable=True
    )
    

    profile_picture = db.Column(
        db.String(255),
        nullable=True
    )
    role = db.Column(
        db.Enum("admin", "manager", "sales"),
        default="admin"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)