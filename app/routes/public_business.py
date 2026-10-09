"""Public, login-free business showcase website.

URLs
    /business/<business_id>
    /business/<business_id>/property/<property_id>

Isolation rule (never bypassed):
    business_id -> BusinessInformation -> business.user_id -> Property.user_id
The user_id is NEVER read from the request.
"""
import os
from datetime import datetime

from flask import Blueprint, current_app, render_template, url_for

from app.models.business_information import BusinessInformation
from app.models.property import Property

# Blueprint name is "public_site" (not "business") to avoid clashing with any
# existing CRM blueprint/endpoint names.
public_site_bp = Blueprint("public_site", __name__)

# Where property images may live inside /static (first match wins).
IMAGE_FOLDERS = (
    "uploads/properties",
    "uploads",
    "images/properties",
    "images",
    "img",
    "",
)

# key, label, min (inclusive), max (exclusive, None = open ended) in rupees
BUDGET_BUCKETS = (
    ("under-50l", "Under ₹ 50 L", 0, 5_000_000),
    ("50l-1cr", "₹ 50 L – 1 Cr", 5_000_000, 10_000_000),
    ("1cr-2cr", "₹ 1 Cr – 2 Cr", 10_000_000, 20_000_000),
    ("2cr-plus", "₹ 2 Cr & above", 20_000_000, None),
)


def _available_properties(business):
    """Only AVAILABLE properties owned by this business's user."""
    return Property.query.filter_by(
        user_id=business.user_id,
        status="Available",
    ).order_by(Property.created_at.desc())


@public_site_bp.app_template_global("property_image_url")
def property_image_url(prop):
    """Return a usable image URL, or None so the template shows a placeholder."""
    name = (getattr(prop, "image", None) or "").strip()
    if not name or name == "default-property.jpg":
        return None
    if name.startswith(("http://", "https://")):
        return name

    name = name.lstrip("/")
    if name.startswith("static/"):
        name = name[len("static/"):]
    if ".." in name.replace("\\", "/").split("/"):
        return None

    static_root = current_app.static_folder
    candidates = [name] + [
        f"{folder}/{os.path.basename(name)}" if folder else os.path.basename(name)
        for folder in IMAGE_FOLDERS
    ]
    for rel in candidates:
        if os.path.isfile(os.path.join(static_root, rel)):
            return url_for("static", filename=rel)
    return None


@public_site_bp.route("/business/<int:business_id>")
def home(business_id):
    business = BusinessInformation.query.get_or_404(business_id)
    properties = _available_properties(business).all()

    cities = sorted({p.city.strip() for p in properties if p.city})
    types = sorted({p.property_type for p in properties if p.property_type})
    areas = sorted({p.area.strip() for p in properties if p.area})
    max_beds = max((p.bedrooms or 0 for p in properties), default=0)

    budget_options = []
    for key, label, low, high in BUDGET_BUCKETS:
        has_match = any(
            p.price is not None and p.price >= low and (high is None or p.price < high)
            for p in properties
        )
        if has_match:
            budget_options.append(
                {"key": key, "label": label, "min": low, "max": high}
            )

    stats = {
        "properties": len(properties),
        "types": len(types),
        "cities": len(cities),
    }

    return render_template(
        "business/public_business.html",
        business=business,
        properties=properties,
        stats=stats,
        cities=cities,
        types=types,
        areas=areas,
        bed_options=list(range(1, min(max_beds, 5) + 1)),
        budget_options=budget_options,
        featured=properties[0] if properties else None,
        current_year=datetime.utcnow().year,
    )


@public_site_bp.route("/business/<int:business_id>/property/<int:property_id>")
def property_detail(business_id, property_id):
    business = BusinessInformation.query.get_or_404(business_id)

    prop = Property.query.filter_by(
        id=property_id,
        user_id=business.user_id,
        status="Available",
    ).first_or_404()

    others = _available_properties(business).filter(Property.id != prop.id).limit(12).all()
    others.sort(key=lambda p: (p.city or "").lower() != (prop.city or "").lower())

    return render_template(
        "business/property_detail.html",
        business=business,
        property=prop,
        related=others[:3],
        current_year=datetime.utcnow().year,
    )
