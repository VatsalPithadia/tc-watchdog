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

Look at this screenshot carefully. Check if it contains ANY of these:
- Terms of Service / Terms of Use / Terms & Conditions
- Privacy Policy
- Legal agreement or contract text
- End User License Agreement
- Cookie Policy
- Any legal document with clauses

Be GENEROUS in detection — if there is ANY legal or policy text visible, treat it as a T&C page.

Only return is_tc=false if the page is clearly something like:
- A social media feed
- A search results page
- A news article
- A shopping page with products
- A homepage with no legal text

If it DOES contain legal/terms content return:
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

If it clearly does NOT contain any legal text return:
{
  "trust_score": -1,
  "summary": "This page does not contain Terms & Conditions or any legal agreement.",
  "flags": [],
  "is_tc": false
}

Scoring rules:
- trust_score 0-40 = dangerous document
- trust_score 41-70 = use caution
- trust_score 71-100 = mostly safe
- danger = selling data, forced arbitration, auto charges, waiving right to sue
- warning = data sharing with partners, no refunds, account suspension
- safe = standard cookies, basic account terms, normal billing

Return ONLY valid JSON, nothing else. No markdown, no backticks.
""")
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1500,
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
            "trust_score": 50,
            "summary": "Could not analyze this page properly. Please try again.",
            "is_tc": True,
            "flags": []
        }
