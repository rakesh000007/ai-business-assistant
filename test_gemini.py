import os
import time

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit()


client = genai.Client(
    api_key=api_key
)


print("=" * 60)
print("GEMINI INTERACTIONS API TEST")
print("=" * 60)


# ==================================================
# TURN 1
# ==================================================

message_1 = """
I am looking for a 2 BHK apartment in Hyderabad.
My budget is 60 lakhs.
"""

print()
print("CUSTOMER 1:")
print(message_1)

start_time = time.time()

interaction_1 = client.interactions.create(
    model="gemini-3.5-flash-lite",
    input=message_1
)

end_time = time.time()

print()
print("GEMINI 1:")
print(interaction_1.output_text)

print()
print(
    f"TIME 1: "
    f"{end_time - start_time:.2f} seconds"
)

print()
print(
    f"INTERACTION ID: "
    f"{interaction_1.id}"
)


# ==================================================
# TURN 2
# ==================================================

message_2 = """
No, I didn't like that property.
Show me another one.
"""

print()
print("=" * 60)
print("CUSTOMER 2:")
print(message_2)

start_time = time.time()

interaction_2 = client.interactions.create(
    model="gemini-3.5-flash-lite",
    input=message_2,
    previous_interaction_id=interaction_1.id
)

end_time = time.time()

print()
print("GEMINI 2:")
print(interaction_2.output_text)

print()
print(
    f"TIME 2: "
    f"{end_time - start_time:.2f} seconds"
)


# ==================================================
# TURN 3
# ==================================================

message_3 = """
Actually, forget Hyderabad.
I want a 3 BHK apartment in Guntur
around 70 lakhs.
"""

print()
print("=" * 60)
print("CUSTOMER 3:")
print(message_3)

start_time = time.time()

interaction_3 = client.interactions.create(
    model="gemini-3.5-flash-lite",
    input=message_3,
    previous_interaction_id=interaction_2.id
)

end_time = time.time()

print()
print("GEMINI 3:")
print(interaction_3.output_text)

print()
print(
    f"TIME 3: "
    f"{end_time - start_time:.2f} seconds"
)


# ==================================================
# STREAMING TEST
# ==================================================

message_4 = """
Tell me briefly what you understood
about my latest requirements.
"""

print()
print("=" * 60)
print("STREAMING TEST")
print("=" * 60)

print()
print("GEMINI STREAM:")

start_time = time.time()

stream = client.interactions.create(
    model="gemini-3.5-flash-lite",
    input=message_4,
    previous_interaction_id=interaction_3.id,
    stream=True
)

first_text_time = None

for event in stream:

    if (
        event.event_type == "step.delta"
        and event.delta
        and getattr(event.delta, "type", None) == "text"
        and getattr(event.delta, "text", None)
    ):

        if first_text_time is None:
            first_text_time = time.time()

        print(
            event.delta.text,
            end="",
            flush=True
        )

end_time = time.time()

print()
print()

if first_text_time:
    print(
        f"TIME TO FIRST TEXT: "
        f"{first_text_time - start_time:.2f} seconds"
    )

print(
    f"TOTAL STREAM TIME: "
    f"{end_time - start_time:.2f} seconds"
)