from app import db


class Lead(db.Model):
    __tablename__ = "leads"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # OWNER / USER
    # ==========================

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # ==========================
    # Relationship with User
    # ==========================

    user = db.relationship(
        "User",
        backref="leads",
        lazy=True
    )

    # ==========================
    # Relationship with Customer
    # ==========================

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False
    )

    customer = db.relationship(
        "Customer",
        back_populates="leads"
    )

    # ==========================
    # Lead Details
    # ==========================

    property_type = db.Column(
        db.String(50),
        nullable=False
    )

    budget = db.Column(
        db.Integer
    )

    preferred_city = db.Column(
        db.String(100)
    )

    bedrooms = db.Column(
        db.Integer
    )

    # ==========================
    # Purpose
    # ==========================

    purpose = db.Column(
        db.Enum(
            "Buy",
            "Rent",
            "Lease"
        ),
        default="Buy"
    )

    # ==========================
    # Priority
    # ==========================

    priority = db.Column(
        db.Enum(
            "Low",
            "Medium",
            "High"
        ),
        default="Medium"
    )

    # ==========================
    # AI Lead Score
    # ==========================

    ai_score = db.Column(
        db.Integer,
        default=0
    )
    # ==========================
    # AI Lead Summary
    # ==========================

    ai_summary = db.Column(
      db.Text,
      nullable=True
    )

    # ==========================
    # Lead Status
    # ==========================

    status = db.Column(
        db.Enum(
            "New Lead",
            "Qualified",
            "Property Shared",
            "Site Visit Scheduled",
            "Negotiation",
            "Closed Won",
            "Closed Lost"
        ),
        default="New Lead"
    )

    follow_up_date = db.Column(
        db.Date
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

 