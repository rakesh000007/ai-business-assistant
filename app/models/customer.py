from app import db


class Customer(db.Model):
    __tablename__ = "customers"

    # ==========================
    # Customer ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # OWNER / USER
    # This tells us which user
    # owns this customer.
    # ==========================
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # ==========================
    # Customer Information
    # ==========================
    full_name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    email = db.Column(
        db.String(120)
    )

    city = db.Column(
        db.String(100)
    )

    # ==========================
    # Customer Source
    # ==========================
    source = db.Column(
        db.Enum(
            "Website",
            "Phone Call",
            "WhatsApp",
            "Walk-in",
            "Facebook",
            "Instagram",
            "Referral"
        ),
        default="Website"
    )

    # ==========================
    # Customer Status
    # ==========================
    status = db.Column(
        db.Enum(
            "New Lead",
            "Contacted",
            "Site Visit Scheduled",
            "Negotiation",
            "Closed",
            "Lost"
        ),
        default="New Lead"
    )

    # ==========================
    # Active / Inactive
    # ==========================
    is_active = db.Column(
        db.Boolean,
        default=True
    )

    # ==========================
    # Created Date
    # ==========================
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # ==========================
    # Relationships
    # ==========================

    requirements = db.relationship(
        "CustomerRequirement",
        backref="customer",
        lazy=True,
        cascade="all, delete-orphan"
    )

    conversations = db.relationship(
        "Conversation",
        backref="customer",
        lazy=True,
        cascade="all, delete-orphan"
    )

    leads = db.relationship(
        "Lead",
        back_populates="customer",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # Relationship to User
    user = db.relationship(
        "User",
        backref="customers",
        lazy=True
    )