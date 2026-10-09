import os
import asyncio
import wave

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


MODEL = "gemini-3.8-live"


async def main():

    print("=" * 60)
    print("GEMINI LIVE AUDIO-ONLY TEST")
    print("=" * 60)

    config = types.LiveConnectConfig(

        response_modalities=[
            "AUDIO"
        ],

        output_audio_transcription=
            types.AudioTranscriptionConfig(),

        system_instruction="""
You are a helpful voice assistant.

Keep your response short and conversational.

Say exactly:

Hello! I am your AI real estate assistant.
How can I help you today?
"""
    )

    print()
    print("Connecting to Gemini Live...")

    async with client.aio.live.connect(
        model=MODEL,
        config=config
    ) as session:

        print("Connected.")

        audio_chunks = []
        audio_bytes = 0

        await session.send_client_content(
            turns={
                "role": "user",
                "parts": [
                    {
                        "text":
                            "Say your greeting now."
                    }
                ]
            },
            turn_complete=True
        )

        print()
        print("Waiting for audio...")

        async for response in session.receive():

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

                        data = (
                            part.inline_data.data
                        )

                        audio_chunks.append(
                            data
                        )

                        audio_bytes += len(data)

                        print(
                            f"\rAudio bytes: "
                            f"{audio_bytes}",
                            end="",
                            flush=True
                        )

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
                    print()
                    print(
                        "TRANSCRIPTION:",
                        text
                    )

            if (
                response.server_content
                and response.server_content
                .turn_complete
            ):

                print()
                print()
                print(
                    "[Turn complete]"
                )

                break


        if audio_chunks:

            audio_data = b"".join(
                audio_chunks
            )

            with wave.open(
                "gemini_live_audio_test.wav",
                "wb"
            ) as wav_file:

                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(
                    audio_data
                )

            print()
            print("=" * 60)
            print("SUCCESS - AUDIO RECEIVED")
            print("=" * 60)
            print(
                "File: "
                "gemini_live_audio_test.wav"
            )
            print(
                "Audio bytes:",
                len(audio_data)
            )

        else:

            print()
            print("=" * 60)
            print("NO AUDIO RECEIVED")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())