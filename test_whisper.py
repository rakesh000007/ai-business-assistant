from faster_whisper import WhisperModel


print("Loading Whisper model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


print("Whisper model loaded.")
print()


audio_file = input(
    "Enter the path of an audio file: "
).strip()


print()
print("Transcribing...")
print()


segments, info = model.transcribe(
    audio_file,
    language="en",
    beam_size=5
)


print("Detected language:", info.language)
print()


full_text = ""


for segment in segments:

    text = segment.text.strip()

    if text:

        print(
            f"[{segment.start:.2f}s -> "
            f"{segment.end:.2f}s] {text}"
        )

        full_text += (
            text + " "
        )


print()
print("=" * 50)
print("FINAL TRANSCRIPTION")
print("=" * 50)
print(full_text.strip())
print("=" * 50)