from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "AI Search Running 🚀"}

# 🧠 Dummy AI (Phase 6 stable)
labels = ["ring", "bracelet", "necklace", "jewelry", "watch"]

@app.post("/search")
async def search(file: UploadFile = File(...)):
    contents = await file.read()

    if not contents:
        return {"error": "No file uploaded"}

    prediction = random.choice(labels)

    return {
        "result": [
            {
                "label": prediction,
                "score": round(random.uniform(0.85, 0.99), 2)
            }
        ]
    }
