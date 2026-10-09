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
from app.models.lead import Lead
from app.models.customer import Customer
from app.ai.summary import generate_lead_summary

lead_bp = Blueprint(
    "lead",
    __name__,
    url_prefix="/leads"
)


# ============================================================
# Lead List
# ============================================================
@lead_bp.route("/")
@login_required
def lead_list():

    status = request.args.get("status", "all")
    priority = request.args.get("priority", "all")
    city = request.args.get("city", "all")
    sort = request.args.get("sort", "newest")

    # ========================================================
    # IMPORTANT:
    # Get ONLY leads whose customer belongs
    # to the currently logged-in user.
    # ========================================================

    query = Lead.query.filter(
       Lead.user_id == current_user.id
    )

    # ========================================================
    # Status Filter
    # ========================================================

    if status != "all":

        query = query.filter(
            Lead.status == status
        )

    # ========================================================
    # Priority Filter
    # ========================================================

    if priority != "all":

        query = query.filter(
            Lead.priority == priority
        )

    # ========================================================
    # City Filter
    # ========================================================

    if city != "all":

        query = query.filter(
            Lead.preferred_city == city
        )

    # ========================================================
    # Sorting
    # ========================================================

    if sort == "newest":

        query = query.order_by(
            Lead.created_at.desc()
        )

    elif sort == "oldest":

        query = query.order_by(
            Lead.created_at.asc()
        )

    elif sort == "name_asc":

        query = query.order_by(
            Customer.full_name.asc()
        )

    elif sort == "name_desc":

        query = query.order_by(
            Customer.full_name.desc()
        )

    elif sort == "budget_low":

        query = query.order_by(
            Lead.budget.asc()
        )

    elif sort == "budget_high":

        query = query.order_by(
            Lead.budget.desc()
        )

    # ========================================================
    # Get Leads
    # ========================================================

    leads = query.all()


    # ========================================================
    # Status Counts
    # ONLY CURRENT USER'S LEADS
    # ========================================================

    user_leads = Lead.query.filter(
       Lead.user_id == current_user.id  
    )

    status_counts = {

       "all": user_leads.count(),

       "New Lead": user_leads.filter(
           Lead.status == "New Lead"
       ).count(),

       "Qualified": user_leads.filter(
          Lead.status == "Qualified"
        ).count(),

       "Property Shared": user_leads.filter(
           Lead.status == "Property Shared"
        ).count(),

       "Site Visit Scheduled": user_leads.filter(
          Lead.status == "Site Visit Scheduled"
        ).count(),

        "Negotiation": user_leads.filter(
           Lead.status == "Negotiation"
        ).count(),

        "Closed Won": user_leads.filter(
           Lead.status == "Closed Won"
        ).count(),

        "Closed Lost": user_leads.filter(
           Lead.status == "Closed Lost"
        ).count()
    }

    # ========================================================
    # Cities
    # ONLY CURRENT USER'S LEADS
    # ========================================================

    cities = (
        db.session.query(
            Lead.preferred_city
        )
        
        .filter(
            Lead.user_id == current_user.id
        )
        .distinct()
        .order_by(
            Lead.preferred_city
        )
        .all()
    )

    cities = [
        c[0]
        for c in cities
        if c[0]
    ]


    # ========================================================
    # Dashboard Statistics
    # ONLY CURRENT USER'S LEADS
    # ========================================================

    user_leads = Lead.query.filter(
        Lead.user_id == current_user.id
    )

    dashboard = {

        "total": user_leads.count(),

        "new": user_leads.filter(
            Lead.status == "New Lead"
        ).count(),

        "qualified": user_leads.filter(
            Lead.status == "Qualified"
        ).count(),

        "closed": user_leads.filter(
            Lead.status == "Closed Won"
        ).count()
    }


    # ========================================================
    # Render
    # ========================================================

    return render_template(
        "lead/lead_list.html",

        leads=leads,

        dashboard=dashboard,

        status=status,

        priority=priority,

        city=city,

        sort=sort,

        status_counts=status_counts,

        cities=cities
    )


