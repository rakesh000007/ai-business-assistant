import os
import asyncio
import time
import json
import wave

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app import create_app
from app.ai.recommendation import get_matching_properties


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit()


client = genai.Client(
    api_key=api_key
)


MODEL = "gemini-3.8-live"


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
    Search the real estate business database.
    """

    print()
    print("=" * 60)
    print("TOOL: search_properties")
    print("=" * 60)

    print("city         :", city)
    print("property_type:", property_type)
    print("bedrooms     :", bedrooms)
    print("budget       :", budget)

    tool_start = time.perf_counter()

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

        result = {
            "properties": results
        }

    tool_end = time.perf_counter()

    print()
    print("DATABASE RESULT:")

    print(
        json.dumps(
            result,
            indent=4,
            default=str
        )
    )

    print()
    print(
        "DATABASE SEARCH TIME: "
        f"{tool_end - tool_start:.4f} seconds"
    )

    return result


# ==========================================================
# GEMINI LIVE TOOL
# ==========================================================

search_properties_declaration = {
    "name": "search_properties",
    "behavior": "BLOCKING",

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
# MAIN TEST
# ==========================================================

async def main():

    print("=" * 60)
    print("GEMINI LIVE + REAL DATABASE TEST")
    print("=" * 60)

    config = types.LiveConnectConfig(

        response_modalities=[
            "AUDIO"
        ],

        output_audio_transcription=
            types.AudioTranscriptionConfig(),

        system_instruction="""
You are an AI assistant for a real-estate business.

Keep your responses short and conversational.

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
8. Ask whether the customer is interested
   after presenting a property.
