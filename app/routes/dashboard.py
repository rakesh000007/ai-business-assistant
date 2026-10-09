from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models.customer import Customer
from app.models.property import Property


dashboard = Blueprint(
    "dashboard",
    __name__
)


@dashboard.route("/dashboard")
@login_required
def dashboard_home():

    # ==========================================
    # CURRENT LOGGED-IN USER
    # ==========================================

    user_id = current_user.id


    # ==========================================
    # CUSTOMER COUNT
    # Only this user's customers
    # ==========================================

    total_customers = Customer.query.filter_by(
        user_id=user_id
    ).count()


    # ==========================================
    # PROPERTY COUNT
    # Only this user's properties
    # ==========================================

    total_properties = Property.query.filter_by(
        user_id=user_id
    ).count()


    # ==========================================
    # RECENT CUSTOMERS
    # Only this user's customers
    # ==========================================

    recent_customers = (
        Customer.query
        .filter_by(user_id=user_id)
        .order_by(Customer.created_at.desc())
        .limit(5)
        .all()
    )


    # ==========================================
    # SEND DATA TO DASHBOARD
    # ==========================================

    return render_template(
        "dashboard/dashboard.html",

        total_customers=total_customers,

        total_properties=total_properties,

        recent_customers=recent_customers
    )