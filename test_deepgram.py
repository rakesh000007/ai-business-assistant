import os
from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()

api_key = os.getenv("DEEPGRAM_API_KEY")

if not api_key:
    print("ERROR: DEEPGRAM_API_KEY not found.")
    exit()

print("Deepgram API key loaded successfully.")

try:
    deepgram = DeepgramClient(api_key=api_key)

    connection = deepgram.listen.v1.connect(
        model="nova-3",
        language="en-IN",
        smart_format=True,
        interim_results=True,
        endpointing=300,
        utterance_end_ms=1000,
        numerals=True,
    )

    print("Deepgram connection object created successfully.")

except Exception as e:
    print("Deepgram connection test failed:")
    print(e)