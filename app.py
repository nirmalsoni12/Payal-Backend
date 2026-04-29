from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
import os, json, uuid, random, io

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

# ---------- DB ----------
def load_db():
    try:
        return json.load(open(DB_FILE))
    except:
        return []

def save_db(data):
    json.dump(data, open(DB_FILE, "w"))

# ---------- ID ----------
def generate_id(db):
    if not db:
        return "I01"
    last = db[-1]["id"]
    n = int(last.replace("I",""))
    return f"I{n+1:02d}"

# ---------- SIMPLE IMAGE HASH (AI-lite) ----------
def image_hash(bytes_data):
    img = Image.open(io.BytesIO(bytes_data)).convert("L").resize((8,8))
    pixels = list(img.getdata())
    avg = sum(pixels)/len(pixels)
    bits = "".join(['1' if p>avg else '0' for p in pixels])
    return hex(int(bits,2))

def hamming(a, b):
    return sum(ch1 != ch2 for ch1, ch2 in zip(bin(int(a,16))[2:].zfill(64),
                                             bin(int(b,16))[2:].zfill(64)))

# ---------- LOGIN ----------
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "payal@2026":
        return {"success": True}
    return {"success": False}

# ---------- ADD ITEM ----------
@app.post("/add-item")
async def add_item(
    file: UploadFile = File(...),
    name: str = Form(...),
    barcodes: str = Form(...),
    weights: str = Form(...)
):
    db = load_db()

    content = await file.read()
    ihash = image_hash(content)

    # 🔎 duplicate check (same design)
    for item in db:
        if hamming(item["hash"], ihash) < 10:
            # same design → quantity add
            new_codes = barcodes.split(",")
            item["barcodes"].extend(new_codes)
            item["weights"].update(json.loads(weights))
            item["quantity"] = len(item["barcodes"])
            save_db(db)
            return {"msg": "Existing item updated", "id": item["id"]}

    # new item
    item_id = generate_id(db)
    filename = f"{item_id}.jpg"

    with open(f"{UPLOAD_DIR}/{filename}", "wb") as f:
        f.write(content)

    new_item = {
        "id": item_id,
        "name": name,
        "barcodes": barcodes.split(","),
        "weights": json.loads(weights),
        "quantity": len(barcodes.split(",")),
        "image": filename,
        "hash": ihash
    }

    db.append(new_item)
    save_db(db)

    return {"id": item_id}

# ---------- SEARCH ----------
@app.post("/search")
async def search(file: UploadFile = File(...)):
    db = load_db()
    if not db:
        return {"error": "no data"}

    content = await file.read()
    qhash = image_hash(content)

    best = None
    best_score = 999

    for item in db:
        score = hamming(item["hash"], qhash)
        if score < best_score:
            best = item
            best_score = score

    if not best:
        return {"error": "no match"}

    tag = random.choice(best["barcodes"])
    weight = best["weights"].get(tag, {})

    return {
        "id": best["id"],
        "name": best["name"],
        "image": best["image"],
        "tag": tag,
        "gross": weight.get("gross"),
        "net": weight.get("net"),
        "quantity": best["quantity"],
        "similarity": 100 - best_score  # rough score
    }

# ---------- SALE ----------
@app.post("/sale")
def sale(tag: str = Form(...)):
    db = load_db()
    for item in db:
        if tag in item["barcodes"]:
            item["barcodes"].remove(tag)
            item["quantity"] -= 1
            save_db(db)
            return {"msg": "Sold"}
    return {"error": "Tag not found"}

# ---------- IMAGE ----------
@app.get("/image/{filename}")
def get_image(filename: str):
    return FileResponse(f"{UPLOAD_DIR}/{filename}")
