"""
AI Service
----------
Central AI service that connects the Flask
application with Ollama and the AI prompts.
"""

from app.ai.ollama_client import generate_response

from app.ai.prompts import (
    SYSTEM_PROMPT,
    CUSTOMER_REQUIREMENT_PROMPT,
    PROPERTY_RECOMMENDATION_PROMPT,
    LEAD_ANALYSIS_PROMPT,
    SUMMARY_PROMPT
)


# ==========================================================
# GENERAL AI CHAT
# ==========================================================

def chat_with_ai(message, conversation_history=None):
    """
    Send a customer message to the AI.

    conversation_history:
        Previous conversation messages.
    """

    conversation = ""

    if conversation_history:

        for item in conversation_history:

            if not isinstance(item, dict):
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

                conversation += (
                    f"{role}: {content}\n"
                )

    # Add latest customer message
    conversation += (
        f"user: {message}"
    )

    prompt = f"""
{SYSTEM_PROMPT}

==================================================
CURRENT CONVERSATION
==================================================

{conversation}

==================================================
INSTRUCTION
==================================================

Respond naturally to the customer's latest message.

Follow all rules in the system instructions.

Do not invent property or business information.
Do not answer unrelated questions using general knowledge.

If the customer is still providing requirements,
continue the conversation naturally.

Ask only ONE question at a time when additional
information is required.

Generate ONLY the customer-facing response.
"""

    return generate_response(prompt)


# ==========================================================
# CUSTOMER REQUIREMENT EXTRACTION
# ==========================================================

def extract_customer_requirements(conversation):
    """
    Extract structured customer requirements
    from a conversation.
    """

    prompt = CUSTOMER_REQUIREMENT_PROMPT.format(
        conversation=conversation
    )

    return generate_response(prompt)


# ==========================================================
# LEAD ANALYSIS
# ==========================================================

def analyze_lead(conversation):
    """
    Analyze a customer conversation and determine
    lead qualification and priority.
    """

    prompt = LEAD_ANALYSIS_PROMPT.format(
        conversation=conversation
    )

    return generate_response(prompt)


# ==========================================================
# PROPERTY RECOMMENDATION
# ==========================================================

def recommend_properties(requirements, properties):
    """
    Recommend properties based on customer
    requirements and available business properties.
    """

    prompt = PROPERTY_RECOMMENDATION_PROMPT.format(
        requirements=requirements,
        properties=properties
    )

    return generate_response(prompt)


# ==========================================================
# CRM SUMMARY
# ==========================================================

def generate_summary(conversation):
    """
    Generate a concise CRM summary from
    a customer conversation.
    """

    prompt = SUMMARY_PROMPT.format(
        conversation=conversation
    )

    return generate_response(prompt)

# ==========================================================
# PROPERTY RESPONSE
# ==========================================================

def generate_property_response(
    customer_message,
    properties,
    customer_interested=False,
    interest_question_asked=False,
    customer_not_interested=False,
    customer_name=None,
    customer_phone=None,
    lead_data=None
):
    """
    Generate customer-facing property responses
    deterministically.

    Property information comes ONLY from the
    properties supplied by the backend.

    Controlled property/contact flows do not require
    an LLM call, which keeps the response fast.
    """

    lead_data = lead_data or {}

    # ======================================================
    # CASE 1: CUSTOMER IS INTERESTED
    # ======================================================

    if customer_interested:

        # ----------------------------------------------
        # NAME REQUIRED
        # ----------------------------------------------

        if not customer_name:

            return (
                "Thank you for confirming your interest "
                "in the property. May I have your name "
                "so we can proceed with the follow-up?"
            )

        # ----------------------------------------------
        # PHONE REQUIRED
        # ----------------------------------------------

        if not customer_phone:

            return (
                f"Thanks, {customer_name}. "
                "May I have your 10-digit phone number?"
            )

        # ----------------------------------------------
        # VALIDATE PHONE
        # ----------------------------------------------

        phone_digits = "".join(
            ch for ch in str(customer_phone)
            if ch.isdigit()
        )

        # ----------------------------------------------
        # INVALID / INCOMPLETE PHONE
        # ----------------------------------------------

        if len(phone_digits) != 10:

            return (
                f"Thanks, {customer_name}. "
                "The phone number seems incomplete. "
                "Could you please provide your 10-digit "
                "phone number?"
            )

        # ----------------------------------------------
        # CONTACT DETAILS COMPLETE
        # ----------------------------------------------

        return (
            f"Thank you, {customer_name}. "
            "We have received your contact details "
            "and will follow up with you regarding "
            "the property."
        )

    # ======================================================
    # CASE 2: CUSTOMER REJECTED PROPERTY
    # ======================================================

    if customer_not_interested:

        # ----------------------------------------------
        # ANOTHER PROPERTY AVAILABLE
        # ----------------------------------------------

        if properties:

            p = properties[0]

            return (
                "Understood. Here's another matching "
                f"property: {p.title}. "
                f"It is a {p.property_type} property "
                f"in {p.city}, priced at {p.short_price}. "
                "Are you interested in this property?"
            )

        # ----------------------------------------------
        # NO MORE PROPERTIES
        # ----------------------------------------------

        return (
            "I understand. There are no more matching "
            "properties currently available based on "
            "your requirements. Would you like to "
            "adjust your requirements?"
        )

    # ======================================================
    # CASE 3: FIRST MATCHING PROPERTY
    # ======================================================

    if (
        properties
        and not interest_question_asked
    ):

        p = properties[0]

        response = (
            f"Hello! I found a matching property for you. "
            f"Property Name: {p.title}. "
            f"Property Type: {p.property_type}. "
            f"Location: {p.city}. "
            f"Price: {p.short_price}."
        )

        # ----------------------------------------------
        # Add availability only if available
        # ----------------------------------------------

        if getattr(
            p,
            "status",
            None
        ):

            response += (
                f" Availability: {p.status}."
            )

        response += (
            " Are you interested in this property?"
        )

        return response

    # ======================================================
    # CASE 4: INTEREST QUESTION ALREADY ASKED
    # ======================================================
    #
    # The customer has not yet given a clear YES/NO.
    # Do NOT show the same property again.
    # Simply wait for the customer's response.
    # ======================================================

    if interest_question_asked:

        return (
            "Are you interested in this property?"
        )

    # ======================================================
    # CASE 5: NO MATCHING PROPERTY
    # ======================================================

    if not properties:

        return (
            "I couldn't find a matching property currently "
            "available based on your requirements. "
            "Would you like to change your requirements so I can look for other options?"
        )

    # ======================================================
    # CASE 6: FALLBACK
    # ======================================================

    return (
        "Would you like to know more about this property?"
        )