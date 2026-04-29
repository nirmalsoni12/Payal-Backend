from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os, json, uuid, io
import numpy as np
from PIL import Image
import cv2
import pytesseract
from pyzbar.pyzbar import decode
from transformers import CLIPProcessor, CLIPModel
from sklearn.metrics.pairwise import cosine_similarity
import torch

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "db.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- LOAD MODEL ----------------
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# ---------------- DB ----------------
def load_db():
    try:
        return json.load(open(DB_FILE))
    except:
        return []

def save_db(data):
    json.dump(data, open(DB_FILE, "w"))

# ---------------- ID ----------------
def generate_id(db):
    return f"I{str(len(db)+1).zfill(2)}"

# ---------------- BARCODE ----------------
def detect_barcode(image_bytes):
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    barcodes = decode(img)
    if barcodes:
        return barcodes[0].data.decode("utf-8")
    return None

# ---------------- OCR ----------------
def extract_text(image_bytes):
    npimg = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray)

def parse_details(text):
    name, gross, net = "", "", ""

    for line in text.split("\n"):
        if "G.W" in line or "GW" in line:
            gross = line.split(":")[-1].strip()
        elif "N.W" in line or "NW" in line:
            net = line.split(":")[-1].strip()
        elif len(line.strip()) > 3 and not name:
            name = line.strip()

    return name, gross, net

# ---------------- AI VECTOR ----------------
def get_embedding(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        emb = model.get_image_features(**inputs)
    return emb[0].numpy().tolist()

# ---------------- LOGIN ----------------
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "1234":
        return {"success": True}
    return {"success": False}

# ---------------- ADD ITEM ----------------
@app.post("/add-item")
async def add_item(
    file: UploadFile = File(...),
    barcode: str = Form(None)
):
    db = load_db()
    content = await file.read()

    # 🔥 auto barcode
    if not barcode:
        barcode = detect_barcode(content)

    if not barcode:
        return {"error": "Barcode not found"}

    # ❌ duplicate tag
    for item in db:
        if barcode in item["tags"]:
            return {"error": "Tag already exists"}

    # 🔍 OCR
    text = extract_text(content)
    name, gross, net = parse_details(text)

    # 🧠 AI vector
    vector = get_embedding(content)

    # 📸 save image
    filename = str(uuid.uuid4()) + ".jpg"
    with open(f"{UPLOAD_DIR}/{filename}", "wb") as f:
        f.write(content)

    # 🔥 match existing
    best_score = 0
    best_item = None

    for item in db:
        score = cosine_similarity(
            [vector], [item["vector"]]
        )[0][0]

        if score > best_score:
            best_score = score
            best_item = item

    if best_score > 0.90:
        best_item["tags"].append(barcode)
        save_db(db)
        return {"msg": "Added to existing", "id": best_item["id"]}

    # 🆕 new item
    new_item = {
        "id": generate_id(db),
        "tags": [barcode],
        "name": name,
        "gross": gross,
        "net": net,
        "vector": vector,
        "image": filename
    }

    db.append(new_item)
    save_db(db)

    return {"msg": "New item added", "id": new_item["id"]}

# ---------------- SEARCH ----------------
@app.post("/search")
async def search(file: UploadFile = File(...)):
    db = load_db()
    content = await file.read()
    query_vec = get_embedding(content)

    best_score = 0
    best_item = None

    for item in db:
        score = cosine_similarity(
            [query_vec], [item["vector"]]
        )[0][0]

        if score > best_score:
            best_score = score
            best_item = item

    if not best_item:
        return {"error": "Not found"}

    import random
    tag = random.choice(best_item["tags"])

    return {
        "id": best_item["id"],
        "tag": tag,
        "name": best_item["name"],
        "gross": best_item["gross"],
        "net": best_item["net"],
        "image": best_item["image"],
        "score": float(best_score)
    }

# ---------------- SALE ----------------
@app.post("/sale")
def sale(tag: str = Form(...)):
    db = load_db()

    for item in db:
        if tag in item["tags"]:
            item["tags"].remove(tag)
            save_db(db)
            return {"msg": "Sold"}

    return {"error": "Tag not found"}

# ---------------- IMAGE ----------------
@app.get("/image/{filename}")
def image(filename: str):
    return FileResponse(f"{UPLOAD_DIR}/{filename}")
