
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Customer, Property, Conversation
from datetime import datetime, date, timedelta

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def report_home():
    user_id = current_user.id

    now = datetime.now()
    today = now.date()
    month_start = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    # Read and validate the selected reporting period.
    period = request.args.get("period", "30days")
    allowed_periods = {"today", "7days", "30days", "month", "custom"}

    if period not in allowed_periods:
        period = "30days"

    if period == "today":
        start_day = today
        end_day = today
    elif period == "7days":
        start_day = today - timedelta(days=6)
        end_day = today
    elif period == "month":
        start_day = today.replace(day=1)
        end_day = today

    elif period == "custom":
        start_value = request.args.get("start_date", "").strip()
        end_value = request.args.get("end_date", "").strip()

        try:
            if not start_value or not end_value:
                raise ValueError("Please select both dates.")

            start_day = date.fromisoformat(start_value)
            end_day = date.fromisoformat(end_value)

            if start_day > end_day:
                raise ValueError("Start date must be before end date.")

            if end_day > today:
                raise ValueError("End date cannot be in the future.")

            if (end_day - start_day).days > 365:
                raise ValueError("Choose a range of 366 days or less.")

        except ValueError:
            period = "30days"
            start_day = today - timedelta(days=29)
            end_day = today

    else:
        start_day = today - timedelta(days=29)
        end_day = today

    start_dt = datetime.combine(start_day, datetime.min.time())
    end_dt = datetime.combine(
        end_day + timedelta(days=1), datetime.min.time()
    )

    period_labels = {
        "today": "Today",
        "7days": "Last 7 Days",
        "30days": "Last 30 Days",
        "month": "This Month",
        "custom": "Custom Date Range",
    }
    period_label = period_labels[period]

    # Overall CRM totals remain independent of the selected period.
    total_customers = Customer.query.filter_by(
        user_id=user_id
    ).count()

    new_customers_this_month = Customer.query.filter(
        Customer.user_id == user_id,
        Customer.created_at >= month_start,
        Customer.created_at <= now
    ).count()

    total_properties = Property.query.filter_by(
        user_id=user_id
    ).count()

    conversations_query = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(Customer.user_id == user_id)
    )

    total_conversations = conversations_query.count()

    completed_conversations = conversations_query.filter(
        Conversation.status == "Completed"
    ).count()

    # Metrics for the selected reporting period.
    period_customers = Customer.query.filter(
        Customer.user_id == user_id,
        Customer.created_at >= start_dt,
        Customer.created_at < end_dt
    ).count()

    period_properties = Property.query.filter(
        Property.user_id == user_id,
        Property.created_at >= start_dt,
        Property.created_at < end_dt
    ).count()

    period_conversations_query = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Customer.user_id == user_id,
            Conversation.started_at >= start_dt,
            Conversation.started_at < end_dt
        )
    )

    period_conversations = period_conversations_query.count()

    period_completed_conversations = (
        period_conversations_query
        .filter(Conversation.status == "Completed")
        .count()
    )

    # Overall property inventory breakdown.
    property_mix = (
        Property.query
        .with_entities(
            Property.property_type,
            func.count(Property.id).label("count")
        )
        .filter_by(user_id=user_id)
        .group_by(Property.property_type)
        .all()
    )

    # Customer registrations grouped by day in the selected period.
    customer_growth_rows = (
        Customer.query
        .with_entities(
            func.date(Customer.created_at).label("day"),
            func.count(Customer.id).label("count")
        )
        .filter(
            Customer.user_id == user_id,
            Customer.created_at >= start_dt,
            Customer.created_at < end_dt
        )
        .group_by(func.date(Customer.created_at))
        .all()
    )

    customer_growth_map = {
        row.day: row.count for row in customer_growth_rows
    }

    customer_growth = []
    current_day = start_day

    while current_day <= end_day:
        customer_growth.append({
            "label": current_day.strftime("%d %b"),
            "count": customer_growth_map.get(current_day, 0)
        })
        current_day += timedelta(days=1)

    # Recent activity within the selected period.
    recent_activity = []

    recent_customers = (
        Customer.query
        .filter(
            Customer.user_id == user_id,
            Customer.created_at >= start_dt,
            Customer.created_at < end_dt
        )
        .order_by(Customer.created_at.desc())
        .limit(5)
        .all()
    )

    for customer in recent_customers:
        recent_activity.append({
            "title": customer.full_name,
            "description": "New customer registered",
            "timestamp": customer.created_at,
            "icon": "bi-person-fill"
        })

    recent_properties = (
        Property.query
        .filter(
            Property.user_id == user_id,
            Property.created_at >= start_dt,
            Property.created_at < end_dt
        )
        .order_by(Property.created_at.desc())
        .limit(5)
        .all()
    )

    for property_item in recent_properties:
        recent_activity.append({
            "title": property_item.title,
            "description": "Property added",
            "timestamp": property_item.created_at,
            "icon": "bi-house-fill"
        })

    recent_conversations = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Customer.user_id == user_id,
            Conversation.status == "Completed",
            Conversation.started_at >= start_dt,
            Conversation.started_at < end_dt
        )
        .order_by(Conversation.started_at.desc())
        .limit(5)
        .all()
    )

    for conversation in recent_conversations:
        recent_activity.append({
            "title": conversation.customer.full_name,
            "description": "AI conversation completed",
            "timestamp": (
                conversation.ended_at or conversation.started_at
            ),
            "icon": "bi-robot"
        })

    recent_activity.sort(
        key=lambda item: item["timestamp"] or datetime.min,
        reverse=True
    )
    recent_activity = recent_activity[:8]

    return render_template(
        "reports/report.html",
        total_customers=total_customers,
        new_customers_this_month=new_customers_this_month,
        total_properties=total_properties,
        total_conversations=total_conversations,
        completed_conversations=completed_conversations,
        property_mix=property_mix,
        customer_growth=customer_growth,
        recent_activity=recent_activity,
        report_generated_at=now,

        # New date-filter variables
        period=period,
        period_label=period_label,
        start_date=start_day.isoformat(),
        end_date=end_day.isoformat(),
        period_customers=period_customers,
        period_properties=period_properties,
        period_conversations=period_conversations,
        period_completed_conversations=period_completed_conversations,
    )
