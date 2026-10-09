import re
import time
import os
import tempfile
import datetime
import asyncio
import json
from threading import Thread
from flask import Blueprint, render_template, request, jsonify, current_app

from flask_login import login_required, current_user

from google import genai
from google.genai import types

from app.ai.lead_scoring import (
    calculate_lead_score,
    calculate_lead_priority
)

from app.ai.summary import generate_lead_summary

from app import db, create_app

from app.ai.ai_service import (
    chat_with_ai,
    generate_property_response
)

from app.ai.lead_analyzer import (
    extract_lead_data,
    extract_name
)

from app.ai.conversation_controller import (
    get_next_action,
    get_action_message
)

from app.ai.recommendation import get_matching_properties

from app.services.whisper_service import transcribe_audio

from app.models import (
    BusinessInformation,
    Customer,
    CustomerRequirement,
    Lead
)

# ==========================================================
# GEMINI LIVE CLIENT
# ==========================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

GEMINI_LIVE_MODEL = (
    "gemini-3.8-live"
)
# ==========================================================
# AI BLUEPRINT
# ==========================================================

ai_bp = Blueprint(
    "ai",
    __name__,
    url_prefix="/ai"
)

# ==========================================================
# DEEPGRAM TEMPORARY TOKEN
# ==========================================================

@ai_bp.route("/api/deepgram-token", methods=["GET"])
def deepgram_token():

    try:

        api_key = os.getenv(
            "DEEPGRAM_API_KEY"
        )

        if not api_key:

            return jsonify({
                "success": False,
                "message": "Deepgram API key is not configured."
            }), 500

        from deepgram import DeepgramClient

        deepgram = DeepgramClient(
            api_key=api_key
        )

        token_response = (
            deepgram.auth.v1.tokens.grant(
                ttl_seconds=30
            )
        )

        return jsonify({
            "success": True,
            "token": token_response.access_token
        })

    except Exception as e:

        print(
            "Deepgram token error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not create Deepgram token."
        }), 500
# ==========================================================
# GEMINI LIVE TEMPORARY TOKEN
# ==========================================================

@ai_bp.route(
    "/api/gemini-live-token",
    methods=["GET"]
)
def gemini_live_token():

    business_id = request.args.get(
        "business_id"
    )

    if not business_id:

        return jsonify({
            "success": False,
            "message": "Business information is missing."
        }), 400

    try:

        business_id = int(
            business_id
        )

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Invalid business information."
        }), 400

    business = BusinessInformation.query.get(
        business_id
    )

    if not business:

        return jsonify({
            "success": False,
            "message": "Business not found."
        }), 404

 
    try:

        now = datetime.datetime.now(
            datetime.timezone.utc
        )

        token = gemini_client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": (
                    now
                    + datetime.timedelta(
                        minutes=30
                    )
                ),
                "new_session_expire_time": (
                    now
                    + datetime.timedelta(
                        minutes=1
                    )
                ),
                
            }
        )

        return jsonify({
            "success": True,
        "token": token.name,
            "business_id": business_id
    })

    except Exception as e:
        print(
            "Gemini Live token error:",
            e
        )

        return jsonify({
            "success": False,
            "message": (
                "Could not create Gemini Live token."
            )
        }), 500
# ==========================================================
# GEMINI LIVE PROPERTY SEARCH
# ==========================================================

@ai_bp.route(
    "/api/gemini-live/search-properties",
    methods=["POST"]
)
def gemini_live_search_properties():

    try:

        data = request.get_json() or {}

        business_id = data.get(
            "business_id"
        )

        city = data.get(
            "city"
        )

        property_type = data.get(
            "property_type"
        )

        bedrooms = data.get(
            "bedrooms"
        )

        budget = data.get(
            "budget"
        )

        excluded_property_ids = data.get(
            "excluded_property_ids",
            []
        )

        if not business_id:

            return jsonify({
                "success": False,
                "message": "Business information is missing."
            }), 400

        business = BusinessInformation.query.get(
            int(business_id)
        )

        if not business:

            return jsonify({
                "success": False,
                "message": "Business not found."
            }), 404

  

        properties = get_matching_properties(
            user_id=business.user_id,
            property_type=property_type,
            city=city,
            budget=budget,
            bedrooms=bedrooms,
            excluded_property_ids=excluded_property_ids
        )

        results = []

        for property in properties:
            results.append({
                "id": property.id,
                "property_id": property.property_id,
                "title": property.title,
                "property_type": property.property_type,
                "city": property.city,
                "address": property.address,
                "bedrooms": property.bedrooms,
                "bathrooms": property.bathrooms,
                "sqft": property.sqft,
                "price": property.price,
                "status": property.status,
                "description": property.description
            })

        return jsonify({
            "success": True,
            "properties": results
        })

    except Exception as e:

        print(
            "Gemini property search error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not search properties."
        }), 500  

