"""
Lead Analyzer
-------------
Extracts structured customer information and
property requirements from the customer conversation.
"""


import re




# ==========================================================
# DEFAULT EMPTY DATA
# ==========================================================

def empty_lead_data():
    """
    Return an empty lead-data structure.
    """

    return {
        "name": None,
        "phone": None,
        "email": None,
        "city": None,
        "property_type": None,
        "purpose": None,
        "budget": None,
        "bedrooms": None
    }




# ==========================================================
# EXTRACT BUDGET DIRECTLY FROM CONVERSATION
# ==========================================================

def extract_budget_from_conversation(conversation):
    """
    Deterministically extract budget from the customer's
    conversation.

    This prevents Ollama from accidentally returning
    budget=None even when the customer explicitly provided it.
    """

    text = conversation.lower()

    # ------------------------------------------------------
    # Crore
    # ------------------------------------------------------

    crore_match = re.search(
        r"(?:budget\s*(?:is|of|around|approximately)?\s*)?"
        r"₹?\s*(\d+(?:\.\d+)?)\s*(?:crore|cr)\b",
        text
    )

    if crore_match:
        return int(
            float(crore_match.group(1)) * 10_000_000
        )

    # ------------------------------------------------------
    # Lakh / Lakhs / L
    # ------------------------------------------------------

    lakh_match = re.search(
        r"(?:budget\s*(?:is|of|around|approximately)?\s*)?"
        r"₹?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs|l)\b",
        text
    )

    if lakh_match:
        return int(
            float(lakh_match.group(1)) * 100_000
        )

    return None


# ==========================================================
# EXTRACT PROPERTY TYPE
# ==========================================================

def extract_property_type(conversation):
    """
    Extract property type deterministically.
    """

    property_types = [
        "Apartment",
        "Villa",
        "House",
        "Plot",
        "Commercial"
    ]

    text = conversation.lower()

    for property_type in property_types:

        if re.search(
            rf"\b{property_type.lower()}\b",
            text
        ):
            return property_type

    return None


# ==========================================================
# EXTRACT PURPOSE
# ==========================================================

def extract_purpose(conversation):
    """
    Extract Buy / Rent / Lease deterministically.
    """

    text = conversation.lower()

    # Buy
    if re.search(
        r"\b(buy|buying|purchase|purchasing)\b",
        text
    ):
        return "Buy"

    # Rent
    if re.search(
        r"\b(rent|rental|renting)\b",
        text
    ):
        return "Rent"

    # Lease
    if re.search(
        r"\b(lease|leasing)\b",
        text
    ):
        return "Lease"

    return None


# ==========================================================
# EXTRACT CITY
# ==========================================================

def extract_city(conversation):
    """
    Extract city from common customer statements.

    Uses the cities explicitly mentioned in the conversation.
    """

    # Add/extend this list with cities supported by your business.
    cities = [
        "Guntur",
        "Vijayawada",
        "Hyderabad",
        "Visakhapatnam",
        "Vizag",
        "Tirupati",
        "Nellore",
        "Kurnool",
        "Chennai",
        "Bangalore",
        "Bengaluru"
    ]

    text = conversation.lower()

    for city in cities:

        if re.search(
            rf"\b{city.lower()}\b",
            text
        ):

            # Normalize Vizag
            if city == "Vizag":
                return "Visakhapatnam"

            if city == "Bengaluru":
                return "Bangalore"

            return city

    return None


# ==========================================================
# EXTRACT BEDROOMS
# ==========================================================

def extract_bedrooms(conversation):
    """
    Extract bedroom count from explicit statements.

    Supports:
        2 BHK
        2 bhk
        2 b h k
        2 bedroom
        2 bedrooms
    """

    text = conversation.lower()

    # ------------------------------------------------------
    # Standard BHK
    # Example: 2 BHK
    # ------------------------------------------------------

    match = re.search(
        r"\b(\d+)\s*(?:bhk|bedroom|bedrooms)\b",
        text
    )

    if match:
        return int(
            match.group(1)
        )

    # ------------------------------------------------------
    # Spaced BHK
    # Example: 2 b h k
    # ------------------------------------------------------

    match = re.search(
        r"\b(\d+)\s*b\s*h\s*k\b",
        text
    )

    if match:
        return int(
            match.group(1)
        )

    return None
# ==========================================================
# EXTRACT CUSTOMER NAME
# ==========================================================

