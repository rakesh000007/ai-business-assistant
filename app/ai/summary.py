"""
Lead Summary
------------
Generates a concise AI-powered summary
of a real-estate customer conversation.
"""

from app.ai.ollama_client import generate_response


# ==========================================================
# LEAD SUMMARY PROMPT
# ==========================================================

LEAD_SUMMARY_PROMPT = """
You are an AI assistant for a real-estate CRM.

Create a concise and professional summary of the
customer conversation provided below.

The summary is for the business owner or sales team,
NOT for the customer.

Include only information explicitly available
in the conversation.

Include, when available:

- Customer name
- Customer phone number
- Property type
- Preferred city
- Purpose: Buy, Rent, or Lease
- Budget
- Bedrooms
- Customer interest
- Property discussed
- Important customer requirements
- Follow-up information

- For Customer interest, report "Interested" only when
  the customer explicitly expresses interest in the
  property, such as "yes, I am interested",
  "I am interested", or an equivalent clear statement.
- Report "Not interested" only when the customer
  explicitly rejects the property or says they are
  not interested.
- If the customer does not clearly express interest
  or rejection, report "No specific interest mentioned."

- Only mention a follow-up as "scheduled" if the conversation contains an actual follow-up date or time.
- If the conversation only says that someone will follow up, say "Follow-up: Business will contact the customer" instead.

IMPORTANT RULES:

1. Do not invent information.
2. Do not assume missing information.
3. Do not include information that is not present
   in the conversation.
4. Keep the summary concise.
5. Use professional CRM language.
6. Do not use markdown headings.
7. Return only the summary text.
8. If some information is missing, simply omit it.

CUSTOMER CONVERSATION:

{conversation}
"""


# ==========================================================
# GENERATE LEAD SUMMARY
# ==========================================================

def generate_lead_summary(conversation):
    """
    Generate a concise AI summary from
    the customer's conversation.
    """

    if not conversation:
        return "No conversation information available."

    prompt = LEAD_SUMMARY_PROMPT.format(
        conversation=conversation
    )

    try:

        summary = generate_response(
            prompt
        )

        if not summary:
            return "No summary available."

        summary = summary.strip()

        # --------------------------------------------------
        # Fix follow-up information
        # --------------------------------------------------
        # The AI should not claim that a follow-up was
        # scheduled unless an actual date/time exists.
        #
        # Current CRM conversation does not contain a
        # scheduled follow-up date or time.
        # Therefore replace AI-generated follow-up wording
        # with a factual statement.
        # --------------------------------------------------

        import re

        summary = re.sub(
            r"Follow-up(?: Information)?\s*:\s*.*?(?=$|\n)",
            "Follow-up: Business will contact the customer.",
            summary,
            flags=re.IGNORECASE
        )

        return summary

    except Exception as e:

        print("\nAI SUMMARY ERROR:")
        print(e)

        return "Unable to generate lead summary."