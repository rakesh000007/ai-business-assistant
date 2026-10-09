import os
import time
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app import create_app
from app.ai.recommendation import get_matching_properties


# ==========================================================
# LOAD ENVIRONMENT
# ==========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured in .env"
    )


# ==========================================================
# GEMINI CLIENT
# ==========================================================

client = genai.Client(
    api_key=api_key
)

MODEL = "gemini-3.1-flash-lite"


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = create_app()


# ==========================================================
# DATABASE TOOL
# ==========================================================

def search_properties(
    city: str,
    property_type: str,
    bedrooms: int,
    budget: int
):
    """
    Search the business owner's available
    properties using the real MySQL database.
    """

    print("\n")
    print("=" * 60)
    print("TOOL: search_properties")
    print("=" * 60)

    print("city         :", city)
    print("property_type:", property_type)
    print("bedrooms     :", bedrooms)
    print("budget       :", budget)

    with app.app_context():

        properties = get_matching_properties(
            user_id=1,
            city=city,
            property_type=property_type,
            bedrooms=bedrooms,
            budget=budget
        )

        results = []

        for property in properties:

            results.append({
                "property_id":
                    property.property_id,

                "title":
                    property.title,

                "property_type":
                    property.property_type,

                "city":
                    property.city,

                "area":
                    property.area,

                "bedrooms":
                    property.bedrooms,

                "bathrooms":
                    property.bathrooms,

                "sqft":
                    property.sqft,

                "price":
                    property.price,

                "status":
                    property.status,

                "description":
                    property.description
            })

        return {
            "properties": results
        }


# ==========================================================
# GEMINI TOOL DECLARATION
# ==========================================================

from google.genai import types


search_properties_declaration = {
    "name": "search_properties",

    "description": (
        "Search the real estate business database "
        "for currently available properties matching "
        "the customer's requirements. "
        "Use this tool whenever the customer asks "
        "to find or recommend properties."
    ),

    "parameters": {
        "type": "object",

        "properties": {

            "city": {
                "type": "string",
                "description":
                    "Customer's preferred city."
            },

            "property_type": {
                "type": "string",
                "description":
                    "Property type such as Apartment, "
                    "Villa, House, Plot, or Commercial."
            },

            "bedrooms": {
                "type": "integer",
                "description":
                    "Required number of bedrooms."
            },

            "budget": {
                "type": "integer",
                "description":
                    "Maximum budget in Indian rupees."
            }
        },

        "required": [
            "city",
            "property_type",
            "bedrooms",
            "budget"
        ]
    }
}


search_properties_tool = types.Tool(
    function_declarations=[
        search_properties_declaration
    ]
)

# ==========================================================
# TEST
# ==========================================================