def extract_name(
    conversation,
    name_was_requested=False
):
    if not conversation:
        return None

    conversation = conversation.strip()

    patterns = [
        r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,40})",
        r"\bthis is\s+([A-Za-z][A-Za-z .'-]{1,40})",
        r"\bname\s*:\s*([A-Za-z][A-Za-z .'-]{1,40})",
        r"\bname is\s+([A-Za-z][A-Za-z .'-]{1,40})"
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            conversation,
            flags=re.IGNORECASE
        )

        if matches:

            name = matches[-1].strip()

            name = re.split(
                r"\b(?:and|my|phone|number|email|is)\b",
                name,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0].strip()

            name = name.strip(
                " .,!?;:"
            )

            if len(name) >= 2:

                return name

    # --------------------------------------------------
    # When the assistant explicitly asks for the name,
    # allow a standalone name such as:
    #
    # Arjun Kumar
    #
    # But reject incomplete responses such as:
    #
    # My name is
    # My name
    # Name is
    # --------------------------------------------------

    if name_was_requested:

        candidate = conversation.strip()
        candidate = candidate.strip(" .,!?;:")

        candidate_lower = candidate.lower()

        negative_name_phrases = [
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
            "i do not like it"
        ]

        if any(
            phrase in candidate_lower
            for phrase in negative_name_phrases
        ):
            return None

        invalid_names = {
            "yes",
            "yeah",
            "yep",
            "no",
            "nope",
            "nah",
            "okay",
            "ok",
            "thanks",
            "thank you",
            "sure",
            "fine",
            "interested",
            "not interested",
            "not really interested",
            "not very interested",
            "less interested",
            "not that interested",
            "no thanks",
            "not for me",
            "i dont want it",
            "i don't want it",
            "i do not want it",
            "i dont like it",
            "i don't like it",
            "i do not like it",
            "my name",
            "my name is",
            "name",
            "name is",
            "my",
            "is"
        }

        if candidate.lower() in invalid_names:
            return None

        # Reject incomplete phrases such as:
        # "My name is"
        # "Name is"
        if re.fullmatch(
            r"(?:my\s+)?name\s+is",
            candidate,
            flags=re.IGNORECASE
        ):
            return None

        if re.fullmatch(
            r"[A-Za-z]+(?:[ .'-][A-Za-z]+)*",
            candidate
        ):

            if len(candidate) >= 2:

                return candidate

    return None
# ==========================================================
# EXTRACT PHONE
# ==========================================================

def extract_phone(conversation):
    """
    Extract an Indian-style phone number.

    Supports:
        9876543210
        987 654 3210
        987-654-3210
        (9 87) 654-3210
        9 8 7 6 5 4 3 2 1 0
        +91 9876543210

    Returns:
        Valid 10-digit number -> normalized phone number
        Incomplete number -> None
        No phone number -> None
    """

    if not conversation:
        return None

    # ------------------------------------------------------
    # FIRST: Find a normal formatted phone number
    # ------------------------------------------------------

    formatted_matches = re.findall(
        r"(?<!\d)"
        r"(?:\+91[\s-]*)?"
        r"\(?[6-9]\d{2}\)?"
        r"[\s-]*"
        r"\d{3}"
        r"[\s-]*"
        r"\d{4}"
        r"(?!\d)",
        conversation
    )

    for candidate in reversed(formatted_matches):

        digits = re.sub(
            r"\D",
            "",
            candidate
        )

        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]

        if (
            len(digits) == 10
            and digits[0] in "6789"
        ):
            return digits

    # ------------------------------------------------------
    # SECOND: Handle spaced digits from speech recognition
    #
    # Example:
    # 9 8 7 6 5 4 3 2 1 0
    # ------------------------------------------------------

    spaced_matches = re.findall(
        r"(?<!\d)"
        r"[6-9]"
        r"(?:[\s.,-]+\d){9}"
        r"(?!\d)",
        conversation
    )

    for candidate in reversed(spaced_matches):

        digits = re.sub(
            r"\D",
            "",
            candidate
        )

        if (
            len(digits) == 10
            and digits[0] in "6789"
        ):
            return digits

    # ------------------------------------------------------
    # No complete phone number found
    # ------------------------------------------------------

    return None
# ==========================================================
# EXTRACT EMAIL
# ==========================================================

def extract_email(conversation):
    """
    Extract email address.
    """

    match = re.findall(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        conversation
    )

    if match:
        return match[-1]

    return None


# ==========================================================
# EXTRACT LEAD DATA
# ==========================================================

def extract_lead_data(
    conversation,
    name_was_requested=False
):
    """
    Extract structured customer information and
    property requirements deterministically.

    Structured CRM fields do not require an LLM call.
    This keeps the application fast and prevents
    hallucinated customer information.
    """

    # ------------------------------------------------------
    # No conversation
    # ------------------------------------------------------

    if not conversation:
        return empty_lead_data()

    # ------------------------------------------------------
    # Start with empty structured data
    # ------------------------------------------------------

    data = empty_lead_data()

    # ------------------------------------------------------
    # Extract customer name
    # ------------------------------------------------------

    data["name"] = extract_name(
        conversation,
        name_was_requested=name_was_requested
    )

    # ------------------------------------------------------
    # Extract phone
    # ------------------------------------------------------

    data["phone"] = extract_phone(
        conversation
    )

    # ------------------------------------------------------
    # Extract email
    # ------------------------------------------------------

    data["email"] = extract_email(
        conversation
    )

    # ------------------------------------------------------
    # Extract city
    # ------------------------------------------------------

    data["city"] = extract_city(
        conversation
    )

    # ------------------------------------------------------
    # Extract property type
    # ------------------------------------------------------

    data["property_type"] = extract_property_type(
        conversation
    )

    # ------------------------------------------------------
    # Extract purpose
    # ------------------------------------------------------

    data["purpose"] = extract_purpose(
        conversation
    )

    # ------------------------------------------------------
    # Extract budget
    # ------------------------------------------------------

    data["budget"] = extract_budget_from_conversation(
        conversation
    )

    # ------------------------------------------------------
    # Extract bedrooms
    # ------------------------------------------------------

    data["bedrooms"] = extract_bedrooms(
        conversation
    )

    return data