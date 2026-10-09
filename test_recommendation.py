from app import create_app
from app.ai.lead_analyzer import extract_lead_data
from app.ai.recommendation import get_matching_properties


app = create_app()

# Test user
USER_ID = 1

# Customer conversation
conversation = """
Customer: I am looking for a commercial property in Guntur.
AI: What is your budget?
Customer: My budget is around 60 lakhs.
AI: Are you looking to buy, rent, or lease?
Customer: I want to buy.
"""


with app.app_context():

    # --------------------------------------------------
    # STEP 1: AI extracts customer requirements
    # --------------------------------------------------

    lead_data = extract_lead_data(conversation)

    print("\nEXTRACTED REQUIREMENTS")
    print("=" * 50)

    for key, value in lead_data.items():
        print(f"{key:15}: {value}")


    # --------------------------------------------------
    # STEP 2: Search database using extracted data
    # --------------------------------------------------

    properties = get_matching_properties(
        user_id=USER_ID,
        property_type=lead_data.get("property_type"),
        city=lead_data.get("city"),
        budget=lead_data.get("budget"),
        bedrooms=lead_data.get("bedrooms")
    )


    # --------------------------------------------------
    # STEP 3: Display matching properties
    # --------------------------------------------------

    print("\nMATCHING PROPERTIES")
    print("=" * 50)

    if not properties:

        print("No matching properties found.")

    else:

        for property in properties:

            print(f"Property ID : {property.property_id}")
            print(f"Title       : {property.title}")
            print(f"Type        : {property.property_type}")
            print(f"City        : {property.city}")
            print(f"Bedrooms    : {property.bedrooms}")
            print(f"Price       : {property.short_price}")
            print(f"Status      : {property.status}")

            print("-" * 50)