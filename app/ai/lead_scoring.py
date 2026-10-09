"""
Lead Scoring
------------
Calculates an explainable AI lead score
from customer information, property requirements,
and customer interest.
"""


# ==========================================================
# CALCULATE LEAD SCORE
# ==========================================================

def calculate_lead_score(
    lead_data,
    customer_interested=False
):
    """
    Calculate a lead score from 0 to 100.

    Score factors:

    Customer name       : 10 points
    Phone number        : 20 points
    Email               : 5 points
    Property type       : 10 points
    City                : 10 points
    Budget              : 15 points
    Purpose             : 10 points
    Bedrooms            : 5 points
    Customer interest   : 15 points

    Maximum score       : 100
    """

    if not isinstance(lead_data, dict):
        lead_data = {}

    score = 0

    # ======================================================
    # CUSTOMER INFORMATION
    # ======================================================

    # Customer name
    if lead_data.get("name"):
        score += 10

    # Phone number
    if lead_data.get("phone"):
        score += 20

    # Email address
    if lead_data.get("email"):
        score += 5

    # ======================================================
    # PROPERTY REQUIREMENTS
    # ======================================================

    # Property type
    if lead_data.get("property_type"):
        score += 10

    # Preferred city
    if lead_data.get("city"):
        score += 10

    # Budget
    if lead_data.get("budget") is not None:
        score += 15

    # Purpose: Buy / Rent / Lease
    if lead_data.get("purpose"):
        score += 10

    # Bedrooms
    if lead_data.get("bedrooms") is not None:
        score += 5

    # ======================================================
    # CUSTOMER INTEREST
    # ======================================================

    if customer_interested:
        score += 15

    # ======================================================
    # SAFETY LIMIT
    # ======================================================

    score = max(
        0,
        min(
            score,
            100
        )
    )

    return score
# ==========================================================
# CALCULATE LEAD PRIORITY
# ==========================================================

def calculate_lead_priority(score):
    """
    Convert AI lead score into CRM priority.

    80 - 100 : High
    50 - 79  : Medium
    0 - 49   : Low
    """

    if score >= 80:
        return "High"

    if score >= 50:
        return "Medium"

    return "Low"