def main():

    print("\n")
    print("=" * 60)
    print("GEMINI TEXT + REAL DATABASE TEST")
    print("=" * 60)

    customer_message = (
        "I am looking for a 2 BHK apartment "
        "in Hyderabad around 60 lakhs."
    )

    print("\nCUSTOMER:")
    print(customer_message)

    print("\nMODEL:")
    print(MODEL)

    # ======================================================
    # STEP 1 — GEMINI UNDERSTANDS CUSTOMER
    # ======================================================

    print("\nStarting Gemini request...")

    total_start = time.perf_counter()

    first_start = time.perf_counter()

    response = client.models.generate_content(
        model=MODEL,

        contents=customer_message,

        config={
            "system_instruction": """
You are an AI real-estate assistant.

Help customers find properties.

IMPORTANT RULES:

1. Never invent property information.
2. Never invent prices.
3. Never invent availability.
4. When the customer asks to find properties,
   use the search_properties tool.
5. Property information must come only from
   the tool result.
6. After receiving the tool result, give a
   short natural customer-facing response.
7. Do not mention internal tools, databases,
   function calls, or implementation details.
8. Keep the response conversational and suitable
   for a voice assistant.
""",
            "tools": [
                search_properties_tool
            ]
        }
    )

    first_time = (
        time.perf_counter() - first_start
    )

    print("\n")
    print("=" * 60)
    print("INITIAL GEMINI RESPONSE")
    print("=" * 60)

    print(response)

    print("\nFIRST GEMINI RESPONSE TIME:")
    print(
        f"{first_time:.2f} seconds"
    )

    # ======================================================
    # STEP 2 — CHECK FOR TOOL CALL
    # ======================================================

    function_call = None

    for part in response.candidates[0].content.parts:

        if part.function_call:

            function_call = part.function_call

            break

    if not function_call:

        print("\n❌ Gemini did not request a tool call.")

        print("\nTEXT RESPONSE:")

        if response.text:
            print(response.text)

        return

    print("\n")
    print("=" * 60)
    print("GEMINI REQUESTED TOOL")
    print("=" * 60)

    print("Tool name:")
    print(function_call.name)

    print("\nArguments:")

    print(
        json.dumps(
            dict(function_call.args),
            indent=4
        )
    )

    # ======================================================
    # STEP 3 — EXECUTE REAL DATABASE TOOL
    # ======================================================

    tool_start = time.perf_counter()

    tool_result = search_properties(
        city=function_call.args["city"],
        property_type=function_call.args["property_type"],
        bedrooms=function_call.args["bedrooms"],
        budget=function_call.args["budget"]
    )

    tool_time = (
        time.perf_counter() - tool_start
    )

    print("\n")
    print("=" * 60)
    print("REAL DATABASE RESULT")
    print("=" * 60)

    print(
        json.dumps(
            tool_result,
            indent=4,
            default=str
        )
    )

    print("\nDATABASE TOOL TIME:")
    print(
        f"{tool_time:.4f} seconds"
    )

    # ======================================================
    # STEP 4 — SEND DATABASE RESULT BACK TO GEMINI
    # ======================================================

    print("\n")
    print("=" * 60)
    print("SENDING DATABASE RESULT TO GEMINI")
    print("=" * 60)

    second_start = time.perf_counter()

    final_response = client.models.generate_content(
        model=MODEL,

        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=customer_message
                    )
                ]
            ),

            response.candidates[0].content,

            types.Content(
                role="user",

                parts=[
                    types.Part.from_function_response(
                        name=function_call.name,

                        response=tool_result
                    )
                ]
            )
        ],
        config={
            "system_instruction": """
You are an AI real-estate assistant.

The customer wants property recommendations.

You have received verified property information
from the search_properties tool.

IMPORTANT:

1. Use ONLY the property information provided
   by the tool.
2. Never invent any property details.
3. Never invent price or availability.
4. Give a short natural customer-facing response.
5. Mention the matching property clearly.
6. Ask whether the customer is interested.
7. Do not mention tools, databases, APIs,
   function calls, or implementation details.
8. This response will be spoken by a voice assistant,
   so keep it natural and concise.
""",

            "tools": [
                search_properties_tool
            ]
        }
    )

    second_time = (
        time.perf_counter() - second_start
    )

    total_time = (
        time.perf_counter() - total_start
    )

    # ======================================================
    # STEP 5 — FINAL CUSTOMER RESPONSE
    # ======================================================

    print("\n")
    print("=" * 60)
    print("FINAL CUSTOMER RESPONSE")
    print("=" * 60)

    print(
        final_response.text
    )

    # ======================================================
    # TIMING SUMMARY
    # ======================================================

    print("\n")
    print("=" * 60)
    print("TIMING SUMMARY")
    print("=" * 60)

    print(
        f"Gemini tool-call response : "
        f"{first_time:.2f} seconds"
    )

    print(
        f"Database search            : "
        f"{tool_time:.4f} seconds"
    )

    print(
        f"Gemini final response      : "
        f"{second_time:.2f} seconds"
    )

    print(
        f"TOTAL TEXT AI FLOW         : "
        f"{total_time:.2f} seconds"
    )

    print("\n")
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()