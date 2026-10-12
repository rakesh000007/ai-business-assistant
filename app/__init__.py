from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_mail import Mail
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.models import (
        User,
        BusinessInformation,
        Property,
        Customer,
        CustomerRequirement,
        Conversation,
        ConversationMessage,
        FAQ,
    )
    print("Before importing auth blueprint")

    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.customer import customer_bp
    from app.routes.property import property_bp
    from app.routes.lead import lead_bp
    from app.routes.ai import ai_bp
    from app.routes.profile import profile_bp
    from app.routes.public_business import public_site_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(property_bp)

   
    print("Imported auth blueprint")

    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(customer_bp)
    app.register_blueprint(lead_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(public_site_bp)
    app.register_blueprint(reports_bp)
    
    print("Registered auth blueprint")

    # Register Blueprints here (we'll add them next)

    @app.route("/")
    def home():
        return """
        <h1>🤖 AI Business Assistant</h1>
        <h2>Capstone Project</h2>
        <p>Project Started Successfully!</p>
        """


    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        from app.models import Customer, Property, Conversation

        notifications = []

        if not current_user.is_authenticated:
            return {
                "header_notifications": [],
                "header_notification_count": 0,
            }

        user_id = current_user.id

        # Recent customers
        customers = (
            Customer.query
            .filter_by(user_id=user_id)
            .order_by(Customer.created_at.desc())
            .limit(5)
            .all()
        )

        for customer in customers:
            notifications.append({
                "title": customer.full_name,
                "message": "New customer registered",
                "icon": "bi-person-fill",
                "color": "text-purple",
                "timestamp": customer.created_at,
            })

        # Recent properties
        properties = (
            Property.query
            .filter_by(user_id=user_id)
            .order_by(Property.created_at.desc())
            .limit(5)
            .all()
        )

        for property_item in properties:
            notifications.append({
                "title": property_item.title,
                "message": "Property added",
                "icon": "bi-house-fill",
                "color": "text-cyan",
                "timestamp": property_item.created_at,
            })

        # Recent completed AI conversations
        conversations = (
            Conversation.query
            .join(Customer, Conversation.customer_id == Customer.id)
            .filter(
                Customer.user_id == user_id,
                Conversation.status == "Completed",
            )
            .order_by(Conversation.ended_at.desc())
            .limit(5)
            .all()
        )

        for conversation in conversations:
            notifications.append({
                "title": conversation.customer.full_name,
                "message": "AI conversation completed",
                "icon": "bi-robot",
                "color": "text-amber",
                "timestamp": (
                    conversation.ended_at or conversation.started_at
                ),
            })

        # Latest five events
        notifications.sort(
            key=lambda item: item["timestamp"] or datetime.min,
            reverse=True,
        )
        notifications = notifications[:5]

        return {
            "header_notifications": notifications,
            "header_notification_count": len(notifications),
        }

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))