""",

        tools=[
            search_properties_tool
        ]
    )

    print()
    print("Connecting to Gemini Live...")

    connection_start = time.perf_counter()

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        connection_time = (
            time.perf_counter()
            - connection_start
        )

        print(
            f"Connected in "
            f"{connection_time:.2f} seconds"
        )

        # ==================================================
        # CUSTOMER MESSAGE
        # ==================================================

        message = (
            "I am looking for a 2 BHK apartment "
            "in Hyderabad with a budget of 60 lakhs."
        )

        print()
        print("CUSTOMER:")
        print(message)

        total_start = time.perf_counter()

        first_response_time = None
        tool_call_time = None
        final_audio_time = None
        final_text_time = None
        tool_response_sent = False

        audio_chunks = []
        audio_bytes_received = 0
        # ==================================================
        # SEND CUSTOMER MESSAGE
        # ==================================================

        await session.send_client_content(
            turns={
                "role": "user",
                "parts": [
                    {
                        "text": message
                    }
                ]
            },
            turn_complete=True
        )

        # ==================================================
        # FIRST GEMINI RESPONSE
        # ==================================================

        print()
        print("=" * 60)
        print("WAITING FOR GEMINI...")
        print("=" * 60)

        async for response in session.receive():

            # ----------------------------------------------
            # GEMINI TOOL CALL
            # ----------------------------------------------

            if response.tool_call:

                if first_response_time is None:

                    first_response_time = (
                        time.perf_counter()
                        - total_start
                    )

                print()
                print("=" * 60)
                print("GEMINI REQUESTED TOOL")
                print("=" * 60)

                function_responses = []

                for function_call in (
                    response.tool_call.function_calls
                ):

                    print(
                        "Tool name:",
                        function_call.name
                    )

                    print()
                    print("Arguments:")

                    print(
                        json.dumps(
                            dict(function_call.args),
                            indent=4
                        )
                    )

                    # --------------------------------------
                    # EXECUTE REAL DATABASE TOOL
                    # --------------------------------------

                    tool_result = search_properties(
                        city=function_call.args["city"],
                        property_type=
                            function_call.args[
                                "property_type"
                            ],
                        bedrooms=
                            function_call.args[
                                "bedrooms"
                            ],
                        budget=
                            function_call.args[
                                "budget"
                            ]
                    )

                    print()
                    print("=" * 60)
                    print("DATABASE RESULT")
                    print("=" * 60)

                    print(
                        json.dumps(
                            tool_result,
                            indent=4
                        )
                    )

                    function_responses.append(
                        types.FunctionResponse(
                            name=function_call.name,
                            id=function_call.id,
                            response={
                                "result": tool_result
                            }
                        )
                    )

                print()
                print("=" * 60)
                print("FUNCTION RESPONSE BEING SENT")
                print("=" * 60)

                print(
                    json.dumps(
                        function_responses,
                        default=str,
                        indent=4
                    )
                )

                print()
                print("=" * 60)
                print("SENDING DATABASE RESULT TO GEMINI")
                print("=" * 60)

                await session.send_tool_response(
                    function_responses=function_responses
                )

                tool_response_sent = True

                tool_call_time = (
                    time.perf_counter()
                    - total_start
                )

                continue


            # ----------------------------------------------
            # FINAL MODEL AUDIO
            # ----------------------------------------------

            if (
                response.server_content
                and response.server_content.model_turn
            ):

                for part in (
                    response
                    .server_content
                    .model_turn
                    .parts
                ):

                    if part.inline_data:

                        if final_audio_time is None:

                            final_audio_time = (
                                time.perf_counter()
                                - total_start
                            )

                            print()
                            print(
                                "[First final audio received]"
                            )

                        audio_data = (
                            part.inline_data.data
                        )

                        audio_chunks.append(
                            audio_data
                        )

                        audio_bytes_received += (
                            len(audio_data)
                        )

                        print(
                            f"\rAudio bytes received: "
                            f"{audio_bytes_received}",
                            end="",
                            flush=True
                        )
            # ----------------------------------------------
            # FINAL MODEL TEXT TRANSCRIPTION
            # ----------------------------------------------

            if (
                response.server_content
                and response.server_content
                .output_transcription
            ):

                text = (
                    response
                    .server_content
                    .output_transcription
                    .text
                )

                if text:

                    if final_text_time is None:

                        final_text_time = (
                            time.perf_counter()
                            - total_start
                        )

                        print()
                        print(
                            "[Final transcription started]"
                        )

                    print(
                        text,
                        end="",
                        flush=True
                    )

            # ----------------------------------------------
            # GENERATION COMPLETE
            # ----------------------------------------------

            if (
                response.server_content
                and response.server_content
                .generation_complete
            ):

                print()

                print(
                    "[Gemini generation complete]"
                )

                # Do NOT break here.
                # Gemini 3.8 Live can send the
                # generation-complete event before
                # the final model audio turn.


            # ----------------------------------------------
            # TURN COMPLETE
            # ----------------------------------------------

            if (
                response.server_content
                and response.server_content
                .turn_complete
            ):

                print()

                if tool_response_sent:

                    print(
                        "[Final Gemini turn complete]"
                    )

                    break

                else:

                    print(
                        "[Initial Gemini turn complete]"
                    )

        # ==================================================
        # SAVE GEMINI AUDIO
        # ==================================================

        if audio_chunks:

            audio_file = "gemini_live_output.wav"

            audio_data = b"".join(
                audio_chunks
            )

            with wave.open(
                audio_file,
                "wb"
            ) as wav_file:

                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(
                    audio_data
                )

            print()
            print()
            print("=" * 60)
            print("AUDIO SAVED")
            print("=" * 60)

            print(
                "File:",
                audio_file
            )

            print(
                "Audio bytes:",
                len(audio_data)
            )

        else:

            print()
            print()
            print("=" * 60)
            print("NO AUDIO RECEIVED")
            print("=" * 60)


        # ==================================================
        # TIMING
        # ==================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        print()
        print()
        print("=" * 60)
        print("TIMING SUMMARY")
        print("=" * 60)

        print(
            "LIVE CONNECTION TIME: "
            f"{connection_time:.2f} seconds"
        )

        if first_response_time is not None:

            print(
                "TIME TO FIRST GEMINI RESPONSE: "
                f"{first_response_time:.2f} seconds"
            )

        if final_audio_time is not None:

            print(
                "TIME TO FIRST AUDIO: "
                f"{final_audio_time:.2f} seconds"
            )

        if final_text_time is not None:

            print(
                "TIME TO FIRST TEXT: "
                f"{final_text_time:.2f} seconds"
            )

        if tool_call_time is not None:

            print(
                "TIME AFTER TOOL REQUEST: "
                f"{tool_call_time:.2f} seconds"
            )

        print(
            "TOTAL LIVE RESPONSE TIME: "
            f"{total_time:.2f} seconds"
        )

        print()
        print("=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())