from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json, os, shutil, uuid
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "items.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------- DB ----------------
def load_items():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE) as f:
        return json.load(f)

def save_items(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------------- IMAGE VECTOR ----------------
def image_to_vector(path):
    img = Image.open(path).resize((64, 64))
    arr = np.array(img).flatten()
    return arr / 255.0

# ---------------- DUPLICATE CHECK ----------------
def is_duplicate(new_vec, items, threshold=0.95):
    for item in items:
        vec = np.array(item["vector"]).reshape(1, -1)
        score = cosine_similarity(new_vec.reshape(1, -1), vec)[0][0]
        if score > threshold:
            return item, score
    return None, None

# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"status": "Phase 10 Running 🔥"}

# ---------------- CHECK ITEM ----------------
@app.post("/check-item")
async def check_item(file: UploadFile = File(...)):
    items = load_items()

    temp = "temp.jpg"
    with open(temp, "wb") as f:
        f.write(await file.read())

    vec = image_to_vector(temp)

    item, score = is_duplicate(vec, items)

    if item:
        return {
            "exists": True,
            "item": item,
            "similarity": round(float(score), 2)
        }

    return {"exists": False}

# ---------------- ADD WITH BARCODE ----------------
@app.post("/add-item")
async def add_item(
    file: UploadFile = File(...),
    name: str = Form(...),
    quantity: int = Form(...),
    barcodes: str = Form(...)
):
    items = load_items()

    sys_id = str(uuid.uuid4())[:8]
    path = f"{UPLOAD_DIR}/{sys_id}.jpg"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    vector = image_to_vector(path).tolist()

    barcode_list = barcodes.split(",")

    new_item = {
        "id": sys_id,
        "name": name,
        "image": path,
        "quantity": len(barcode_list),
        "tag_series": barcode_list,
        "vector": vector
    }

    items.append(new_item)
    save_items(items)

    return {"msg": "Item added"}

# ---------------- SEARCH ----------------
@app.post("/search")
async def search(file: UploadFile = File(...)):
    items = load_items()

    if not items:
        return {"error": "No data"}

    temp = "temp.jpg"
    with open(temp, "wb") as f:
        f.write(await file.read())

    query_vec = image_to_vector(temp).reshape(1, -1)

    best = None
    best_score = -1

    for item in items:
        vec = np.array(item["vector"]).reshape(1, -1)
        score = cosine_similarity(query_vec, vec)[0][0]

        if score > best_score:
            best_score = score
            best = item

    return {
        "match": best,
        "similarity": round(float(best_score), 2)
    }

# ---------------- SELL ----------------
@app.post("/sell-item")
def sell_item(tag_no: str = Form(...)):
    items = load_items()

    for item in items:
        if tag_no in item["tag_series"]:

            if item["quantity"] <= 0:
                return {"error": "Out of stock"}

            item["quantity"] -= 1
            item["tag_series"].remove(tag_no)

            save_items(items)

            return {
                "msg": "Sold",
                "remaining": item["quantity"]
            }

    return {"error": "Tag not found"}
