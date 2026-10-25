
from datetime import date, datetime, time, timedelta
from math import ceil
from types import SimpleNamespace

from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_

from app.models import (
    Customer,
    Conversation,
    CallSession,
    BusinessInformation,
)


call_history_bp = Blueprint(
    "call_history",
    __name__,
    url_prefix="/call-history",
)


def build_pagination(items, page, per_page=10):
    total = len(items)
    pages = ceil(total / per_page) if total else 0
    page = min(page, max(pages, 1))
    start = (page - 1) * per_page

    return SimpleNamespace(
        items=items[start:start + per_page],
        page=page,
        pages=pages,
        total=total,
        has_prev=page > 1,
        has_next=page < pages,
        prev_num=page - 1,
        next_num=page + 1,
        iter_pages=lambda: range(1, pages + 1),
    )


@call_history_bp.route("/")
@login_required
def index():
    user_id = current_user.id

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    start_date_value = request.args.get("start_date", "").strip()
    end_date_value = request.args.get("end_date", "").strip()

    business_ids = [
        row.id
        for row in BusinessInformation.query
        .filter_by(user_id=user_id)
        .all()
    ]

    # Existing customer-linked conversations.
    conversation_query = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(Customer.user_id == user_id)
    )

    # Call sessions, including sessions without a customer.
    session_query = CallSession.query.filter(
        CallSession.business_id.in_(business_ids)
    ) if business_ids else CallSession.query.filter(False)

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
            start_day = end_day = None
            start_date_value = end_date_value = ""

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
        start_day = end_day = None
        start_date_value = end_date_value = ""

    if search:
        pattern = f"%{search}%"
        conversation_query = conversation_query.filter(
            or_(
                Customer.full_name.ilike(pattern),
                Customer.phone.ilike(pattern),
            )
        )

        session_query = session_query.outerjoin(
            Customer,
            CallSession.customer_id == Customer.id,
        ).filter(
            or_(
                Customer.full_name.ilike(pattern),
                Customer.phone.ilike(pattern),
                CallSession.transcript.ilike(pattern),
            )
        )

    if status in ("Active", "Completed", "In Progress"):
        if status == "In Progress":
            conversation_query = conversation_query.filter(False)
            session_query = session_query.filter(
                CallSession.status == "In Progress"
            )
        else:
            conversation_query = conversation_query.filter(
                Conversation.status == status
            )
            session_query = session_query.filter(
                CallSession.status == status
            )
    else:
        status = ""

    if start_day:
        start_at = datetime.combine(start_day, time.min)
        conversation_query = conversation_query.filter(
            Conversation.started_at >= start_at
        )
        session_query = session_query.filter(
            CallSession.started_at >= start_at
        )

    if end_day:
        end_at = datetime.combine(
            end_day + timedelta(days=1), time.min
        )
        conversation_query = conversation_query.filter(
            Conversation.started_at < end_at
        )
        session_query = session_query.filter(
            CallSession.started_at < end_at
        )


       

    sessions = session_query.all()

    linked_conversation_ids = [
        session.conversation_id
        for session in sessions
        if session.conversation_id is not None
    ]

    if linked_conversation_ids:
        conversation_query = conversation_query.filter(
            ~Conversation.id.in_(linked_conversation_ids)
        )

    conversations = conversation_query.all()

    # Overall statistics are not affected by search/date/status filters.
    total_conversations = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(Customer.user_id == user_id)
        .count()
    )

    total_sessions = (
        CallSession.query
        .filter(CallSession.business_id.in_(business_ids))
        .count()
        if business_ids else 0
    )

    completed_conversations = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Customer.user_id == user_id,
            Conversation.status == "Completed",
        )
        .count()
    )

    completed_sessions = (
        CallSession.query
        .filter(
            CallSession.business_id.in_(business_ids),
            CallSession.status == "Completed",
        )
        .count()
        if business_ids else 0
    )

    active_conversations = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Customer.user_id == user_id,
            Conversation.status == "Active",
        )
        .count()
    )

    active_sessions = (
        CallSession.query
        .filter(
            CallSession.business_id.in_(business_ids),
            CallSession.status == "In Progress",
        )
        .count()
        if business_ids else 0
    )

    total_records = total_conversations + total_sessions
    completed_records = completed_conversations + completed_sessions
    active_records = active_conversations + active_sessions

    completion_rate = (
        completed_records / total_records * 100
        if total_records else 0
    )

    # Normalize both models into one table-friendly structure.
    history_items = []

    for conversation in conversations:
        history_items.append({
            "kind": "conversation",
            "id": conversation.id,
            "customer_name": conversation.customer.full_name,
            "customer_phone": conversation.customer.phone,
            "started_at": conversation.started_at,
            "message_count": len(conversation.messages),
            "duration_seconds": None,
            "status": conversation.status,
            "transcript": None,
        })

    for session in sessions:
        history_items.append({
            "kind": "session",
            "id": session.id,
            "customer_name": (
                session.customer.full_name
                if session.customer else "Anonymous"
            ),
            "customer_phone": (
                session.customer.phone
                if session.customer else None
            ),
            "started_at": session.started_at,
            "message_count": None,
            "duration_seconds": session.duration_seconds,
            "status": session.status,
            "transcript": session.transcript,
        })

    history_items.sort(
        key=lambda item: item["started_at"] or datetime.min,
        reverse=True,
    )

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    pagination = build_pagination(history_items, page, 10)
    history_items = pagination.items

    return render_template(
        "call_history/index.html",
        history_items=history_items,
        search=search,
        selected_status=status,
        start_date=start_date_value,
        end_date=end_date_value,
        date_error=date_error,
        pagination=pagination,
        filtered_conversations=len(conversations) + len(sessions),
        total_conversations=total_records,
        completed_conversations=completed_records,
        active_conversations=active_records,
        completion_rate=completion_rate,
    )


@call_history_bp.route("/<int:conversation_id>")
@login_required
def transcript(conversation_id):
    user_id = current_user.id

    conversation = (
        Conversation.query
        .join(Customer, Conversation.customer_id == Customer.id)
        .filter(
            Conversation.id == conversation_id,
            Customer.user_id == user_id,
        )
        .first_or_404()
    )

    messages = sorted(
        conversation.messages,
        key=lambda message: (
            message.created_at is None,
            message.created_at,
        ),
    )

    return render_template(
        "call_history/transcript.html",
        conversation=conversation,
        messages=messages,
    )


@call_history_bp.route("/session/<int:session_id>")
@login_required
def session_transcript(session_id):
    business_ids = [
        row.id
        for row in BusinessInformation.query
        .filter_by(user_id=current_user.id)
        .all()
    ]

    if not business_ids:
        abort(404)

    session = CallSession.query.filter(
        CallSession.id == session_id,
        CallSession.business_id.in_(business_ids),
    ).first_or_404()

    return render_template(
        "call_history/session_transcript.html",
        session=session,
    )
