from app import create_app

from app.ai.recommendation import (
    get_matching_properties
)

from app.ai.ai_service import (
    generate_property_response
)


app = create_app()

USER_ID = 1


with app.app_context():

    # Test with the property we know exists
    properties = get_matching_properties(
        user_id=USER_ID,
        property_type="Commercial",
        city="Guntur",
        budget=6000000
    )

    customer_message = """
    I am looking for a commercial property in Guntur
    under 60 lakhs. I want to buy.
    """

    response = generate_property_response(
        customer_message,
        properties
    )

    print("\nAI PROPERTY RESPONSE")
    print("=" * 60)
    print(response)