from app import create_app
from app.ai.lead_analyzer import extract_lead_data

app = create_app()

conversation = """
Customer: Hi, my name is Rakesh Reddy.
My phone number is 9876543210.
My email is rakesh@gmail.com.
I am looking for a 2 bedroom apartment in Amaravathi.
My budget is 70 lakhs and I want to buy.
"""

with app.app_context():

    result = extract_lead_data(conversation)

    print("\nEXTRACTED LEAD DATA")
    print("=" * 50)

    for key, value in result.items():
        print(f"{key:15}: {value}")