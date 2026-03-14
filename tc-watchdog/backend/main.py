import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import base64
import io
from agent import analyze_tc

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- MODELS ----
class TextRequest(BaseModel):
    text: str

# ---- ROUTES ----

@app.get("/")
def home():
    return {"status": "T&C Watchdog is running!"}

# ---- Analyze Screenshot (Extension) ----
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    result = analyze_tc(image_base64)
    return result

# ---- Analyze Text (Website) ----
@app.post("/analyze-text")
async def analyze_text(req: TextRequest):
    from PIL import Image, ImageDraw
    
    # Create white image with text
    img = Image.new('RGB', (900, 700), color=(10, 15, 30))
    draw = ImageDraw.Draw(img)

    # Wrap text into lines
    words = req.text.split()
    lines = []
    line = ""
    for word in words:
        if len(line + word) < 95:
            line += word + " "
        else:
            lines.append(line.strip())
            line = word + " "
    if line:
        lines.append(line.strip())

    # Draw text on image
    y = 20
    for l in lines[:45]:
        draw.text((20, y), l, fill=(226, 232, 240))
        y += 18

    # Convert to base64
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    result = analyze_tc(img_b64)
    return result