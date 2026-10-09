from app.ai.ollama_client import generate_response


prompt = "Introduce yourself in one short sentence."

response = generate_response(prompt)

print("\nAI RESPONSE:")
print(response)