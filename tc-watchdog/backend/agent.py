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
            model="gemini-2.5-pro",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=image_data,
                            mime_type="image/png"
                        ),
                        types.Part.from_text(text="""
You are a legal expert AI that analyzes Terms & Conditions documents.

FIRST check if this page contains Terms & Conditions, Privacy Policy,
Terms of Service, or any legal agreement text.

If it does NOT contain any legal/terms content, return exactly:
{
  "trust_score": -1,
  "summary": "This page does not appear to contain Terms & Conditions or any legal agreement text.",
  "flags": [],
  "is_tc": false
}

If it DOES contain legal/terms content, return:
{
  "trust_score": <number 0-100>,
  "summary": "<2 sentence plain English summary>",
  "is_tc": true,
  "flags": [
    {
      "level": "danger or warning or safe",
      "clause": "<short clause title>",
      "explanation": "<plain English explanation in 1 simple sentence>"
    }
  ]
}

Rules:
- danger = selling data, auto charges, waiving rights, cant sue
- warning = data sharing, no refunds, account suspension
- safe = standard cookies, basic account terms
- trust_score: 0=very bad, 100=perfectly safe
- Return ONLY valid JSON, nothing else
""")
                    ]
                )
            ]
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
