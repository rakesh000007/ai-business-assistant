from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from app import db
from app.models.customer import Customer


customer_bp = Blueprint(
    "customer",
    __name__,
    url_prefix="/customers"
)


# ==========================
# Customer List
# ==========================
@customer_bp.route("/")
@login_required
def customer_list():

    status = request.args.get("status", "all")
    source = request.args.get("source", "all")
    city = request.args.get("city", "all")
    sort = request.args.get("sort", "newest")

    # IMPORTANT:
    # Start with ONLY the logged-in user's customers.
    #
    # This prevents User A from seeing
    # User B's customers.
    query = Customer.query.filter_by(
        user_id=current_user.id
    )

    # ==========================
    # Status Filter
    # ==========================
    if status != "all":
        query = query.filter(
            Customer.status == status
        )

    # ==========================
    # Source Filter
    # ==========================
    if source != "all":
        query = query.filter(
            Customer.source == source
        )

    # ==========================
    # City Filter
    # ==========================
    if city != "all":
        query = query.filter(
            Customer.city == city
        )

    # ==========================
    # Sorting
    # ==========================
    if sort == "newest":

        query = query.order_by(
            Customer.created_at.desc()
        )

    elif sort == "oldest":

        query = query.order_by(
            Customer.created_at.asc()
        )

    elif sort == "name_asc":

        query = query.order_by(
            Customer.full_name.asc()
        )

    elif sort == "name_desc":

        query = query.order_by(
            Customer.full_name.desc()
        )

    # Get only this user's customers
    customers = query.all()

    # ==========================
    # Status Counts
    # ==========================
    #
    # IMPORTANT:
    # Counts must ALSO belong to
    # the logged-in user.
    #
    status_counts = {

        "all": Customer.query.filter_by(
            user_id=current_user.id
        ).count(),

        "New Lead": Customer.query.filter_by(
            user_id=current_user.id,
            status="New Lead"
        ).count(),

        "Contacted": Customer.query.filter_by(
            user_id=current_user.id,
            status="Contacted"
        ).count(),

        "Site Visit Scheduled": Customer.query.filter_by(
            user_id=current_user.id,
            status="Site Visit Scheduled"
        ).count(),

        "Negotiation": Customer.query.filter_by(
            user_id=current_user.id,
            status="Negotiation"
        ).count(),

        "Closed": Customer.query.filter_by(
            user_id=current_user.id,
            status="Closed"
        ).count(),

        "Lost": Customer.query.filter_by(
            user_id=current_user.id,
            status="Lost"
        ).count(),
    }

    # ==========================
    # Customer Sources
    # ==========================

    sources = [
        "Website",
        "Phone Call",
        "WhatsApp",
        "Walk-in",
        "Facebook",
        "Instagram",
        "Referral"
    ]

    # ==========================
    # Cities
    # ==========================
    #
    # Only show cities belonging
    # to the logged-in user.
    #
    cities = (
        db.session.query(Customer.city)
        .filter(
            Customer.user_id == current_user.id
        )
        .distinct()
        .order_by(Customer.city)
        .all()
    )

    cities = [
        city[0]
        for city in cities
        if city[0]
    ]

    # ==========================
    # Render Customer List
    # ==========================

    return render_template(
        "customer/customer_list.html",

        customers=customers,

        status_counts=status_counts,

        sources=sources,

        cities=cities,

        status=status,

        source=source,

        city=city,

        sort=sort
    )


# ==========================
# Add Customer
# ==========================
@customer_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
def add_customer():

    if request.method == "POST":

        # ==========================
        # Create Customer
        # ==========================
        #
        # IMPORTANT:
        # We automatically assign the
        # logged-in user as the owner.
        #
        customer = Customer(

            user_id=current_user.id,

            full_name=request.form["full_name"],

            phone=request.form["phone"],

            email=request.form["email"],

            city=request.form["city"],

            source=request.form["source"],

            status="New Lead"
        )

        db.session.add(customer)

        db.session.commit()

        flash(
            "Customer added successfully!",
            "success"
        )

        return redirect(
            url_for("customer.customer_list")
        )

    return render_template(
        "customer/add_customer.html"
    )


# ==========================
# Edit Customer
# ==========================
@customer_bp.route(
    "/edit/<int:customer_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_customer(customer_id):

    # ==========================
    # IMPORTANT SECURITY CHECK
    # ==========================
    #
    # Find the customer ONLY if
    # it belongs to the logged-in user.
    #
    customer = Customer.query.filter_by(
        id=customer_id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        customer.full_name = request.form[
            "full_name"
        ]

        customer.phone = request.form[
            "phone"
        ]

        customer.email = request.form[
            "email"
        ]

        customer.city = request.form[
            "city"
        ]

        customer.source = request.form[
            "source"
        ]

        customer.status = request.form[
            "status"
        ]

        db.session.commit()

        flash(
            "Customer updated successfully!",
            "success"
        )

        return redirect(
            url_for("customer.customer_list")
        )

    return render_template(
        "customer/edit_customer.html",
        customer=customer
    )


# ==========================
# Delete Customer
# ==========================
@customer_bp.route(
    "/delete/<int:customer_id>",
    methods=["POST"]
)
@login_required
def delete_customer(customer_id):

    # ==========================
    # IMPORTANT SECURITY CHECK
    # ==========================
    #
    # User can delete ONLY their
    # own customer.
    #
    customer = Customer.query.filter_by(
        id=customer_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(customer)

    db.session.commit()

    flash(
        "Customer deleted successfully!",
        "success"
    )

    return redirect(
        url_for("customer.customer_list")
    )