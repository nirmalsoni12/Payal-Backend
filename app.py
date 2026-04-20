from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import datetime

app = FastAPI()

# CORS (frontend connect)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"],)

# DB
conn = sqlite3.connect("db.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS designs (id INTEGER PRIMARY KEY AUTOINCREMENT, image TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS items (tag INTEGER, design_id INTEGER, stock INTEGER, price REAL)")
cur.execute("CREATE TABLE IF NOT EXISTS sales (tag INTEGER, qty INTEGER, date TEXT)")
conn.commit()

# 🔥 Add Design
@app.post("/add_design")
async def add_design(file: UploadFile):
    path = f"dataset/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    cur.execute("INSERT INTO designs (image) VALUES (?)", (path,))
    conn.commit()
    return {"status": "design added"}

# 🔥 Add Item
@app.post("/add_item")
def add_item(tag: int, design_id: int, stock: int, price: float):
    cur.execute("INSERT INTO items VALUES (?, ?, ?, ?)", (tag, design_id, stock, price))
    conn.commit()
    return {"status": "item added"}

# 🔥 Sell
@app.post("/sell")
def sell(tag: int, qty: int):
    cur.execute("UPDATE items SET stock = stock - ? WHERE tag=?", (qty, tag))
    cur.execute("INSERT INTO sales VALUES (?, ?, ?)", (tag, qty, str(datetime.datetime.now())))
    conn.commit()
    return {"status": "sold"}

# 🔍 Search
@app.get("/search/{design_id}")
def search(design_id: int):
    cur.execute("SELECT * FROM items WHERE design_id=?", (design_id,))
    return {"items": cur.fetchall()}