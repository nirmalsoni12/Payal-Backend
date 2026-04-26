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

# ---------------- AUTO TAG ----------------
def generate_tag(items):
    if not items:
        return "TAG0001"
    last = items[-1]["tag_no"]
    num = int(last.replace("TAG", ""))
    return f"TAG{num+1:04d}"

# ---------------- IMAGE VECTOR ----------------
def image_to_vector(path):
    img = Image.open(path).resize((64, 64))
    arr = np.array(img).flatten()
    return arr / 255.0

# ---------------- HOME ----------------
@app.get("/")
def home():
    return {"status": "System Running 🚀"}

# ---------------- ADD ITEM ----------------
@app.post("/add-item")
async def add_item(
    file: UploadFile = File(...),
    name: str = Form(...),
    quantity: int = Form(...)
):
    items = load_items()

    tag_no = generate_tag(items)
    sys_id = str(uuid.uuid4())[:8]

    path = f"{UPLOAD_DIR}/{sys_id}.jpg"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    vector = image_to_vector(path).tolist()

    new_item = {
        "id": sys_id,
        "tag_no": tag_no,
        "name": name,
        "image": path,
        "quantity": quantity,
        "vector": vector
    }

    items.append(new_item)
    save_items(items)

    return {"msg": "Item added", "tag": tag_no}

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

# ---------------- SELL ITEM ----------------
@app.post("/sell-item")
def sell_item(tag_no: str = Form(...)):
    items = load_items()

    for item in items:
        if item["tag_no"] == tag_no:

            if item["quantity"] <= 0:
                return {"error": "Out of stock"}

            item["quantity"] -= 1
            save_items(items)

            return {
                "msg": "Sold",
                "remaining": item["quantity"]
            }

    return {"error": "Item not found"}
