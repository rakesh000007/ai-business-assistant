import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename


profile_bp = Blueprint(
    "profile",
    __name__,
    url_prefix="/profile"
)


@profile_bp.route("/")
@login_required
def profile():

    from app.models import BusinessInformation

    business = BusinessInformation.query.filter_by(
        user_id=current_user.id
    ).first()

    return render_template(
        "profile/profile.html",
        user=current_user,
        business=business
    )


@profile_bp.route("/upload-photo", methods=["POST"])
@login_required
def upload_photo():

    file = request.files.get("profile_picture")

    if not file or file.filename == "":
        flash("Please select a profile picture.", "danger")
        return redirect(url_for("profile.profile"))

    allowed_extensions = {
        "png",
        "jpg",
        "jpeg",
        "webp"
    }

    filename = secure_filename(file.filename)

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        flash(
            "Only PNG, JPG, JPEG and WEBP images are allowed.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    # Create unique filename
    new_filename = (
        f"user_{current_user.id}_"
        f"{uuid.uuid4().hex}.{extension}"
    )

    upload_folder = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "profiles"
    )

    os.makedirs(upload_folder, exist_ok=True)

    # Delete previous uploaded profile picture
    if current_user.profile_picture:

        old_path = os.path.join(
            upload_folder,
            os.path.basename(current_user.profile_picture)
        )

        if os.path.exists(old_path):
            os.remove(old_path)

    # Save new image
    file.save(
        os.path.join(
            upload_folder,
            new_filename
        )
    )

    # Store only filename in database
    current_user.profile_picture = new_filename

    from app import db

    db.session.commit()

    flash(
        "Profile picture updated successfully.",
        "success"
    )

    return redirect(url_for("profile.profile"))

@profile_bp.route("/update-profile", methods=["POST"])
@login_required
def update_profile():

    from app import db
    from app.models import BusinessInformation

    business = BusinessInformation.query.filter_by(
        user_id=current_user.id
    ).first()

    if not business:
        flash(
            "Business information not found.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    current_user.full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    current_user.phone = request.form.get(
        "phone",
        ""
    ).strip()

    business.business_name = request.form.get(
        "business_name",
        ""
    ).strip()

    business.business_type = request.form.get(
        "business_type",
        ""
    ).strip()

    business.owner_name = request.form.get(
        "owner_name",
        ""
    ).strip()

    business.phone = request.form.get(
        "business_phone",
        ""
    ).strip()

    business.email = request.form.get(
        "business_email",
        ""
    ).strip()

    business.address = request.form.get(
        "business_address",
        ""
    ).strip()

    business.description = request.form.get(
        "business_description",
        ""
    ).strip()

    db.session.commit()

    flash(
        "Profile information updated successfully.",
        "success"
    )

    return redirect(url_for("profile.profile"))

@profile_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():

    from app import db

    current_password = request.form.get(
        "current_password",
        ""
    ).strip()

    new_password = request.form.get(
        "new_password",
        ""
    ).strip()

    confirm_password = request.form.get(
        "confirm_password",
        ""
    ).strip()

    if not current_password:
        flash(
            "Please enter your current password.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    if not new_password:
        flash(
            "Please enter a new password.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    if new_password != confirm_password:
        flash(
            "New passwords do not match.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    if not current_user.check_password(current_password):
        flash(
            "Current password is incorrect.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    if current_password == new_password:
        flash(
            "New password must be different from your current password.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    if len(new_password) < 8:
        flash(
            "New password must be at least 8 characters long.",
            "danger"
        )
        return redirect(url_for("profile.profile"))

    current_user.set_password(new_password)

    db.session.commit()

    flash(
        "Password changed successfully.",
        "success"
    )

    return redirect(url_for("profile.profile"))