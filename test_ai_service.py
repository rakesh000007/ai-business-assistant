from app.ai.ai_service import chat_with_ai


message = "I am looking for an apartment in Vijayawada under 80 lakhs."

response = chat_with_ai(message)

print("\nAI RESPONSE:")
print(response)