@ai_bp.route(
    "/api/gemini-live/save-customer",
    methods=["POST"]
)
def gemini_live_save_customer():
    try:
        data = request.get_json() or {}

        business_id = data.get("business_id")
        full_name = data.get("full_name")
        phone = data.get("phone")
        email = data.get("email")
        city = data.get("city")

        if not business_id:
            return jsonify({
                "success": False,
                "message": "Business information is missing."
            }), 400

        if not full_name or not phone:
            return jsonify({
                "success": False,
                "message": "Customer name and phone number are required."
            }), 400


        business = BusinessInformation.query.get(
            int(business_id)
        )

        if not business:

            return jsonify({
                "success": False,
                "message": "Business not found."
            }), 404

    
        business_user_id = business.user_id
        clean_phone = phone.strip()

        # ------------------------------------------
        # FIND EXISTING CUSTOMER
        # ------------------------------------------

        customer = Customer.query.filter_by(
            user_id=business_user_id,
            phone=clean_phone
        ).first()

        # ------------------------------------------
        # UPDATE EXISTING CUSTOMER
        # ------------------------------------------

        if customer:

            customer.full_name = full_name.strip()

            if email:
                customer.email = email.strip()

            if city:
                customer.city = city.strip()

            customer.status = "New Lead"

            action = "updated"

        # ------------------------------------------
        # CREATE NEW CUSTOMER
        # ------------------------------------------

        else:

            customer = Customer(
                user_id=business_user_id,
                full_name=full_name.strip(),
                phone=clean_phone,
                email=email.strip() if email else None,
                city=city.strip() if city else None,
                source="Website",
                status="New Lead"
            )

            db.session.add(customer)

            action = "created"

        db.session.commit()

        print(
            "GEMINI CUSTOMER:",
            action,
            customer.id,
            customer.full_name,
            customer.phone
        )

        return jsonify({
            "success": True,
            "action": action,
            "customer": {
                "id": customer.id,
                "full_name": customer.full_name,
                "phone": customer.phone,
                "email": customer.email,
                "city": customer.city
            }
        })

    except Exception as e:
        db.session.rollback()

        print(
            "Gemini customer save error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not save customer."
        }), 500
# ==========================================================
# GEMINI LIVE BUSINESS INFORMATION
# ==========================================================

@ai_bp.route(
    "/api/gemini-live/business-information",
    methods=["POST"]
)
def gemini_live_business_information():

    try:

        data = request.get_json() or {}

        business_id = data.get(
            "business_id"
        )

        if not business_id:

            return jsonify({
                "success": False,
                "message": "Business information is missing."
            }), 400

        business = BusinessInformation.query.get(
            int(business_id)
        )

        if not business:

            return jsonify({
                "success": False,
                "message": "Business not found."
            }), 404

        return jsonify({
            "success": True,
            "business": {
                "business_name":
                    business.business_name,

                "owner_name":
                    business.owner_name,

                "email":
                    business.email,

                "phone":
                    business.phone,

                "address":
                    business.address,

                "business_type":
                    business.business_type,

                "description":
                    business.description
            }
        })

    except Exception as e:

        print(
            "Gemini business information error:",
            e
        )

        return jsonify({
            "success": False,
            "message":
                "Could not retrieve business information."
        }), 500
# ==========================================================
# GEMINI LIVE CUSTOMER REQUIREMENT
# ==========================================================

@ai_bp.route(
    "/api/gemini-live/save-customer-requirement",
    methods=["POST"]
)
def gemini_live_save_customer_requirement():

    try:

        data = request.get_json() or {}

        business_id = data.get(
            "business_id"
        )

        phone = data.get(
            "phone"
        )

        property_type = data.get(
            "property_type"
        )

        preferred_location = data.get(
            "preferred_location"
        )

        min_budget = data.get(
            "min_budget"
        )

        max_budget = data.get(
            "max_budget"
        )

        bedrooms = data.get(
            "bedrooms"
        )

        notes = data.get(
            "notes"
        )

        if not business_id:

            return jsonify({
                "success": False,
                "message": "Business information is missing."
            }), 400

        if not phone:

            return jsonify({
                "success": False,
                "message": "Customer phone number is required."
            }), 400

        if not property_type:

            return jsonify({
                "success": False,
                "message": "Property type is required."
            }), 400

        business = BusinessInformation.query.get(
            int(business_id)
        )

        if not business:

            return jsonify({
                "success": False,
                "message": "Business not found."
            }), 404

   

        customer = Customer.query.filter_by(
            user_id=business.user_id,
            phone=phone.strip()
        ).first()

        if not customer:

            return jsonify({
                "success": False,
                "message": "Customer not found."
            }), 404

        requirement = (
            CustomerRequirement.query
            .filter_by(
                customer_id=customer.id
            )
            .order_by(
                CustomerRequirement.id.desc()
            )
            .first()
        )
        if requirement:

            requirement.property_type = property_type
            requirement.preferred_location = preferred_location
            requirement.min_budget = min_budget
            requirement.max_budget = max_budget
            requirement.bedrooms = bedrooms
            requirement.notes = notes

            action = "updated"

        else:

            requirement = CustomerRequirement(
                customer_id=customer.id,
                property_type=property_type,
                preferred_location=preferred_location,
                min_budget=min_budget,
                max_budget=max_budget,
                bedrooms=bedrooms,
                status="New",
                notes=notes
            )

            db.session.add(
                requirement
            )

            action = "created"

        db.session.commit()

        print(
            "GEMINI CUSTOMER REQUIREMENT:",
            action,
            requirement.id,
            customer.full_name,
            requirement.property_type,
            requirement.preferred_location,
            requirement.min_budget,
            requirement.max_budget,
            requirement.bedrooms
        )

        return jsonify({
            "success": True,
            "action": action,
            "requirement": {
                "id": requirement.id,
                "customer_id": requirement.customer_id,
                "property_type": requirement.property_type,
                "preferred_location": requirement.preferred_location,
                "min_budget": requirement.min_budget,
                "max_budget": requirement.max_budget,
                "bedrooms": requirement.bedrooms,
                "status": requirement.status,
                "notes": requirement.notes
            }
        })

    except Exception as e:

        db.session.rollback()

        print(
            "Gemini customer requirement error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not save customer requirement."
        }), 500

    
# ==========================================================
# BACKGROUND - GENERATE LEAD SUMMARY
# ==========================================================

