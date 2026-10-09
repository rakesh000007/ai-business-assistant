from app import db
from datetime import datetime


class Property(db.Model):
    __tablename__ = "properties"

    # ==========================
    # Property ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # OWNER / USER
    # Each property belongs to
    # the user who created it.
    # ==========================
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # ==========================
    # Property Information
    # ==========================
    property_id = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    title = db.Column(
        db.String(120),
        nullable=False
    )

    property_type = db.Column(
        db.Enum(
            "Apartment",
            "Villa",
            "House",
            "Plot",
            "Commercial",
            name="property_type_enum"
        ),
        nullable=False
    )

    city = db.Column(
        db.String(100),
        nullable=False
    )

    area = db.Column(
        db.String(100)
    )

    address = db.Column(
        db.Text
    )

    bedrooms = db.Column(
        db.Integer,
        nullable=True
    )

    bathrooms = db.Column(
        db.Integer,
        nullable=True
    )

    sqft = db.Column(
        db.Integer,
        nullable=True
    )

    price = db.Column(
        db.BigInteger
    )

    # ==========================
    # Property Status
    # ==========================
    status = db.Column(
        db.Enum(
            "Available",
            "Booked",
            "Sold",
            name="property_status_enum"
        ),
        default="Available"
    )

    description = db.Column(
        db.Text
    )

    image = db.Column(
        db.String(255),
        default="default-property.jpg"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ==========================
    # Relationship to User
    # ==========================
    user = db.relationship(
        "User",
        backref="properties",
        lazy=True
    )

    # ==========================
    # Formatted Price
    # ==========================
    @property
    def formatted_price(self):
        """Returns price in Indian number format."""

        if self.price is None:
            return "₹ 0"

        number = str(int(self.price))

        if len(number) <= 3:
            return f"₹ {number}"

        last3 = number[-3:]
        remaining = number[:-3]

        parts = []

        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        if remaining:
            parts.insert(0, remaining)

        return "₹ " + ",".join(parts + [last3])

    # ==========================
    # Short Price
    # ==========================
    @property
    def short_price(self):
        """Returns price in Lakh/Crore format."""

        if self.price is None:
            return "₹ 0"

        if self.price >= 10000000:
            return f"₹ {self.price / 10000000:.2f} Cr"

        if self.price >= 100000:
            return f"₹ {self.price / 100000:.2f} L"

        return self.formatted_price

    # ==========================
    # Representation
    # ==========================
    def __repr__(self):
        return f"<Property {self.title}>"