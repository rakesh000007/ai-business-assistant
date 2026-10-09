from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from flask_mail import Mail


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

    app.register_blueprint(property_bp)

   
    print("Imported auth blueprint")

    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(customer_bp)
    app.register_blueprint(lead_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(public_site_bp)

    print("Registered auth blueprint")

    # Register Blueprints here (we'll add them next)

    @app.route("/")
    def home():
        return """
        <h1>🤖 AI Business Assistant</h1>
        <h2>Capstone Project</h2>
        <p>Project Started Successfully!</p>
        """

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))