def generate_lead_summary_background(
    app,
    lead_id,
    conversation,
    follow_up_date
):

    with app.app_context():

        try:

            lead = Lead.query.get(
                lead_id
            )

            if not lead:
                print(
                    "Background summary error: Lead not found."
                )
                return

            lead.ai_summary = generate_lead_summary(
                conversation
            )

            if follow_up_date:

                lead.ai_summary = re.sub(
                    r"Follow-up(?: Information)?\s*:\s*.*?(?=$|\n)",
                    "Follow-up: " +
                    follow_up_date.strftime(
                        "%d %B %Y"
                    ),
                    lead.ai_summary,
                    flags=re.IGNORECASE
                )

            db.session.commit()

            print(
                "GEMINI AI SUMMARY:",
                lead.ai_summary
            )

        except Exception as summary_error:

            db.session.rollback()

            print(
                "Gemini AI background summary error:",
                summary_error
            )

        finally:

            db.session.remove()

# ==========================================================
# GEMINI LIVE - CREATE LEAD
# ==========================================================

@ai_bp.route(
    "/api/gemini-live/create-lead",
    methods=["POST"]
)
def gemini_live_create_lead():

    try:
        data = request.get_json() or {}

        business_id = data.get("business_id")
        phone = str(data.get("phone") or "").strip()
        follow_up_date = str(
            data.get("follow_up_date") or ""
        ).strip()
        conversation = str(
            data.get("conversation") or ""
        ).strip()

        if not business_id:
            return jsonify({
                "success": False,
                "message": "Business information is missing."
            }), 400

        if not phone:
            return jsonify({
                "success": False,
                "message": "Customer phone number is required."
            }), 400

        if not conversation:
            return jsonify({
                "success": False,
                "message": "Conversation information is missing."
            }), 400

      
        # --------------------------------------------------
        # PARSE FOLLOW-UP DATE
        # --------------------------------------------------

        parsed_follow_up_date = None

        if follow_up_date:
            try:
                parsed_follow_up_date = (
                    datetime.datetime.strptime(
                        follow_up_date,
                        "%Y-%m-%d"
                    ).date()
                )
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Invalid follow-up date."
                }), 400

        # --------------------------------------------------
        # FIND BUSINESS
        # --------------------------------------------------

        business = BusinessInformation.query.get(
            int(business_id)
        )

        if not business:

            return jsonify({
                "success": False,
                "message": "Business not found."
            }), 404



        business_user_id = business.user_id

        # --------------------------------------------------
        # FIND CUSTOMER
        # --------------------------------------------------

        customer = Customer.query.filter_by(
            user_id=business_user_id,
            phone=phone
        ).first()

        if not customer:
            return jsonify({
                "success": False,
                "message": "Customer not found."
            }), 404

        # --------------------------------------------------
        # FIND CUSTOMER REQUIREMENT
        # --------------------------------------------------

        requirement = (
            CustomerRequirement.query
            .filter_by(
                customer_id=customer.id
            )
            .order_by(
                CustomerRequirement.id.desc()
            )
            .first()
        )

        if not requirement:
            return jsonify({
                "success": False,
                "message": "Customer requirement not found."
            }), 404
        print(
            "GEMINI REQUIREMENT USED FOR LEAD:",
            {
                "requirement_id": requirement.id,
                "customer_id": requirement.customer_id,
                "property_type": requirement.property_type,
                "preferred_location":
                    requirement.preferred_location,
                "max_budget":
                    requirement.max_budget,
                "bedrooms":
                    requirement.bedrooms,
                "status":
                    requirement.status
            }
        )

        # --------------------------------------------------
        # BUILD LEAD DATA
        # --------------------------------------------------

        lead_data = {
            "name": customer.full_name,
            "phone": customer.phone,
            "email": customer.email,

            "property_type":
                requirement.property_type,

            "city":
                requirement.preferred_location,

            "budget":
                requirement.max_budget,

            "bedrooms":
                requirement.bedrooms,

            "purpose":
                "Buy"
        }

        # --------------------------------------------------
        # CHECK EXISTING ACTIVE LEAD
        # --------------------------------------------------

        existing_lead = Lead.query.filter_by(

            user_id=business_user_id,

            customer_id=customer.id,

            property_type=
                lead_data["property_type"],

            preferred_city=
                lead_data["city"],

            bedrooms=
                lead_data["bedrooms"],

            budget=
                lead_data["budget"],

            status="New Lead"

        ).first()
        print(
            "GEMINI LEAD DEBUG:",
            {
                "customer_id": customer.id,
                "lead_data": lead_data,
                "existing_lead_id": (
                    existing_lead.id
                    if existing_lead
                    else None
                ),
                "existing_lead_data": (
                    {
                        "property_type":
                            existing_lead.property_type,
                        "preferred_city":
                            existing_lead.preferred_city,
                        "bedrooms":
                            existing_lead.bedrooms,
                        "budget":
                            existing_lead.budget,
                        "status":
                            existing_lead.status
                    }
                    if existing_lead
                    else None
                )
            }
        )
        # --------------------------------------------------
        # UPDATE EXISTING LEAD
        # --------------------------------------------------

        if existing_lead:

            existing_lead.ai_score = (
                calculate_lead_score(
                    lead_data,
                    customer_interested=True
                )
            )

            existing_lead.priority = (
                calculate_lead_priority(
                    existing_lead.ai_score
                )
            )

            existing_lead.notes = conversation

            existing_lead.follow_up_date = (
                parsed_follow_up_date
            )

            lead = existing_lead
            action = "updated"

        # --------------------------------------------------
        # CREATE NEW LEAD
        # --------------------------------------------------

        else:

            lead = create_lead(
                customer,
                lead_data,
                conversation,
                business_user_id
            )

            if not lead:
                return jsonify({
                    "success": False,
                    "message": "Could not create lead."
                }), 500

            lead.follow_up_date = (
                parsed_follow_up_date
            )

            action = "created"
        # --------------------------------------------------
        # SAVE LEAD
        # --------------------------------------------------

        db.session.commit()


        app = current_app._get_current_object()

        Thread(
            target=generate_lead_summary_background,
            args=(
                app,
                lead.id,
                conversation,
                lead.follow_up_date
            )
        ).start()

        print(
            "GEMINI LIVE LEAD:",
            action,
            lead.id,
            customer.full_name,
            lead.ai_score,
            lead.priority,
            "FOLLOW_UP:",
            lead.follow_up_date
        )


        return jsonify({

            "success": True,

            "action": action,

            "lead": {
                "id": lead.id,
                "customer_id": lead.customer_id,
                "property_type":
                    lead.property_type,
                "budget":
                    lead.budget,
                "preferred_city":
                    lead.preferred_city,
                "bedrooms":
                    lead.bedrooms,
                "purpose":
                    lead.purpose,
                "ai_score":
                    lead.ai_score,
                "priority":
                    lead.priority,
                "status":
                    lead.status,
                "follow_up_date":
                    lead.follow_up_date.isoformat()
                    if lead.follow_up_date
                    else None
            }

        })

    except Exception as e:

        db.session.rollback()

        print(
            "Gemini Live lead creation error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not create lead."
        }), 500
