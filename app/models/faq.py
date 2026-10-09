from app import db


class FAQ(db.Model):
    __tablename__ = "faqs"

    # ==========================
    # FAQ ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # OWNER / USER
    # ==========================
    #
    # Each FAQ belongs to the
    # logged-in user's business.
    #
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationship to User
    user = db.relationship(
        "User",
        backref="faqs",
        lazy=True
    )

    # ==========================
    # FAQ Question
    # ==========================
    question = db.Column(
        db.Text,
        nullable=False
    )

    # ==========================
    # FAQ Answer
    # ==========================
    answer = db.Column(
        db.Text,
        nullable=False
    )

    # ==========================
    # FAQ Category
    # ==========================
    category = db.Column(
        db.String(100)
    )

    # ==========================
    # Created Date
    # ==========================
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )