from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os

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

# 🔥 Image compare function
def compare_images(img1, img2):
    img1 = cv2.resize(img1, (300, 300))
    img2 = cv2.resize(img2, (300, 300))
    diff = np.mean((img1 - img2) ** 2)
    return diff

@app.post("/search")
async def search(file: UploadFile):
    content = await file.read()
    
    # uploaded image
    nparr = np.frombuffer(content, np.uint8)
    query_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    best_score = float("inf")
    best_match = None

    # 🔍 compare with database images
    for img_name in os.listdir("database"):
        path = os.path.join("database", img_name)
        db_img = cv2.imread(path)

        score = compare_images(query_img, db_img)

        if score < best_score:
            best_score = score
            best_match = img_name

    return {
        "match": best_match,
        "score": float(best_score)
    }