# ==========================================================
# AI DASHBOARD
# ==========================================================

@ai_bp.route("/")
@login_required
def dashboard():

    from app.models import BusinessInformation

    business = BusinessInformation.query.filter_by(
        user_id=current_user.id
    ).first()

    if not business:
        return render_template(
            "ai/dashboard.html",
            business=None
        )

    return render_template(
        "ai/dashboard.html",
        business=business
    )

# ==========================================================
# AI CHAT PAGE
# ==========================================================

@ai_bp.route("/chat/<int:business_id>")
def chat(business_id):

    # Find the business connected to this public AI chat.
    business = BusinessInformation.query.get_or_404(
        business_id
    )

    return render_template(
        "ai/chat.html",
        business=business
    )
@ai_bp.route("/call/<int:business_id>")
def call(business_id):
    business = BusinessInformation.query.get_or_404(
        business_id
    )
    return render_template(
        "ai/call.html",
        business=business
    )
# ==========================================================
# HELPER - FIND OR CREATE CUSTOMER
# ==========================================================

def get_or_create_customer(
    lead_data,
    business_user_id
):
    """
    Find an existing customer using phone number.
    If the customer does not exist, create a new one.

    Customers are always restricted to the
    currently logged-in business user.
    """

    phone = lead_data.get("phone")

    if not phone:
        return None, False

    phone = str(phone).strip()

    if not phone:
        return None, False

    # ------------------------------------------------------
    # Search existing customer
    # ------------------------------------------------------

    customer = Customer.query.filter_by(
        user_id=business_user_id,
        phone=phone
    ).first()

    if customer:

        # Update information if newly provided
        if lead_data.get("name"):
            customer.full_name = lead_data["name"]

        if lead_data.get("email"):
            customer.email = lead_data["email"]

        if lead_data.get("city"):
            customer.city = lead_data["city"]

        db.session.commit()

        return customer, False

    # ------------------------------------------------------
    # Create new customer
    # ------------------------------------------------------

    customer = Customer(
        user_id=business_user_id,
        full_name=lead_data.get("name") or "Unknown Customer",
        phone=phone,
        email=lead_data.get("email"),
        city=lead_data.get("city"),
        source="Website",
        status="New Lead",
        is_active=True
    )

    db.session.add(customer)
    db.session.flush()

    return customer, True


# ==========================================================
# HELPER - CREATE CUSTOMER REQUIREMENT
# ==========================================================

def create_customer_requirement(
    customer,
    lead_data,
    conversation_text
):
    """
    Save the customer's property requirement.
    """

    property_type = lead_data.get("property_type")

    # CustomerRequirement requires property_type
    if not property_type:
        return None

    # ------------------------------------------------------
    # Your CustomerRequirement model allows:
    #
    # Apartment
    # Villa
    # Plot
    # Commercial
    #
    # House is NOT currently allowed by the DB enum.
    # ------------------------------------------------------

    allowed_types = {
       "Apartment",
       "Villa",
       "House",
       "Plot",
       "Commercial"
    }

    if property_type not in allowed_types:
        return None

    requirement = CustomerRequirement(
        customer_id=customer.id,

        property_type=property_type,

        preferred_location=lead_data.get(
            "city"
        ),

        min_budget=None,

        max_budget=lead_data.get(
            "budget"
        ),

        bedrooms=lead_data.get(
            "bedrooms"
        ),

        status="New",

        notes=conversation_text
    )

    db.session.add(requirement)

    return requirement


# ==========================================================
# HELPER - CREATE LEAD
# ==========================================================

