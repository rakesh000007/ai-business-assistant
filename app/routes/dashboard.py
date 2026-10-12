from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from sqlalchemy import func, case

from app.models.customer import Customer
from app.models.property import Property
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage

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
        # CUSTOMER ACTIVITY — THIS WEEK
       # ==========================================

    now = datetime.now()

    today_start = datetime.combine(
        now.date(),
        datetime.min.time()
    )

    tomorrow_start = today_start + timedelta(days=1)

    week_start = today_start - timedelta(
        days=now.weekday()
    )

    customers_this_week = (
        Customer.query
        .filter(
            Customer.user_id == user_id,
            Customer.created_at >= week_start,
            Customer.created_at < tomorrow_start
        )
        .count()
    )

        # ==========================================
         # PROPERTY ACTIVITY — TODAY
        # ==========================================

    properties_today = (
        Property.query
        .filter(
            Property.user_id == user_id,
            Property.created_at >= today_start,
            Property.created_at < tomorrow_start
        )
        .count()
    )



    # ==========================================
    # AI CONVERSATIONS
    # Count conversations belonging to this user
    # ==========================================

    total_conversations = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(Customer.user_id == user_id)
        .count()
    )

    completed_conversations = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Customer.user_id == user_id,
            Conversation.status == "Completed"
        )
        .count()
    )

    # ==========================================
    # CONVERSATION COMPLETION RATE
    # ==========================================

    conversation_completion_rate = (
        round(
            (completed_conversations / total_conversations) * 100,
            1
        )
        if total_conversations > 0
        else 0
    )

    



    # ==========================================
    # TODAY'S AI RESPONSES
    # Count AI messages created today
    # for this user's conversations
    # ==========================================

    today_start = datetime.combine(
        datetime.now().date(),
        datetime.min.time()
    )

    tomorrow_start = today_start + timedelta(days=1)

    todays_responses = (
        ConversationMessage.query
        .join(
            Conversation,
            ConversationMessage.conversation_id == Conversation.id
        )
        .join(
            Customer,
            Conversation.customer_id == Customer.id
        )
        .filter(
            Customer.user_id == user_id,
            ConversationMessage.sender == "AI",
            ConversationMessage.created_at >= today_start,
            ConversationMessage.created_at < tomorrow_start
        )
        .count()
    )


    # ==========================================
    # PROPERTY MIX
    # Count each property type for this user
    # ==========================================

    property_mix_rows = (
        Property.query
        .with_entities(
            Property.property_type,
            func.count(Property.id)
        )
        .filter_by(user_id=user_id)
        .group_by(Property.property_type)
        .all()
    )

    property_type_order = [
        "Apartment",
        "Villa",
        "House",
        "Plot",
        "Commercial"
    ]

    property_mix_counts = {
        property_type: 0
        for property_type in property_type_order
    }

    for property_type, count in property_mix_rows:
        property_mix_counts[property_type] = count

    property_mix = [
        {
            "type": property_type,
            "count": property_mix_counts[property_type]
        }
        for property_type in property_type_order
    ]


    # ==========================================
    # PROPERTY MIX CHART GRADIENT
    # ==========================================

    property_colors = {
        "Apartment": "#7c5cfc",
        "Villa": "#a78bfa",
        "House": "#4f46e5",
        "Plot": "#22d3ee",
        "Commercial": "#f5a623"
    }

    total_mix = sum(
        item["count"] for item in property_mix
    )

    gradient_segments = []
    offset = 0.0

    if total_mix > 0:
        for item in property_mix:
            if item["count"] > 0:
                end = (
                    offset
                    + item["count"] / total_mix * 100
                )

                gradient_segments.append(
                    f'{property_colors[item["type"]]} '
                    f'{offset:.2f}% {end:.2f}%'
                )

                offset = end

        property_mix_gradient = (
            "conic-gradient("
            + ", ".join(gradient_segments)
            + ")"
        )
    else:
        property_mix_gradient = (
            "conic-gradient(#374151 0% 100%)"
        )

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
    # RECENT ACTIVITY — REAL DATABASE RECORDS
    # ==========================================

    recent_activity = []

    # Recent customer registrations
    recent_customer_events = (
        Customer.query
        .filter_by(user_id=user_id)
        .order_by(Customer.created_at.desc())
        .limit(5)
        .all()
    )

    for customer in recent_customer_events:
        recent_activity.append({
            "type": "customer",
            "title": customer.full_name,
            "description": "New customer registered",
            "timestamp": customer.created_at,
            "icon": "bi-person-fill",
            "color": "icon-purple"
        })

    # Recent property additions
    recent_property_events = (
        Property.query
        .filter_by(user_id=user_id)
        .order_by(Property.created_at.desc())
        .limit(5)
        .all()
    )

    for property_item in recent_property_events:
        recent_activity.append({
            "type": "property",
            "title": property_item.title,
            "description": "Property added",
            "timestamp": property_item.created_at,
            "icon": "bi-house-fill",
            "color": "icon-indigo"
        })

    # Recent completed AI conversations
    recent_conversation_events = (
        Conversation.query
        .join(
            Customer,
            Conversation.customer_id == Customer.id
        )
        .filter(
            Customer.user_id == user_id,
            Conversation.status == "Completed"
        )
        .order_by(Conversation.ended_at.desc())
        .limit(5)
        .all()
    )

    for conversation in recent_conversation_events:
        recent_activity.append({
            "type": "conversation",
            "title": conversation.customer.full_name,
            "description": "AI conversation completed",
            "timestamp": (
                conversation.ended_at
                or conversation.started_at
            ),
            "icon": "bi-robot",
            "color": "icon-cyan"
        })

    # Show the latest 8 events across all activity types
    recent_activity.sort(
        key=lambda item: item["timestamp"] or datetime.min,
        reverse=True
    )

    recent_activity = recent_activity[:8]



    # ==========================================
    # CUSTOMER GROWTH — LAST 12 MONTHS
    # Current user's customer registrations
    # ==========================================

    customer_growth_rows = (
        Customer.query
        .with_entities(
            func.year(Customer.created_at).label("year"),
            func.month(Customer.created_at).label("month"),
            func.count(Customer.id).label("count")
        )
        .filter(
            Customer.user_id == user_id,
            Customer.created_at >= (
                datetime.now().replace(
                    day=1, hour=0, minute=0,
                    second=0, microsecond=0
                ) - timedelta(days=365)
            )
        )
        .group_by(
            func.year(Customer.created_at),
            func.month(Customer.created_at)
        )
        .all()
    )

    customer_growth_map = {
        (row.year, row.month): row.count
        for row in customer_growth_rows
    }

    now = datetime.now()
    customer_growth = []

    for months_ago in range(11, -1, -1):
        month_index = now.month - 1 - months_ago
        year = now.year + (month_index // 12)
        month = (month_index % 12) + 1

        customer_growth.append({
            "label": datetime(year, month, 1).strftime("%b"),
            "count": customer_growth_map.get(
                (year, month), 0
            )
        })


    # ==========================================
    # CUSTOMER GROWTH — LAST 30 DAYS
    # Daily customer registrations for this user
    # ==========================================

    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=29)

    daily_growth_rows = (
        Customer.query
        .with_entities(
            func.date(Customer.created_at).label("day"),
            func.count(Customer.id).label("count")
        )
        .filter(
            Customer.user_id == user_id,
            Customer.created_at >= datetime.combine(
                thirty_days_ago,
                datetime.min.time()
            ),
            Customer.created_at < datetime.combine(
                today + timedelta(days=1),
                datetime.min.time()
            )
        )
        .group_by(func.date(Customer.created_at))
        .all()
    )

    daily_growth_map = {
        row.day: row.count
        for row in daily_growth_rows
    }

    daily_customer_growth = []

    for days_ago in range(29, -1, -1):
        day = today - timedelta(days=days_ago)

        daily_customer_growth.append({
            "label": day.strftime("%d %b"),
            "count": daily_growth_map.get(day, 0)
        })

    # ==========================================
    # PROPERTY GROWTH — LAST 30 DAYS
    # Daily property registrations for this user
    # ==========================================

    daily_property_rows = (
        Property.query
        .with_entities(
            func.date(Property.created_at).label("day"),
            func.count(Property.id).label("count")
        )
        .filter(
            Property.user_id == user_id,
            Property.created_at >= datetime.combine(
                thirty_days_ago,
                datetime.min.time()
            ),
            Property.created_at < datetime.combine(
                today + timedelta(days=1),
                datetime.min.time()
            )
        )
        .group_by(func.date(Property.created_at))
        .all()
    )

    daily_property_map = {
        row.day: row.count
        for row in daily_property_rows
    }

    daily_property_growth = []

    for days_ago in range(29, -1, -1):
        day = today - timedelta(days=days_ago)

        daily_property_growth.append({
            "label": day.strftime("%d %b"),
            "count": daily_property_map.get(day, 0)
        })

    # ==========================================
    # AI CONVERSATION GROWTH — LAST 30 DAYS
    # Daily conversations for this user
    # ==========================================

    daily_conversation_rows = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .with_entities(
            func.date(Conversation.started_at).label("day"),
            func.count(Conversation.id).label("count")
        )
        .filter(
            Customer.user_id == user_id,
            Conversation.started_at >= datetime.combine(
                thirty_days_ago,
                datetime.min.time()
            ),
            Conversation.started_at < datetime.combine(
                today + timedelta(days=1),
                datetime.min.time()
            )
        )
        .group_by(func.date(Conversation.started_at))
        .all()
    )

    daily_conversation_map = {
        row.day: row.count
        for row in daily_conversation_rows
    }

    daily_conversation_growth = []

    for days_ago in range(29, -1, -1):
        day = today - timedelta(days=days_ago)

        daily_conversation_growth.append({
            "label": day.strftime("%d %b"),
            "count": daily_conversation_map.get(day, 0)
        })


    # ==========================================
    # SEND DATA TO DASHBOARD
    # ==========================================




    return render_template(
        "dashboard/dashboard.html",
        total_customers=total_customers,
        total_properties=total_properties,
        total_conversations=total_conversations,
        completed_conversations=completed_conversations,
        conversation_completion_rate=conversation_completion_rate,
        recent_customers=recent_customers,
        property_mix=property_mix,
        property_mix_gradient=property_mix_gradient,
        customer_growth=customer_growth,
        daily_customer_growth=daily_customer_growth,
        todays_responses=todays_responses,
        customers_this_week=customers_this_week,
        properties_today=properties_today,
        
        recent_activity=recent_activity,
        daily_property_growth=daily_property_growth,
        daily_conversation_growth=daily_conversation_growth,
    )