# ============================================================
# Add Lead
# ============================================================
@lead_bp.route(
    "/add",
    methods=["GET", "POST"]
)
@login_required
def add_lead():

    # IMPORTANT:
    # Show ONLY customers belonging to
    # the logged-in user.

    customers = (
        Customer.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Customer.full_name
        )
        .all()
    )


    if request.method == "POST":

        # ====================================================
        # SECURITY CHECK
        # Make sure selected customer belongs
        # to current user.
        # ====================================================

        customer = Customer.query.filter_by(
            id=request.form["customer_id"],
            user_id=current_user.id
        ).first()

        if not customer:

            flash(
                "Invalid customer selected.",
                "danger"
            )

            return redirect(
                url_for("lead.add_lead")
            )


        lead = Lead(
            user_id=current_user.id,
            customer_id=customer.id,

            property_type=request.form[
                "property_type"
            ],

            budget=(
                int(request.form["budget"])
                if request.form["budget"]
                else None
            ),

            preferred_city=request.form[
                "preferred_city"
            ],

            bedrooms=(
                int(request.form["bedrooms"])
                if request.form["bedrooms"]
                else None
            ),

            purpose=request.form[
                "purpose"
            ],

            priority=request.form[
                "priority"
            ],

            status="New Lead",

            follow_up_date=(
                request.form["follow_up_date"]
                if request.form["follow_up_date"]
                else None
            ),

            notes=request.form[
                "notes"
            ]
        )


        db.session.add(lead)

        db.session.commit()

        flash(
            "Lead added successfully!",
            "success"
        )

        return redirect(
            url_for("lead.lead_list")
        )


    return render_template(
        "lead/add_lead.html",
        customers=customers
    )


# ============================================================
# View Lead
# ============================================================
@lead_bp.route(
    "/view/<int:lead_id>"
)
@login_required
def view_lead(lead_id):

    # Only allow viewing a lead whose
    # customer belongs to current user.

    lead = (
        Lead.query
        .join(Customer)
        .filter(
            Lead.id == lead_id,
            Customer.user_id == current_user.id
        )
        .first_or_404()
    )

    
    return render_template(
       "lead/lead_detail.html",
        lead=lead
    )
# ============================================================
# Edit Lead
# ============================================================
@lead_bp.route(
    "/edit/<int:lead_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_lead(lead_id):

    # Only current user's lead

    lead = (
        Lead.query
        .join(Customer)
        .filter(
            Lead.id == lead_id,
            Customer.user_id == current_user.id
        )
        .first_or_404()
    )


    # Only current user's customers

    customers = (
        Customer.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Customer.full_name
        )
        .all()
    )


    if request.method == "POST":

        # ====================================================
        # SECURITY CHECK FOR NEW CUSTOMER
        # ====================================================

        customer = Customer.query.filter_by(
            id=request.form["customer_id"],
            user_id=current_user.id
        ).first()

        if not customer:

            flash(
                "Invalid customer selected.",
                "danger"
            )

            return redirect(
                url_for(
                    "lead.edit_lead",
                    lead_id=lead_id
                )
            )


        # ====================================================
        # Update Lead
        # ====================================================

        budget = request.form.get(
            "budget"
        )

        bedrooms = request.form.get(
            "bedrooms"
        )

        follow_up_date = request.form.get(
            "follow_up_date"
        )


        lead.customer_id = customer.id

        lead.property_type = request.form[
            "property_type"
        ]

        lead.budget = (
            int(budget)
            if budget
            else None
        )

        lead.preferred_city = request.form[
            "preferred_city"
        ]

        lead.bedrooms = (
            int(bedrooms)
            if bedrooms
            else None
        )

        lead.purpose = request.form[
            "purpose"
        ]

        lead.priority = request.form[
            "priority"
        ]

        lead.status = request.form[
            "status"
        ]

        lead.follow_up_date = (
            follow_up_date
            if follow_up_date
            else None
        )

        lead.notes = request.form[
            "notes"
        ]


        db.session.commit()

        flash(
            "Lead updated successfully!",
            "success"
        )

        return redirect(
            url_for("lead.lead_list")
        )


    return render_template(
        "lead/edit_lead.html",

        lead=lead,

        customers=customers
    )


# ============================================================
# Delete Lead
# ============================================================
@lead_bp.route(
    "/delete/<int:lead_id>",
    methods=["POST"]
)
@login_required
def delete_lead(lead_id):

    # Only current user's lead

    lead = (
        Lead.query
        .join(Customer)
        .filter(
            Lead.id == lead_id,
            Customer.user_id == current_user.id
        )
        .first_or_404()
    )


    db.session.delete(lead)

    db.session.commit()

    flash(
        "Lead deleted successfully!",
        "success"
    )

    return redirect(
        url_for("lead.lead_list")
    )

# ============================================================
# Regenerate AI Lead Summary
# ============================================================
@lead_bp.route(
    "/regenerate-summary/<int:lead_id>",
    methods=["POST"]
)
@login_required
def regenerate_summary(lead_id):

    # Only allow the logged-in business user
    # to regenerate their own lead summary.

    lead = (
        Lead.query
        .join(Customer)
        .filter(
            Lead.id == lead_id,
            Customer.user_id == current_user.id
        )
        .first_or_404()
    )

    # Generate a fresh AI summary
    new_summary = generate_lead_summary(
        lead.notes
    )

    # Save the new summary
    lead.ai_summary = new_summary

    db.session.commit()

    return redirect(
        url_for(
            "lead.view_lead",
            lead_id=lead.id
        )
    )
 