def create_lead(
    customer,
    lead_data,
    conversation_text,
    business_user_id
):
    """
    Create a CRM Lead for the customer.
    """

    property_type = lead_data.get(
        "property_type"
    )

    if not property_type:
        return None

    allowed_types = {
        "Apartment",
        "Villa",
        "House",
        "Plot",
        "Commercial"
    }

    if property_type not in allowed_types:
        return None

    # ------------------------------------------------------
    # Calculate AI lead score
    # ------------------------------------------------------

    ai_score = calculate_lead_score(
        lead_data,
        customer_interested=True
    )
    priority = calculate_lead_priority(
        ai_score
    )
        # ------------------------------------------------------
    # AI lead summary
    # ------------------------------------------------------
    # Summary will be generated separately so the
    # customer does not have to wait for the AI call.

    ai_summary = (
        "AI summary will be generated separately."
    )

    lead = Lead(
        user_id=business_user_id,

        customer_id=customer.id,

        property_type=property_type,

        budget=lead_data.get(
            "budget"
        ),

        preferred_city=lead_data.get(
            "city"
        ),

        bedrooms=lead_data.get(
            "bedrooms"
        ),

        purpose=lead_data.get(
            "purpose"
        ) or "Buy",

        priority=priority,

        ai_score=ai_score,

        ai_summary=ai_summary,

        status="New Lead",

        notes=conversation_text
    )

    db.session.add(lead)

    return lead


# ==========================================================
# AI CHAT API
# ==========================================================

@ai_bp.route("/api/chat", methods=["POST"])

