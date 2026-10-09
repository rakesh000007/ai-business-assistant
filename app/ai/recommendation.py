"""
Property Recommendation
-----------------------
Finds properties belonging to the logged-in business
that match a customer's requirements.
"""

from app.models import Property


def get_matching_properties(
    user_id,
    property_type=None,
    city=None,
    budget=None,
    bedrooms=None,
    excluded_property_ids=None
):
    """
    Find available properties belonging ONLY
    to the logged-in business user.

    Matching is based on:
    - Property type
    - City
    - Maximum budget
    - Exact bedroom requirement
    """

    # ======================================================
    # No requirements
    # ======================================================

    if not any([
        property_type,
        city,
        budget is not None,
        bedrooms is not None
    ]):
        return []

    # ======================================================
    # Base query
    # ======================================================

    query = Property.query.filter(
        Property.user_id == user_id,
        Property.status == "Available"
    )
        # ======================================================
    # EXCLUDE PREVIOUSLY REJECTED PROPERTIES
    # ======================================================

    if excluded_property_ids:
       query = query.filter(
          ~Property.property_id.in_(excluded_property_ids)
    )

    # ======================================================
    # Property Type
    # ======================================================

    if property_type:
        query = query.filter(
            Property.property_type == property_type
        )

    # ======================================================
    # City
    # ======================================================

    if city:
        query = query.filter(
            Property.city == city
        )

    # ======================================================
    # Maximum Budget
    # ======================================================

    if budget is not None:
        query = query.filter(
            Property.price <= budget
        )

    # ======================================================
    # Exact Bedrooms
    # ======================================================

    if bedrooms is not None:
        query = query.filter(
            Property.bedrooms == bedrooms
        )

    # ======================================================
    # Return database results
    # ======================================================

    return query.all()


def properties_to_text(properties):
    """
    Convert database Property objects into text
    for the AI.

    IMPORTANT:
    Only information from the database is included.
    """

    if not properties:
        return "No matching properties found."

    property_list = []

    for property in properties:

        details = f"""
Property ID: {property.property_id}
Title: {property.title}
Property Type: {property.property_type}
City: {property.city}
Area: {property.area or "Not provided"}
Address: {property.address or "Not provided"}
Bedrooms: {
    property.bedrooms
    if property.bedrooms is not None
    else "Not provided"
}
Bathrooms: {
    property.bathrooms
    if property.bathrooms is not None
    else "Not provided"
}
Size: {
    f"{property.sqft} sq.ft"
    if property.sqft is not None
    else "Not provided"
}
Price: {property.short_price}
Status: {property.status}
Description: {property.description or "Not provided"}
"""

        property_list.append(
            details.strip()
        )

    return "\n\n".join(property_list)