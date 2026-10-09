from app import db


class CustomerRequirement(db.Model):
    __tablename__ = "customer_requirements"

    # ==========================
    # Requirement ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # Customer
    # ==========================
    #
    # Every requirement belongs
    # to one customer.
    #
    # Customer already belongs
    # to a specific User.
    #
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False
    )

    # ==========================
    # Property Type
    # ==========================
    property_type = db.Column(
        db.Enum(
            "Apartment",
            "Villa",
            "House",
            "Plot",
            "Commercial"
        ),
        nullable=False
    )

    # ==========================
    # Preferred Location
    # ==========================
    preferred_location = db.Column(
        db.String(150)
    )

    # ==========================
    # Budget Range
    # ==========================
    min_budget = db.Column(
        db.Float
    )

    max_budget = db.Column(
        db.Float
    )

    # ==========================
    # Required Bedrooms
    # ==========================
    bedrooms = db.Column(
        db.Integer
    )

    # ==========================
    # Requirement Status
    # ==========================
    status = db.Column(
        db.Enum(
            "New",
            "Contacted",
            "Interested",
            "Site Visit Scheduled",
            "Negotiation",
            "Booked",
            "Closed",
            "Lost"
        ),
        default="New"
    )

    # ==========================
    # Additional Notes
    # ==========================
    notes = db.Column(
        db.Text
    )

    # ==========================
    # Created Date
    # ==========================
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )