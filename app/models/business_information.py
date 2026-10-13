
from app import db


class BusinessInformation(db.Model):
    __tablename__ = "business_information"

    # Business Information ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Owner / User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        backref="business_information",
        lazy=True
    )

    # Business Profile
    business_name = db.Column(
        db.String(150),
        nullable=False
    )

    owner_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120)
    )

    phone = db.Column(
        db.String(20)
    )

    address = db.Column(
        db.Text
    )

    business_type = db.Column(
        db.String(100)
    )

    description = db.Column(
        db.Text
    )

    # Created Date
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # AI Assistant Greeting
    greeting_message = db.Column(
        db.Text,
        nullable=True
    )

    # AI Assistant Introduction
    assistant_introduction = db.Column(
        db.Text,
        nullable=True
    )

    # AI Assistant Response Style
    response_style = db.Column(
        db.String(20),
        nullable=False,
        default="friendly",
        server_default="friendly"
    )

    # AI Assistant Preferred Language
    preferred_language = db.Column(
        db.String(10),
        nullable=False,
        default="auto",
        server_default="auto"
    )

    # Gemini Live Voice Selection
    voice_name = db.Column(
        db.String(40),
        nullable=False,
        default="Kore",
        server_default="Kore"
    )
