from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

app = FastAPI()

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Home route
@app.get("/")
def home():
    return {"status": "AI Search Running 🚀"}

# Health check
@app.get("/health")
def health():
    return {"ok": True}

# Search API
@app.post("/search")
async def search(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        logging.info(f"File received: {file.filename}")

        async with httpx.AsyncClient(timeout=20) as client:
            response = None

            # retry logic
            for _ in range(2):
                try:
                    response = await client.post(
                        API_URL,
                        headers=headers,
                        content=contents
                    )
                    break
                except httpx.RequestError:
                    logging.error("Retrying request...")

        if response is None:
            return {"error": "AI server not responding"}

        if response.status_code != 200:
            logging.error(response.text)
            return {"error": response.text}

        result = response.json()

        if not isinstance(result, list):
            return {"error": "Invalid AI response", "raw": result}

        return {"result": result}

    except Exception as e:
        logging.error(str(e))
        return {"error": str(e)}
