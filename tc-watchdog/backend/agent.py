import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

def analyze_tc(image_base64: str) -> dict:
    try:
        image_data = base64.b64decode(image_base64)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type="image/png"
                        ),
                        types.Part.from_text(text="""
You are a strict legal expert AI. Analyze this Terms & Conditions screenshot.

STEP 1 — Check if this page contains Terms & Conditions, Privacy Policy or legal agreement text.

If NO legal text found, return EXACTLY this JSON:
{
  "trust_score": -1,
  "summary": "This page does not contain Terms & Conditions or any legal agreement.",
  "flags": [],
  "is_tc": false
}

If YES legal text found, follow these STRICT rules:

TRUST SCORE RULES — must follow exactly:
- Start at 100
- Subtract 30 for each DANGER clause found
- Subtract 10 for each WARNING clause found
- Minimum score is 0

DANGER clauses — ALWAYS flag these:
- Selling or sharing personal data with third parties for profit
- Forced arbitration or waiving right to sue
- Auto renewal charges without clear notice
- Collecting data without consent
- Can terminate account without reason

WARNING clauses — ALWAYS flag these:
- Sharing data with partners for advertising
- No refund policy
- Can change terms anytime without notice
- Content ownership claims
- Account suspension without warning

SAFE clauses — ALWAYS flag these:
- Standard cookie usage for login only
- Basic account creation terms
- Standard billing terms

Return EXACTLY this JSON format:
{
  "trust_score": <calculated number 0-100>,
  "summary": "<exactly 2 sentences in simple English>",
  "is_tc": true,
  "flags": [
    {
      "level": "danger",
      "clause": "<max 5 words title>",
      "explanation": "<exactly 1 simple sentence>"
    }
  ]
}

IMPORTANT RULES:
- Always return same result for same document
- Be consistent — same clauses always get same level
- Return ONLY valid JSON, no extra text
- No markdown, no backticks
""")
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=1000,
            )
        )

        text = response.text.strip()

        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text.strip())

    except Exception as e:
        return {
            "trust_score": 0,
            "summary": f"Error analyzing page: {str(e)}",
            "is_tc": False,
            "flags": []
        }