def api_chat():
    request_start = time.perf_counter()
    # ------------------------------------------------------
    # STEP 1: Get request data
    # ------------------------------------------------------

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received."
        }), 400
    # ------------------------------------------------------
    # PUBLIC CHAT - BUSINESS IDENTIFICATION
    # ------------------------------------------------------

    business_id = data.get("business_id")

    if not business_id:
        return jsonify({
            "success": False,
            "message": "Business information is missing."
        }), 400

    try:
        business_id = int(business_id)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Invalid business information."
        }), 400

    business = BusinessInformation.query.get(
        business_id
    )

    if not business:
        return jsonify({
            "success": False,
            "message": "Business not found."
        }), 404

    # The properties, customers and leads
    # for this public chat belong to this business owner.

    business_user_id = business.user_id


    

    # ------------------------------------------------------
    # STEP 2: Current customer message
    # ------------------------------------------------------

    message = data.get(
        "message",
        ""
    ).strip()
    

    if not message:
        return jsonify({
            "success": False,
            "message": "Please enter a message."
        }), 400

    # ------------------------------------------------------
    # Previously rejected property IDs
    # ------------------------------------------------------

    rejected_property_ids = data.get(
        "rejected_property_ids",
        []
    )

    if not isinstance(
        rejected_property_ids,
        list
    ):
        rejected_property_ids = []

    # ------------------------------------------------------
    # STEP 3: Previous conversation
    # ------------------------------------------------------

    conversation_history = data.get(
        "conversation_history",
        []
    )

    if not isinstance(
        conversation_history,
        list
    ):
        conversation_history = []

    try:

        # ==================================================
        # STEP 4: BUILD COMPLETE CONVERSATION
        # ==================================================

        conversation_text = ""

        for item in conversation_history:

            if not isinstance(
                item,
                dict
            ):
                continue

            role = item.get(
                "role",
                "user"
            )

            content = item.get(
                "content",
                ""
            )

            if content:

                conversation_text += (
                    f"{role}: {content}\n"
                )

        # Add latest customer message
        conversation_text += (
            f"user: {message}"
        )
        # ==================================================
        # INTEREST STATE
        # ==================================================

        interest_question_asked = any(
           item.get("role") == "assistant"
           and "are you interested" in item.get(
             "content",
             ""
           ).lower()
           for item in conversation_history
           if isinstance(item, dict)
        )
        # ==================================================
        # STEP 4B: BUILD CUSTOMER-ONLY CONVERSATION
        # ==================================================

        customer_conversation_text = ""

        for item in conversation_history:

            if not isinstance(
                item,
                dict
            ):
                continue

            role = item.get(
                "role",
                ""
            )

            content = item.get(
                "content",
                ""
            )

            if role == "user" and content:

                customer_conversation_text += (
                    f"{content}\n"
                )

        # Add latest customer message
        customer_conversation_text += (
            f"{message}"
        )

        # ==================================================
        # STEP 5: EXTRACT LEAD DATA
        # ==================================================

        extract_start = time.perf_counter()

        # --------------------------------------------------
        # Check whether the LAST assistant message asked
        # the customer for their name.
        # --------------------------------------------------

        name_was_requested = False

        if conversation_history:

            for item in reversed(
                conversation_history
            ):

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if item.get(
                    "role",
                    ""
                ) != "assistant":

                    continue

                last_assistant_message = str(
                    item.get(
                        "content",
                        ""
                    )
                ).strip()

                name_was_requested = bool(
                    re.search(
                        r"\b(?:may i have your name|"
                        r"can i have your name|"
                        r"what is your name|"
                        r"what's your name|"
                        r"please provide your name|"
                        r"provide your name)\b",
                        last_assistant_message,
                        flags=re.IGNORECASE
                    )
                )

                break

        print(
            "NAME WAS REQUESTED:",
            name_was_requested
        )

        # --------------------------------------------------
        # Extract lead data from the complete conversation.
        # --------------------------------------------------

        lead_data = extract_lead_data(
            customer_conversation_text,
            name_was_requested=name_was_requested
        )

        # --------------------------------------------------
        # IMPORTANT:
        #
        # Always recover previously collected information
        # from previous user messages.
        #
        # This prevents a later message such as:
        #
        # User: 9123456780
        #
        # from removing:
        #
        # name = Arjun Kumar
        # --------------------------------------------------

        previous_messages = []

        if conversation_history:

            for item in conversation_history:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if item.get(
                    "role",
                    ""
                ) != "user":

                    continue

                previous_messages.append(
                    str(
                        item.get(
                            "content",
                            ""
                        )
                    )
                )

        # --------------------------------------------------
        # Recover previously collected name.
        # --------------------------------------------------

        previous_name = None

        for previous_message in reversed(
            previous_messages
        ):

            extracted_previous_name = extract_name(
                previous_message,
                name_was_requested=False
            )

            if extracted_previous_name:

                previous_name = (
                    extracted_previous_name
                )

                break

        # --------------------------------------------------
        # If the current extraction does not contain a name,
        # restore the previously collected name.
        # --------------------------------------------------

        if (
            not lead_data.get("name")
            and previous_name
        ):

            lead_data["name"] = (
                previous_name
            )

        # --------------------------------------------------
        # Extract the name from the CURRENT message when
        # the assistant has requested it.
        # --------------------------------------------------

        if name_was_requested:

            latest_name = extract_name(
                message,
                name_was_requested=True
            )

            print(
                "LATEST NAME MESSAGE:",
                repr(message)
            )

            print(
                "EXTRACTED NAME:",
                repr(latest_name)
            )

            if latest_name:

                lead_data["name"] = (
                    latest_name
                )

        print(
            "PREVIOUS NAME RECOVERED:",
            repr(previous_name)
        )

        print(
            "FINAL LEAD NAME:",
            repr(
                lead_data.get(
                    "name"
                )
            )
        )

        extract_end = time.perf_counter()

        print(
            f"⏱️ LEAD EXTRACTION TIME: "
            f"{extract_end - extract_start:.2f} seconds"
        )

        print("\n")
        print("=" * 60)
        print("EXTRACTED LEAD DATA")
        print("=" * 60)

        for key, value in lead_data.items():

            print(
                f"{key:<15}: {value}"
            )
        # ==================================================
        # STEP 6: DETERMINE REQUIREMENTS
        # ==================================================

        has_requirements = (
            lead_data.get("property_type") is not None
            and lead_data.get("city") is not None
            and lead_data.get("bedrooms") is not None
            and lead_data.get("budget") is not None
        )

        has_contact_details = bool(
            lead_data.get("phone")
        )

        # ==================================================
        # STEP 7: DETERMINE INTEREST STATE
        # ==================================================
        #
        # The assistant asks about interest only after
        # finding a matching property.
        #
        # We derive the state from the conversation history
        # instead of adding another database field.
        # ==================================================

        interest_question_asked = False
        customer_interested = False
        customer_not_interested = False

        # --------------------------------------------------
        # Check previous assistant messages
        # --------------------------------------------------

        last_interest_question_index = -1

        for index, item in enumerate(conversation_history):

            if not isinstance(
                item,
                dict
            ):
                continue

            role = item.get(
                "role",
                ""
            )

            content = str(
                item.get(
                    "content",
                    ""
                )
            ).lower()

            if role != "assistant":
                continue

            # The assistant previously asked about interest
            if (
                "are you interested" in content
                or "would you like to know more" in content
                or "would you be interested" in content
                or "interested in this property" in content
            ):
                interest_question_asked = True
                last_interest_question_index = index

        # --------------------------------------------------
        # If interest question was already asked,
        # determine whether the customer answered.
        # --------------------------------------------------

        if interest_question_asked:

            normalized_message = (
                message
                .lower()
                .strip()
            )

            # Remove common punctuation
            normalized_message = re.sub(
                r"[^\w\s]",
                "",
                normalized_message
            )

            positive_interest = {
                "yes",
                "yeah",
                "yep",
                "yup",
                "sure",
                "okay",
                "ok",
                "interested",
                "yes interested",
                "i am interested",
                "im interested",
                "i'm interested",
                "definitely",
                "of course",
                "yes i am interested"
            }

            negative_interest = {
                "no",
                "nope",
                "nah",
                "not interested",
                "im not interested",
                "i am not interested",
                "i'm not interested",
                "less interested",
                "not very interested",
                "not really interested",
                "not that interested",
                "no thanks",
                "not for me",
                "i dont want it",
                "i don't want it",
                "i do not want it",
                "i dont like it",
                "i don't like it",
                "i do not like it",
                "i didnt like it",
                "i didn't like it",
                "i dont like this",
                "i don't like this",
                "i do not like this",
                "i didnt like this",
                "i didn't like this",
                "i didnt trust",
                "i didn't trust",
                "i dont trust",
                "i don't trust",
                "i do not trust"
            }

            # --------------------------------------------------
            # Natural negative phrases
            # --------------------------------------------------

            negative_phrases = [
                "not interested",
                "i am not interested",
                "i'm not interested",
                "im not interested",
                "less interested",
                "not very interested",
                "not really interested",
                "not that interested",
                "no thanks",
                "not for me",
                "i dont want it",
                "i don't want it",
                "i do not want it",
                "i dont like it",
                "i don't like it",
                "i do not like it",
                "i didnt like it",
                "i didn't like it",
                "i dont like this",
                "i don't like this",
                "i do not like this",
                "i didnt like this",
                "i didn't like this",
                "i didnt trust",
                "i didn't trust",
                "i dont trust",
                "i don't trust",
                "i do not trust",
                "no i dont",
                "no i don't"
            ]

            # --------------------------------------------------
            # Natural positive phrases
            # --------------------------------------------------

            positive_phrases = [
                "i am interested",
                "i'm interested",
                "im interested",
                "yes i am",
                "yes im",
                "yes i'm",
                "i would like to know more",
                "i'd like to know more",
                "tell me more",
                "i want to know more",
                "i want this property",
                "i like this property"
            ]

            # --------------------------------------------------
            # First check the CURRENT message
            # --------------------------------------------------

            if normalized_message in negative_interest:

                customer_interested = False
                customer_not_interested = True

            elif any(
                phrase in normalized_message
                for phrase in negative_phrases
            ):

                customer_interested = False
                customer_not_interested = True

            elif normalized_message in positive_interest:

                customer_interested = True
                customer_not_interested = False

            elif any(
                phrase in normalized_message
                for phrase in positive_phrases
            ):

                customer_interested = True
                customer_not_interested = False

            # --------------------------------------------------
            # If CURRENT message is not YES/NO,
            # recover the previous YES/NO from conversation
            # history.
            #
            # Example:
            # User: yes
            # AI: May I have your name?
            # User: Rakesh Reddy
            #
            # The current message is a name, so we keep
            # customer_interested = True from the previous YES.
            # --------------------------------------------------

            if (
                normalized_message not in positive_interest
                and normalized_message not in negative_interest
                and not any(
                    phrase in normalized_message
                    for phrase in positive_phrases
                )
                and not any(
                    phrase in normalized_message
                    for phrase in negative_phrases
                )
            ):

                for item in conversation_history[
                    last_interest_question_index + 1:
                ]:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    role = item.get(
                        "role",
                        ""
                    )

                    if role != "user":
                        continue

                    historical_message = str(
                        item.get(
                            "content",
                            ""
                        )
                    ).lower().strip()

                    historical_message = re.sub(
                        r"[^\w\s]",
                        "",
                        historical_message
                    )

                    if historical_message in negative_interest:

                        customer_interested = False
                        customer_not_interested = True
                        break

                    if any(
                        phrase in historical_message
                        for phrase in negative_phrases
                    ):

                        customer_interested = False
                        customer_not_interested = True
                        break

                    if historical_message in positive_interest:

                        customer_interested = True
                        customer_not_interested = False
                        break

                    if any(
                        phrase in historical_message
                        for phrase in positive_phrases
                    ):

                        customer_interested = True
                        customer_not_interested = False
                        break

        print("\n")
        print("=" * 60)
        print("INTEREST STATE")
        print("=" * 60)
        print(
            f"Interest question asked : "
            f"{interest_question_asked}"
        )
        print(
            f"Customer interested     : "
            f"{customer_interested}"
        )
        print(
            f"Customer not interested : "
            f"{customer_not_interested}"
        )
        # ==================================================
        # STEP 8: FIND MATCHING PROPERTIES
        # ==================================================

        print("\n")
        print("=" * 60)
        print("REJECTED PROPERTY IDs RECEIVED")
        print("=" * 60)
        print(rejected_property_ids)
        print("=" * 60)

        properties = []

        if has_requirements:
            property_start = time.perf_counter()
            properties = get_matching_properties(

                user_id=business_user_id,

                property_type=lead_data.get(
                    "property_type"
                ),

                city=lead_data.get(
                    "city"
                ),

                budget=lead_data.get(
                    "budget"
                ),

                bedrooms=lead_data.get(
                    "bedrooms"
                ),

                excluded_property_ids=rejected_property_ids
            )

        # --------------------------------------------------
        # Customer rejected the previously shown property
        # --------------------------------------------------

        if customer_not_interested:

            # The rejected property has already been added
            # to rejected_property_ids by chat.js.
            #
            # Therefore, DO NOT add properties[0] again.
            # Just search using the rejected IDs already received.

            if has_requirements:

                properties = get_matching_properties(

                    user_id=business_user_id,

                    property_type=lead_data.get(
                        "property_type"
                    ),

                    city=lead_data.get(
                        "city"
                    ),

                    budget=lead_data.get(
                        "budget"
                    ),

                    bedrooms=lead_data.get(
                        "bedrooms"
                    ),

                    excluded_property_ids=rejected_property_ids
                )

            else:

                properties = []


        # ==================================================
        # HIDE PROPERTY CARDS AFTER CUSTOMER SHOWS INTEREST
        # ==================================================

        if customer_interested:
             properties = []  

        # --------------------------------------------------
        # Show only ONE property at a time
        # --------------------------------------------------

        if properties:

            properties = [
                properties[0]
            ]   

        # ==================================================
        # STEP 9: PROPERTY DATA FOR FRONTEND
        # ==================================================

        property_data = []

        for p in properties:

            property_data.append({

                "property_id":
                    p.property_id,

                "title":
                    p.title,

                "type":
                    p.property_type,

                "city":
                    p.city,

                "location":
                    p.area,

                "address":
                    p.address,

                "bedrooms":
                    p.bedrooms,

                "bathrooms":
                    p.bathrooms,

                "area": (
                    f"{p.sqft} sq.ft"
                    if p.sqft is not None
                    else None
                ),

                "price":
                    p.short_price,

                "status":
                    p.status,

                "description":
                    p.description
            })

        # ==================================================
        # STEP 10: CUSTOMER / LEAD CREATION
        # ==================================================
        customer_created = False
        lead_created = False
        requirement_created = False

        # --------------------------------------------------
        # VALIDATE PHONE NUMBER BEFORE CREATING CRM DATA
        # --------------------------------------------------

        phone = str(
            lead_data.get("phone") or ""
        ).strip()

        phone_digits = "".join(
            ch for ch in phone
            if ch.isdigit()
        )

        valid_phone = len(phone_digits) == 10

        if valid_phone:
            lead_data["phone"] = phone_digits
        else:
            # Keep the entered number so the response
            # can explain that it is incomplete/invalid.
            lead_data["phone"] = phone_digits or None

        # ==================================================
        # STEP 10B: CONVERSATION CONTROLLER
        # ==================================================

        next_action = get_next_action(
            lead_data=lead_data,
            customer_interested=customer_interested,
            valid_phone=valid_phone
        )

        action_name = next_action.get(
            "action"
        )

        print("\n")
        print("=" * 60)
        print("CONVERSATION CONTROLLER")
        print("=" * 60)
        print(
            f"Next action : {action_name}"
        )
        print(
            f"Missing field : "
            f"{next_action.get('missing_field')}"
        )
        print("=" * 60)
        # --------------------------------------------------
        # IMPORTANT:
        #
        # CRM data is saved ONLY when:
        #
        # 1. Requirements exist
        # 2. Customer is interested
        # 3. Valid 10-digit phone number is available
        # --------------------------------------------------

        if (
            customer_interested
            and valid_phone
            and has_requirements
        ):

            customer, customer_created = (
                get_or_create_customer(
                    lead_data,
                    business_user_id
                )
            )

            if customer:

                # ------------------------------------------
                # Create requirement
                # ------------------------------------------

                requirement = (
                    create_customer_requirement(
                        customer,
                        lead_data,
                        conversation_text
                    )
                )

                if requirement:
                    requirement_created = True

                 # ------------------------------------------
                # Check existing active lead
                #
                # A lead is considered the same only when
                # the main property requirements match.
                #
                # This allows the same customer to have
                # different requirements over time.
                # ------------------------------------------

                existing_lead = Lead.query.filter_by(

                    user_id=business_user_id,

                    customer_id=customer.id,

                    property_type=lead_data.get(
                        "property_type"
                    ),

                    preferred_city=lead_data.get(
                        "city"
                    ),

                    bedrooms=lead_data.get(
                        "bedrooms"
                    ),

                    budget=lead_data.get(
                        "budget"
                    ),

                    status="New Lead"

                ).first()
                
                # ------------------------------------------
                # Create lead if not already present
                # ------------------------------------------

                if existing_lead:

                    # ------------------------------------------
                    # Update AI score for existing lead
                    # ------------------------------------------

                    existing_lead.ai_score = (
                        calculate_lead_score(
                            lead_data,
                            customer_interested=True
                        )
                    )
                    # ------------------------------------------
                    # Update priority from AI score
                    # ------------------------------------------

                    existing_lead.priority = (
                        calculate_lead_priority(
                            existing_lead.ai_score
                        )
                    )

                else:

                    # ------------------------------------------
                    # Create lead if not already present
                    # ------------------------------------------

                    lead = create_lead(
                        customer,
                        lead_data,
                        conversation_text,
                        business_user_id
                    )

                    if lead:
                        lead_created = True        
        # ==================================================
        # STEP 11: SAVE DATABASE CHANGES
        # ==================================================

        db.session.commit()

               # ==================================================
        # STEP 12: GENERATE RESPONSE
        # ==================================================

        response_start = time.perf_counter()

        # --------------------------------------------------
        # DETERMINISTIC RESPONSES
        # --------------------------------------------------
        # Do NOT call the LLM when we already know exactly
        # what information needs to be collected.
        # --------------------------------------------------

        deterministic_actions = {
          "ASK_CITY",
          "ASK_PROPERTY_TYPE",
          "ASK_BEDROOMS",
          "ASK_BUDGET",
          "ASK_NAME",
          "ASK_PHONE"
        }

        if action_name in deterministic_actions:

            ai_response = get_action_message(
                action_name
            )

        # --------------------------------------------------
        # PROPERTY / INTEREST / CRM FLOW
        # --------------------------------------------------

        else:

            if has_requirements:

                ai_response = generate_property_response(
                    conversation_text,
                    properties,
                    customer_interested=customer_interested,
                    interest_question_asked=interest_question_asked,
                    customer_not_interested=customer_not_interested,
                    customer_name=lead_data.get("name"),
                    customer_phone=lead_data.get("phone"),
                    lead_data=lead_data
                )

            else:

                ai_response = chat_with_ai(
                    message,
                    conversation_history
                )

        response_end = time.perf_counter()
        print(
          f"⏱️ AI RESPONSE TIME: "
          f"{response_end - response_start:.2f} seconds"
        )

        # ==================================================
        # STEP 13: RETURN RESPONSE
        # ==================================================

        request_end = time.perf_counter()

        print(
            f"⏱️ TOTAL API TIME: "
            f"{request_end - request_start:.2f} seconds"
        )

        return jsonify({

            "success": True,

            "response": ai_response,

            "properties": property_data,

            "requirements": lead_data,

            "rejected_property_ids":
                rejected_property_ids,

            "customer_created":
                customer_created,

            "requirement_created":
                requirement_created,

            "lead_created":
                lead_created
        })  
    # ======================================================
    # STEP 14: ERROR HANDLING
    # ======================================================

    except Exception as e:

        db.session.rollback()

        print("\nAI CHAT ERROR:")
        print(str(e))

        return jsonify({

            "success": False,

            "message":
                "Something went wrong while processing your request."

        }), 500
# ==========================================================
# AI VOICE TRANSCRIPTION API
# ==========================================================

@ai_bp.route("/api/transcribe", methods=["POST"])
def transcribe_voice():

    audio_file = request.files.get("audio")

    if not audio_file:
        return jsonify({
            "success": False,
            "message": "No audio file received."
        }), 400

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as temp_file:

            audio_file.save(
                temp_file.name
            )

            temp_path = temp_file.name

        transcript = transcribe_audio(
            temp_path
        )

        return jsonify({
            "success": True,
            "transcript": transcript
        })

    except Exception as e:

        print(
            "Transcription API error:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Could not transcribe audio."
        }), 500

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:
                os.remove(
                    temp_path
                )

            except Exception:
                pass