
from datetime import date, datetime, time, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import Customer, Conversation


call_history_bp = Blueprint(
    "call_history",
    __name__,
    url_prefix="/call-history"
)


@call_history_bp.route("/")
@login_required
def index():
    user_id = current_user.id

    # Read search and filter values
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    start_date_value = request.args.get("start_date", "").strip()
    end_date_value = request.args.get("end_date", "").strip()

    # Base query: only conversations owned by this user
    base_query = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(Customer.user_id == user_id)
    )

    # Overall statistics (not affected by filters)
    total_conversations = base_query.count()

    completed_conversations = (
        base_query
        .filter(Conversation.status == "Completed")
        .count()
    )

    active_conversations = (
        base_query
        .filter(Conversation.status == "Active")
        .count()
    )

    completion_rate = (
        completed_conversations / total_conversations * 100
        if total_conversations else 0
    )

    # Filtered results
    query = base_query

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(pattern),
                Customer.phone.ilike(pattern)
            )
        )

    if status in ("Active", "Completed"):
        query = query.filter(Conversation.status == status)
    else:
        status = ""

    # Validate date filters
    date_error = None
    start_day = None
    end_day = None

    try:
        if start_date_value:
            start_day = date.fromisoformat(start_date_value)

        if end_date_value:
            end_day = date.fromisoformat(end_date_value)

        if start_day and end_day and start_day > end_day:
            date_error = "Start date cannot be after end date."
            start_day = None
            end_day = None
            start_date_value = ""
            end_date_value = ""

        today = date.today()

        if start_day and start_day > today:
            date_error = "Start date cannot be in the future."
            start_day = None
            start_date_value = ""

        if end_day and end_day > today:
            date_error = "End date cannot be in the future."
            end_day = None
            end_date_value = ""

    except ValueError:
        date_error = "Please enter valid dates."
        start_day = None
        end_day = None
        start_date_value = ""
        end_date_value = ""

    if start_day:
        query = query.filter(
            Conversation.started_at >= datetime.combine(
                start_day, time.min
            )
        )

    if end_day:
        query = query.filter(
            Conversation.started_at < datetime.combine(
                end_day + timedelta(days=1), time.min
            )
        )

    # Number of records matching the filters
    filtered_conversations = query.count()

    # Pagination: show 10 conversations per page
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    pagination = query.order_by(
        Conversation.started_at.desc()
    ).paginate(
        page=page,
        per_page=10,
        error_out=False
    )

    conversations = pagination.items

    return render_template(
        "call_history/index.html",
        conversations=conversations,
        search=search,
        selected_status=status,
        start_date=start_date_value,
        end_date=end_date_value,
        date_error=date_error,
        pagination=pagination,
        filtered_conversations=filtered_conversations,
        total_conversations=total_conversations,
        completed_conversations=completed_conversations,
        active_conversations=active_conversations,
        completion_rate=completion_rate,
    )


@call_history_bp.route("/<int:conversation_id>")
@login_required
def transcript(conversation_id):
    user_id = current_user.id

    # Only allow access to conversations owned by this user
    conversation = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Conversation.id == conversation_id,
            Customer.user_id == user_id
        )
        .first_or_404()
    )

    messages = sorted(
        conversation.messages,
        key=lambda message: (
            message.created_at is None,
            message.created_at
        )
    )

    return render_template(
        "call_history/transcript.html",
        conversation=conversation,
        messages=messages
    )
