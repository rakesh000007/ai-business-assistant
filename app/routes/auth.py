print("auth.py loaded")


from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
import os
import secrets
from datetime import datetime, timedelta
from flask_login import login_user, login_required, logout_user
from flask_mail import Message
from app.models import User, BusinessInformation
from app import db, mail

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        business_name = request.form.get("business_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check passwords match
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists.", "danger")
            return redirect(url_for("auth.register"))

        # Create new user
        user = User(
            full_name=full_name,
            email=email
        )

        user.set_password(password)

        db.session.add(user)

        # Automatically create Business Information
        db.session.flush()

        business = BusinessInformation(
            user_id=user.id,
            business_name=business_name,
            owner_name=full_name,
            email=email,
            business_type="Real Estate"
        )

        db.session.add(business)
        db.session.commit()
        flash("Account created successfully! Please login.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            flash("Login successful!", "success")

            return redirect(url_for("dashboard.dashboard_home"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")

@auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not email:
            flash(
                "Please enter your registered email address.",
                "danger"
            )
            return redirect(
                url_for("auth.forgot_password")
            )

        user = User.query.filter_by(
            email=email
        ).first()

        if not user:
            flash(
                "No account found with that email address.",
                "danger"
            )
            return redirect(
                url_for("auth.forgot_password")
            )

        reset_token = secrets.token_urlsafe(32)

        user.reset_token = reset_token

        user.reset_token_expires = (
            datetime.utcnow() + timedelta(minutes=30)
        )

        db.session.commit()

        reset_link = url_for(
            "auth.reset_password",
            token=reset_token,
            _external=True
        )

        message = Message(
            subject="Reset Your AI Business Assistant Password",
            sender=os.getenv("MAIL_USERNAME"),
            recipients=[user.email]
        )

        message.body = f"""
Hello {user.full_name},

We received a request to reset your password for AI Business Assistant.

Click the link below to create a new password:

{reset_link}

This link will expire in 30 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
AI Business Assistant
"""

        mail.send(message)

        flash(
            "Password reset link has been sent to your email.",
            "success"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    return render_template(
        "auth/forgot_password.html"
    )
# ==========================
# Reset Password
# ==========================
@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(
        reset_token=token
    ).first()

    if not user:

        flash(
            "Invalid or expired password reset link.",
            "danger"
        )
        return redirect(
            url_for("auth.forgot_password")
        )

    if (
        not user.reset_token_expires
        or user.reset_token_expires < datetime.utcnow()
    ):
        flash(
            "This password reset link has expired.",
            "danger"
        )
        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password",
            ""
        ).strip()

        if not new_password:
            flash(
                "Please enter a new password.",
                "danger"
            )
            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if len(new_password) < 8:
            flash(
                "Password must be at least 8 characters long.",
                "danger"
            )
            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if new_password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )
            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        user.set_password(new_password)

        user.reset_token = None
        user.reset_token_expires = None

        db.session.commit()

        flash(
            "Password reset successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        token=token
    )
# ==========================
# Logout
# ==========================
@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("auth.login"))



