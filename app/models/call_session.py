
from app import db


class CallSession(db.Model):
    __tablename__ = "call_sessions"

    id = db.Column(db.Integer, primary_key=True)

    # Business receiving the call
    business_id = db.Column(
        db.Integer,
        db.ForeignKey("business_information.id"),
        nullable=False,
        index=True
    )

    # Optional: anonymous callers have no customer ID
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=True,
        index=True
    )

    # Optional link to the existing CRM conversation
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversations.id"),
        nullable=True,
        index=True
    )

    started_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )

    ended_at = db.Column(db.DateTime, nullable=True)

    duration_seconds = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="In Progress",
        server_default="In Progress",
        index=True
    )

    # Optional transcript for calls without a Conversation record
    transcript = db.Column(db.Text, nullable=True)

    business = db.relationship("BusinessInformation")
    customer = db.relationship("Customer")
    conversation = db.relationship("Conversation")
