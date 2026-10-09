import os
import asyncio
import json
import time
import wave

from app.ai.recommendation import get_matching_properties
from app import create_app
from app.models import Property

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit()


client = genai.Client(
    api_key=api_key
)
app = create_app()

MODEL = "gemini-3.8-live"


# ==================================================
# REAL DATABASE FUNCTION
# ==================================================

def search_properties(
    city=None,
    property_type=None,
    bedrooms=None,
    budget=None
):
    print()
    print("=" * 60)
    print("TOOL CALLED: search_properties")
    print("=" * 60)

    print("city          :", city)
    print("property_type :", property_type)
    print("bedrooms      :", bedrooms)
    print("budget        :", budget)

    with app.app_context():

        properties = get_matching_properties(
            user_id=1,
            property_type=property_type,
            city=city,
            budget=budget,
            bedrooms=bedrooms
        )

    result = {
        "properties": []
    }

    for property in properties:

        result["properties"].append({
            "property_id": property.property_id,
            "title": property.title,
            "property_type": property.property_type,
            "city": property.city,
            "area": property.area,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "sqft": property.sqft,
            "price": property.price,
            "status": property.status,
            "description": property.description
        })

    print()
    print("DATABASE RESULT:")

    print(
        json.dumps(
            result,
            indent=4,
            default=str
        )
    )

    return result

# ==================================================
# GET PROPERTY DETAILS
# ==================================================

def get_property_details(property_id):
    print()
    print("=" * 60)
    print("TOOL CALLED: get_property_details")
    print("=" * 60)

    print("property_id :", property_id)

    with app.app_context():

        property = Property.query.filter_by(
            property_id=property_id,
            user_id=1
        ).first()

    if not property:
        result = {
            "found": False,
            "message": "Property not found."
        }

    else:
        result = {
            "found": True,
            "property": {
                "property_id": property.property_id,
                "title": property.title,
                "property_type": property.property_type,
                "city": property.city,
                "area": property.area,
                "address": property.address,
                "bedrooms": property.bedrooms,
                "bathrooms": property.bathrooms,
                "sqft": property.sqft,
                "price": property.price,
                "status": property.status,
                "description": property.description
            }
        }

    print()
    print("PROPERTY DETAILS:")

    print(
        json.dumps(
            result,
            indent=4,
            default=str
        )
    )

    return result

# ==================================================
# TOOL DECLARATION
# ==================================================

search_properties_tool = types.FunctionDeclaration(
    name="search_properties",
    behavior="BLOCKING",

    description=(
        "Search available properties from the business database "
        "using the customer's requirements."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "city": types.Schema(
                type="STRING",
                description=(
                    "City where the customer wants the property."
                )
            ),
            "property_type": types.Schema(
                type="STRING",
                description=(
                    "Property type such as Apartment, Villa, "
                    "House, Plot, or Commercial."
                )
            ),
            "bedrooms": types.Schema(
                type="INTEGER",
                description=(
                    "Number of bedrooms required."
                )
            ),
            "budget": types.Schema(
                type="NUMBER",
                description=(
                    "Maximum property budget in Indian rupees."
                )
            )
        },
        required=[
            "city",
            "property_type",
            "bedrooms",
            "budget"
        ]
    )
)


get_property_details_tool = types.FunctionDeclaration(
    name="get_property_details",
    behavior="BLOCKING",
    description=(
        "Get complete verified details about a specific property "
        "from the business database."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "property_id": types.Schema(
                type="STRING",
                description=(
                    "The unique property ID, such as PROP010."
                )
            )
        },
        required=[
            "property_id"
        ]
    )
)


tool = types.Tool(
    function_declarations=[
        search_properties_tool,
        get_property_details_tool
    ]
)

# ==================================================
# LIVE CONFIGURATION
# ==================================================

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    output_audio_transcription=types.AudioTranscriptionConfig(),
    tools=[tool],
system_instruction="""
You are an AI voice assistant for a real-estate business.

Your job is to understand customer property questions.

When the customer asks to find properties,
USE the search_properties tool.

When the customer asks for details about a specific property,
USE the get_property_details tool.

IMPORTANT:

- Never invent property information.
- Never invent prices.
- Never invent availability.
- Never claim that no property exists without using the appropriate tool.
- Property information must come from the tool result.
- Keep spoken responses short and conversational.
"""
)


# ==================================================
# MAIN
# ==================================================

