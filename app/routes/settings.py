
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models.business_information import BusinessInformation

settings_bp = Blueprint(
    "settings",
    __name__,
    url_prefix="/settings"
)

# Supported Gemini Live API voices for the Settings dropdown.
SUPPORTED_VOICES = (
    ("Kore", "Kore — Clear and professional"),
    ("Aoede", "Aoede — Friendly and conversational"),
    ("Zephyr", "Zephyr — Light and upbeat"),
    ("Charon", "Charon — Informative and steady"),
    ("Fenrir", "Fenrir — Strong and energetic"),
    ("Puck", "Puck — Lively and expressive"),
)


@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    business = BusinessInformation.query.filter_by(
        user_id=current_user.id
    ).first()

    if request.method == "POST":
        if business is None:
            flash(
                "Please save your business information first.",
                "warning"
            )
            return redirect(url_for("settings.index"))

        # Save AI assistant greeting, introduction, and voice.
        if any(
            field in request.form
            for field in (
                "greeting_message",
                "assistant_introduction",
                "voice_name"
            )
        ):
            if "greeting_message" in request.form:
                business.greeting_message = request.form.get(
                    "greeting_message", ""
                ).strip()

            if "assistant_introduction" in request.form:
                business.assistant_introduction = request.form.get(
                    "assistant_introduction", ""
                ).strip()

            if "voice_name" in request.form:
                selected_voice = request.form.get(
                    "voice_name", "Kore"
                ).strip()

                allowed_voices = {
                    voice[0] for voice in SUPPORTED_VOICES
                }

                if selected_voice not in allowed_voices:
                    flash(
                        "Invalid voice selection. Please choose a supported voice.",
                        "danger"
                    )
                    return redirect(url_for("settings.index"))

                business.voice_name = selected_voice

            db.session.commit()

            if request.form.get("action") == "test_greeting":
                flash(
                    "Assistant settings saved. Open the AI Assistant to test the selected voice.",
                    "success"
                )
                return redirect(url_for("ai.dashboard"))

            flash(
                "AI assistant greeting, introduction, and voice settings saved successfully!",
                "success"
            )

        # Save response style and preferred language independently.
        elif (
            "response_style" in request.form
            or "preferred_language" in request.form
        ):
            if "response_style" in request.form:
                response_style = request.form.get(
                    "response_style", "friendly"
                ).strip().lower()

                if response_style not in {
                    "friendly", "professional", "concise"
                }:
                    response_style = "friendly"

                business.response_style = response_style

            if "preferred_language" in request.form:
                preferred_language = request.form.get(
                    "preferred_language", "auto"
                ).strip().lower()

                if preferred_language not in {
                    "auto", "en", "te", "hi"
                }:
                    preferred_language = "auto"

                business.preferred_language = preferred_language

            db.session.commit()
            flash(
                "AI assistant preferences saved successfully!",
                "success"
            )

        return redirect(url_for("settings.index"))

    return render_template(
        "settings/index.html",
        business=business,
        supported_voices=SUPPORTED_VOICES
    )
