from app import db


class ConversationMessage(db.Model):
    __tablename__ = "conversation_messages"

    # ==========================
    # Message ID
    # ==========================
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # Conversation
    # ==========================
    #
    # Every message belongs to
    # one conversation.
    #
    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey("conversations.id"),
        nullable=False
    )

    # ==========================
    # Message Sender
    # ==========================
    #
    # Customer = customer message
    # AI       = AI response
    #
    sender = db.Column(
        db.Enum(
            "Customer",
            "AI"
        ),
        nullable=False
    )

    # ==========================
    # Message Content
    # ==========================
    message = db.Column(
        db.Text,
        nullable=False
    )

    # ==========================
    # Message Created Time
    # ==========================
    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )