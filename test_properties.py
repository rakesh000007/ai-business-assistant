from app import create_app
from app.models import Property


app = create_app()

with app.app_context():

    properties = Property.query.order_by(Property.user_id, Property.id).all()

    print("\nALL PROPERTIES")
    print("=" * 80)

    if not properties:
        print("No properties found in database.")

    else:
        for property in properties:
            print(f"Database ID : {property.id}")
            print(f"User ID     : {property.user_id}")
            print(f"Property ID : {property.property_id}")
            print(f"Title       : {property.title}")
            print(f"Type        : {property.property_type}")
            print(f"City        : {property.city}")
            print(f"Price       : {property.short_price}")
            print(f"Bedrooms    : {property.bedrooms}")
            print(f"Status      : {property.status}")
            print("-" * 80)