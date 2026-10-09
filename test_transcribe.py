import requests


url = "http://127.0.0.1:5050/ai/api/transcribe"

audio_path = (
    r"C:\Users\rakes\OneDrive\Documents"
    r"\Sound Recordings\hi.wav.m4a"
)


with open(audio_path, "rb") as audio_file:

    response = requests.post(
        url,
        files={
            "audio": (
                "hi.wav.m4a",
                audio_file,
                "audio/mp4"
            )
        }
    )


print("STATUS CODE:", response.status_code)

print()

print("RESPONSE:")

print(response.text)