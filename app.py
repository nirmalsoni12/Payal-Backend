from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "AI Search Running"}

@app.post("/search")
async def search(file: UploadFile = File(...)):
    contents = await file.read()

    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/octet-stream"
        },
        data=contents
    )

    try:
        result = response.json()
    except:
        return {"error": response.text}

    if isinstance(result, dict) and "error" in result:
        return {"error": result["error"]}

    return {"result": result}
