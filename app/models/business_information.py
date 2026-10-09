from app import db


class BusinessInformation(db.Model):
    __tablename__ = "business_information"

    # ==========================
    # Business Information ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # OWNER / USER
    # ==========================
    #
    # Each business information
    # record belongs to one user.
    #
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Relationship to User
    user = db.relationship(
        "User",
        backref="business_information",
        lazy=True
    )

    # ==========================
    # Business Name
    # ==========================
    business_name = db.Column(
        db.String(150),
        nullable=False
    )

    # ==========================
    # Owner Name
    # ==========================
    owner_name = db.Column(
        db.String(100),
        nullable=False
    )

    # ==========================
    # Business Email
    # ==========================
    email = db.Column(
        db.String(120)
    )

    # ==========================
    # Business Phone
    # ==========================
    phone = db.Column(
        db.String(20)
    )

    # ==========================
    # Business Address
    # ==========================
    address = db.Column(
        db.Text
    )

    # ==========================
    # Business Type
    # ==========================
    business_type = db.Column(
        db.String(100)
    )

    # ==========================
    # Business Description
    # ==========================
    description = db.Column(
        db.Text
    )

    # ==========================
    # Created Date
    # ==========================
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )