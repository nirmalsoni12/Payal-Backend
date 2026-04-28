from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json, uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "db.json"

def load_db():
    try:
        return json.load(open(DB_FILE))
    except:
        return []

def save_db(data):
    json.dump(data, open(DB_FILE, "w"))

# LOGIN
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "payal@2026":
        return {"success": True}
    return {"success": False}

# ADD ITEM
@app.post("/add-item")
async def add_item(
    file: UploadFile = File(...),
    name: str = Form(...),
    barcodes: str = Form(...),
    weights: str = Form(...)
):
    db = load_db()

    item = {
        "id": str(uuid.uuid4()),
        "name": name,
        "barcodes": barcodes.split(","),
        "weights": json.loads(weights),
        "quantity": len(barcodes.split(",")),
        "image": file.filename
    }

    db.append(item)
    save_db(db)

    return {"id": item["id"]}

# SEARCH
@app.post("/search")
async def search(file: UploadFile = File(...)):
    db = load_db()
    if db:
        return {"item": db[0]}
    return {"error": "No data"}

# SALE (manual tag)
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
