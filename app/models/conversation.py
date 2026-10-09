from app import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    # ==========================
    # Conversation ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # Customer
    # ==========================
    #
    # Every conversation belongs
    # to one customer.
    #
    # Customer already belongs
    # to a specific user/business.
    #
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False
    )

    # ==========================
    # Conversation Start Time
    # ==========================
    started_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # ==========================
    # Conversation End Time
    # ==========================
    ended_at = db.Column(
        db.DateTime
    )

    # ==========================
    # Conversation Status
    # ==========================
    status = db.Column(
        db.Enum(
            "Active",
            "Completed"
        ),
        default="Active"
    )

    # ==========================
    # Conversation Messages
    # ==========================
    #
    # One conversation can have
    # multiple messages.
    #
    messages = db.relationship(
        "ConversationMessage",
        backref="conversation",
        lazy=True,
        cascade="all, delete-orphan"
    )