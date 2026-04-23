from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import httpx

HF_TOKEN = os.getenv("HF_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

app = FastAPI()

# CORS fix (VERY IMPORTANT)
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

    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=headers, content=contents)

    result = response.json()
    return {"result": result}
