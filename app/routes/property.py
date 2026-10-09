from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from app import db
from app.models import Property


property_bp = Blueprint(
    "property",
    __name__,
    url_prefix="/properties"
)


# ==========================
# Property List
# ==========================
@property_bp.route("/")
@login_required
def property_list():

    status = request.args.get("status", "all")
    property_type = request.args.get("type", "all")
    city = request.args.get("city", "all")
    price = request.args.get("price", "all")
    sort = request.args.get("sort", "newest")

    print("Selected Price:", price)
    print(request.args)

    # ==========================
    # IMPORTANT:
    # Only get properties owned
    # by the logged-in user.
    # ==========================
    query = Property.query.filter_by(
        user_id=current_user.id
    )

    # ==========================
    # Status Filter
    # ==========================
    if status != "all":
        query = query.filter(
            Property.status == status
        )

    # ==========================
    # Property Type Filter
    # ==========================
    if property_type != "all":
        query = query.filter(
            Property.property_type == property_type
        )

    # ==========================
    # City Filter
    # ==========================
    if city != "all":
        query = query.filter(
            Property.city == city
        )

    # ==========================
    # Price Filter
    # ==========================
    if price == "below10":

        query = query.filter(
            Property.price < 1000000
        )

    elif price == "10to50":

        query = query.filter(
            Property.price >= 1000000,
            Property.price <= 5000000
        )

    elif price == "50to100":

        query = query.filter(
            Property.price > 5000000,
            Property.price <= 10000000
        )

    elif price == "above100":

        query = query.filter(
            Property.price > 10000000
        )

    # ==========================
    # Sorting
    # ==========================
    if sort == "newest":

        query = query.order_by(
            Property.created_at.desc()
        )

    elif sort == "oldest":

        query = query.order_by(
            Property.created_at.asc()
        )

    elif sort == "price_low":

        query = query.order_by(
            Property.price.asc()
        )

    elif sort == "price_high":

        query = query.order_by(
            Property.price.desc()
        )

    elif sort == "name_asc":

        query = query.order_by(
            Property.title.asc()
        )

    elif sort == "name_desc":

        query = query.order_by(
            Property.title.desc()
        )

    # ==========================
    # Get Properties
    # ==========================
    properties = query.all()

    # ==========================
    # Get Unique Cities
    # ONLY for current user
    # ==========================
    cities = (
        db.session.query(Property.city)
        .filter(
            Property.user_id == current_user.id
        )
        .distinct()
        .order_by(Property.city)
        .all()
    )

    city_list = [
        c[0]
        for c in cities
        if c[0]
    ]

    # ==========================
    # Property Counts
    # ONLY for current user
    # ==========================
    property_counts = {

        "all": Property.query.filter_by(
            user_id=current_user.id
        ).count(),

        "Available": Property.query.filter_by(
            user_id=current_user.id,
            status="Available"
        ).count(),

        "Booked": Property.query.filter_by(
            user_id=current_user.id,
            status="Booked"
        ).count(),

        "Sold": Property.query.filter_by(
            user_id=current_user.id,
            status="Sold"
        ).count(),
    }

    return render_template(
        "property/property_list.html",

        properties=properties,

        property_counts=property_counts,

        selected_status=status,

        selected_type=property_type,

        selected_city=city,

        selected_price=price,

        selected_sort=sort,

        city_list=city_list
    )


# ==========================
# Add Property
# ==========================
@property_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
def add_property():

    if request.method == "POST":

        # ==========================
        # Generate Property ID
        # ==========================
        #
        # Keep your existing logic.
        #
        last_property = Property.query.order_by(
            Property.id.desc()
        ).first()

        if last_property:
            next_id = last_property.id + 1
        else:
            next_id = 1

        property_id = f"PROP{next_id:03d}"

        # ==========================
        # Upload Image
        # ==========================

        image = request.files.get("image")

        filename = "default-property.jpg"

        if image and image.filename != "":

            filename = secure_filename(
                image.filename
            )

            upload_path = os.path.join(
                "app",
                "static",
                "images",
                "properties",
                filename
            )

            image.save(upload_path)

        # ==========================
        # Create Property
        # ==========================
        #
        # IMPORTANT:
        # Automatically assign the
        # logged-in user as owner.
        #
        new_property = Property(

            user_id=current_user.id,

            property_id=property_id,

            title=request.form["title"],

            property_type=request.form[
                "property_type"
            ],

            city=request.form["city"],

            area=request.form["area"],

            address=request.form["address"],

            bedrooms=(
                int(request.form["bedrooms"])
                if request.form["bedrooms"]
                else None
            ),

            bathrooms=(
                int(request.form["bathrooms"])
                if request.form["bathrooms"]
                else None
            ),

            sqft=(
                int(request.form["sqft"])
                if request.form["sqft"]
                else None
            ),

            price=request.form["price"],

            status=request.form["status"],

            description=request.form[
                "description"
            ],

            image=filename
        )

        db.session.add(new_property)

        db.session.commit()

        flash(
            "Property added successfully!",
            "success"
        )

        return redirect(
            url_for("property.property_list")
        )

    return render_template(
        "property/add_property.html"
    )


# ==========================
# Edit Property
# ==========================
@property_bp.route(
    "/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_property(id):

    # ==========================
    # IMPORTANT SECURITY CHECK
    # ==========================
    #
    # Only allow the logged-in
    # user to edit their property.
    #
    property = Property.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        property.title = request.form[
            "title"
        ]

        property.property_type = request.form[
            "property_type"
        ]

        property.city = request.form[
            "city"
        ]

        property.area = request.form[
            "area"
        ]

        property.address = request.form[
            "address"
        ]

        property.bedrooms = (
            int(request.form["bedrooms"])
            if request.form["bedrooms"]
            else None
        )

        property.bathrooms = (
            int(request.form["bathrooms"])
            if request.form["bathrooms"]
            else None
        )

        property.sqft = (
            int(request.form["sqft"])
            if request.form["sqft"]
            else None
        )

        property.price = request.form[
            "price"
        ]

        property.status = request.form[
            "status"
        ]

        property.description = request.form[
            "description"
        ]

        # ==========================
        # Update Image
        # ==========================

        image = request.files.get("image")

        if image and image.filename != "":

            filename = secure_filename(
                image.filename
            )

            upload_path = os.path.join(
                "app",
                "static",
                "images",
                "properties",
                filename
            )

            image.save(upload_path)

            property.image = filename

        db.session.commit()

        flash(
            "Property updated successfully!",
            "success"
        )

        return redirect(
            url_for("property.property_list")
        )

    return render_template(
        "property/edit_property.html",
        property=property
    )


# ==========================
# Delete Property
# ==========================
@property_bp.route(
    "/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_property(id):

    # ==========================
    # IMPORTANT SECURITY CHECK
    # ==========================
    #
    # User can delete ONLY their
    # own property.
    #
    property = Property.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    # ==========================
    # Delete Image
    # ==========================

    if property.image:

        image_path = os.path.join(
            "app",
            "static",
            "images",
            "properties",
            property.image
        )

        if os.path.exists(image_path):

            os.remove(image_path)

    db.session.delete(property)

    db.session.commit()

    flash(
        "Property deleted successfully!",
        "success"
    )

    return redirect(
        url_for("property.property_list")
    )