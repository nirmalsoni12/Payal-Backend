from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json, os, shutil, uuid
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "items.json"
USERS = "users.json"
UPLOAD = "uploads"
os.makedirs(UPLOAD, exist_ok=True)

# ---------------- DB ----------------
def load_db():
    return json.load(open(DB)) if os.path.exists(DB) else []

def save_db(data):
    json.dump(data, open(DB, "w"), indent=2)

def load_users():
    return json.load(open(USERS))

# ---------------- LOGIN ----------------
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    for u in load_users():
        if u["username"] == username and u["password"] == password:
            return {"success": True, "msg": "Login success"}
    return {"success": False, "msg": "Invalid username or password"}
# ---------------- IMAGE VECTOR ----------------
def img_vec(path):
    img = Image.open(path).resize((64,64))
    arr = np.array(img).flatten()
    return arr / 255.0

# ---------------- DUPLICATE CHECK ----------------
def find_duplicate(vec, items):
    for item in items:
        v = np.array(item["vector"]).reshape(1,-1)
        score = cosine_similarity(vec.reshape(1,-1), v)[0][0]
        if score > 0.95:
            return item
    return None

# ---------------- ADD ITEM ----------------
@app.post("/add-item")
async def add_item(
    file: UploadFile = File(...),
    name: str = Form(...),
    barcodes: str = Form(...),
    weights: str = Form(...)
):
    items = load_db()

    temp = "temp.jpg"
    with open(temp, "wb") as f:
        f.write(await file.read())

    vec = img_vec(temp)
    existing = find_duplicate(vec, items)

    barcode_list = barcodes.split(",")
    weight_data = json.loads(weights)

    if existing:
        existing["quantity"] += len(barcode_list)
        existing["tag_series"].extend(barcode_list)
        existing["barcode_data"].update(weight_data)
        save_db(items)
        return {"msg": "Added to existing", "id": existing["id"]}

    sys_id = str(uuid.uuid4())[:8]
    path = f"{UPLOAD}/{sys_id}.jpg"
    shutil.copy(temp, path)

    new_item = {
        "id": sys_id,
        "name": name,
        "image": path,
        "quantity": len(barcode_list),
        "tag_series": barcode_list,
        "barcode_data": weight_data,
        "vector": vec.tolist()
    }

    items.append(new_item)
    save_db(items)

    return {"msg": "New item added", "id": sys_id}

# ---------------- SEARCH ----------------
@app.post("/search")
async def search(file: UploadFile = File(...)):
    items = load_db()

    temp = "temp.jpg"
    with open(temp, "wb") as f:
        f.write(await file.read())

    vec = img_vec(temp).reshape(1,-1)

    best = None
    best_score = 0

    for item in items:
        v = np.array(item["vector"]).reshape(1,-1)
        score = cosine_similarity(vec, v)[0][0]
        if score > best_score:
            best_score = score
            best = item

    if best_score > 0.95:
        return {"type": "same", "item": best}

    return {"type": "similar", "item": best}

# ---------------- SALE ----------------
@app.post("/sale")
def sale(tag: str = Form(...)):
    items = load_db()

    for item in items:
        if tag in item["tag_series"]:
            item["tag_series"].remove(tag)
            item["quantity"] -= 1
            save_db(items)
            return {"msg": "Sold", "remaining": item["quantity"]}

    return {"error": "Not found"}