async def main():

    print("=" * 60)
    print("GEMINI LIVE FUNCTION CALLING TEST")
    print("=" * 60)

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        print()
        print("Connected to Gemini Live.")

        customer_message = (
            "Tell me more about property PROP010."
            "Please answer me verbally with a short spoken response."
        )

        print()
        print("CUSTOMER:")
        print(customer_message)

        start_time = time.time()

        await session.send_client_content(
            turns={
                "role": "user",
                "parts": [
                    {
                        "text": customer_message
                    }
                ]
            },
            turn_complete=True
        )

        print()
        print("Waiting for Gemini...")
        print()
        # --------------------------------------------------
        # AUDIO OUTPUT FILE
        # --------------------------------------------------

        audio_file = wave.open(
            "gemini_response.wav",
            "wb"
        )

        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(24000)
        

        # --------------------------------------------------
        # FIRST RECEIVE PHASE
        # --------------------------------------------------

        async for response in session.receive():

            print()
            print("RESPONSE RECEIVED")

            if response.server_content:

                print(
                    "SERVER CONTENT:",
                    response.server_content
                )

            # --------------------------------------------------
            # TOOL CALL
            # --------------------------------------------------

            if response.tool_call:

                for function_call in (
                    response.tool_call.function_calls
                ):

                    print()
                    print("=" * 60)
                    print("GEMINI REQUESTED TOOL")
                    print("=" * 60)

                    print(
                        "Function:",
                        function_call.name
                    )

                    print(
                        "Arguments:",
                        function_call.args
                    )

                    result = None

                    # ------------------------------------------
                    # GET PROPERTY DETAILS
                    # ------------------------------------------

                    if (
                        function_call.name
                        == "get_property_details"
                    ):

                        property_id = (
                            function_call.args.get(
                                "property_id"
                            )
                        )

                        result = get_property_details(
                            property_id
                        )

                    # ------------------------------------------
                    # SEARCH PROPERTIES
                    # ------------------------------------------

                    elif (
                        function_call.name
                        == "search_properties"
                    ):

                        result = search_properties(
                            **function_call.args
                        )

                    # ------------------------------------------
                    # UNKNOWN TOOL
                    # ------------------------------------------

                    else:

                        result = {
                            "error": "Unknown function"
                        }

                    print()
                    print("=" * 60)
                    print("TOOL RESULT")
                    print("=" * 60)

                    print(
                        json.dumps(
                            result,
                            indent=4
                        )
                    )

                    # ------------------------------------------
                    # SEND TOOL RESULT
                    # ------------------------------------------

                    function_response = (
                        types.FunctionResponse(
                            id=function_call.id,
                            name=function_call.name,
                            response={
                                "result": result
                            }
                        )
                    )

                    await session.send_tool_response(
                        function_responses=[
                            function_response
                        ]
                    )

                    print()
                    print("=" * 60)
                    print("TOOL RESULT SENT TO GEMINI")
                    print("=" * 60)

                break

        # --------------------------------------------------
        # SECOND RECEIVE PHASE
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("WAITING FOR GEMINI FINAL RESPONSE")
        print("=" * 60)

        async for response in session.receive():

            print()
            print("FINAL RESPONSE RECEIVED")

            if response.data is not None:

                print(
                    "AUDIO DATA RECEIVED:",
                    len(response.data),
                    "bytes"
                )

                audio_file.writeframes(
                    response.data
                )

            if response.server_content:

                content = response.server_content

                print(
                    "SERVER CONTENT:",
                    content
                )

                if content.model_turn:

                    print()
                    print("=" * 60)
                    print("GEMINI MODEL RESPONSE")
                    print("=" * 60)

                    for part in content.model_turn.parts:

                        if part.inline_data:

                            audio_data = (
                                part.inline_data.data
                            )

                            print(
                                "AUDIO CHUNK RECEIVED:",
                                len(audio_data),
                                "bytes"
                            )

                            audio_file.writeframes(
                                audio_data
                            )

                        if part.text:

                            print(
                                "TEXT:",
                                part.text
                            )

                content = response.server_content

                print(
                    "SERVER CONTENT:",
                    content
                )

                # ------------------------------------------
                # MODEL TURN / AUDIO
                # ------------------------------------------

                if content.model_turn:

                    print()
                    print("=" * 60)
                    print("GEMINI MODEL RESPONSE")
                    print("=" * 60)

                    for part in content.model_turn.parts:

                        if part.inline_data:

                            audio_data = (
                                part.inline_data.data
                            )

                            print(
                                "AUDIO CHUNK RECEIVED:",
                                len(audio_data),
                                "bytes"
                            )

                            audio_file.writeframes(
                                audio_data
                            )

                        if part.text:

                            print(
                                "TEXT:",
                                part.text
                            )

                # ------------------------------------------
                # OUTPUT TRANSCRIPTION
                # ------------------------------------------

                if content.output_transcription:

                    print(
                        "GEMINI:",
                        content.output_transcription.text
                    )

                # ------------------------------------------
                # TURN COMPLETE
                # ------------------------------------------

                if content.turn_complete:

                    print()
                    print("=" * 60)
                    print("GEMINI TURN COMPLETE")
                    print("=" * 60)

                    break

        # --------------------------------------------------
        # CLOSE AUDIO FILE
        # --------------------------------------------------

        audio_file.close()

        # --------------------------------------------------
        # TOTAL TIME
        # --------------------------------------------------

        end_time = time.time()

        print()
        print("=" * 60)
        print("TOTAL TIME")
        print("=" * 60)

        print(
            f"{end_time - start_time:.2f} seconds"
        )


if __name__ == "__main__":
    asyncio.run(main())
