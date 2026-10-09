# app/ai/conversation_controller.py


REQUIRED_PROPERTY_FIELDS = [
    "city",
    "property_type",
    "bedrooms",
    "budget"
]


def get_missing_fields(lead_data):
    """
    Determine which property requirements are still missing.
    """

    missing_fields = []

    for field in REQUIRED_PROPERTY_FIELDS:

        value = lead_data.get(field)

        if value is None or value == "":
            missing_fields.append(field)

    return missing_fields


def get_next_missing_field(lead_data):
    """
    Return the next property requirement that
    needs to be collected from the customer.
    """

    missing_fields = get_missing_fields(
        lead_data
    )

    if not missing_fields:
        return None

    return missing_fields[0]


def get_next_action(
    lead_data,
    customer_interested=False,
    valid_phone=False
):
    """
    Decide what the conversation should do next.

    Business logic stays here instead of inside
    the LLM.
    """

    missing_field = get_next_missing_field(
        lead_data
    )

    # --------------------------------------------------
    # STEP 1: Collect property requirements
    # --------------------------------------------------

    if missing_field == "city":

        return {
            "action": "ASK_CITY",
            "missing_field": "city"
        }

    if missing_field == "property_type":

        return {
            "action": "ASK_PROPERTY_TYPE",
            "missing_field": "property_type"
        }

    if missing_field == "bedrooms":

        return {
            "action": "ASK_BEDROOMS",
            "missing_field": "bedrooms"
        }

    if missing_field == "budget":

        return {
            "action": "ASK_BUDGET",
            "missing_field": "budget"
        }

    # --------------------------------------------------
    # STEP 2: All property requirements collected
    # --------------------------------------------------

    if not customer_interested:

        return {
            "action": "SEARCH_PROPERTIES",
            "missing_field": None
        }

    # --------------------------------------------------
    # STEP 3: Customer is interested
    # --------------------------------------------------

    if not lead_data.get("name"):

        return {
            "action": "ASK_NAME",
            "missing_field": "name"
        }

    if not valid_phone:

        return {
            "action": "ASK_PHONE",
            "missing_field": "phone"
        }

    # --------------------------------------------------
    # STEP 4: Ready for CRM
    # --------------------------------------------------

    return {
        "action": "CREATE_CRM",
        "missing_field": None
    }


def get_action_message(action):
    """
    Return a short natural response for deterministic
    conversation steps.
    """

    messages = {

        "ASK_CITY":
            "Which city are you looking for a property in?",

        "ASK_PROPERTY_TYPE":
            "What type of property are you looking for — Apartment, Villa, House, Plot, or Commercial?",

        "ASK_BEDROOMS":
            "How many bedrooms are you looking for?",

        "ASK_BUDGET":
            "What is your budget for the property?",

        "ASK_NAME":
            "Thank you for your interest. May I have your name so we can proceed with the follow-up?",

        "ASK_PHONE":
            "Could you please provide your phone number so our team can contact you?",

    }

    return messages.get(
        action,
        ""
    )