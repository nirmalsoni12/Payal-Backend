from fastapi import FastAPI, UploadFile, File
from pyzbar.pyzbar import decode
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import re

app = FastAPI()

db = []

def extract_text(img):
    return pytesseract.image_to_string(img)

def parse_data(text):
    name = "Unknown"
    gw = ""
    nw = ""

    lines = text.split("\n")

    for line in lines:
        if "G.W" in line:
            gw = re.findall(r"\d+\.\d+", line)[0] if re.findall(r"\d+\.\d+", line) else ""
        if "N.W" in line:
            nw = re.findall(r"\d+\.\d+", line)[0] if re.findall(r"\d+\.\d+", line) else ""
        if "KRISHNA" in line.upper():
            name = "Krishna Payal"

    return name, gw, nw

@app.get("/")
def home():
    return {"message": "API is running 🚀"}

@app.post("/scan")
async def scan(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents))

    # barcode detect
    barcodes = decode(img)
    barcode_data = barcodes[0].data.decode("utf-8") if barcodes else "NONE"

    # OCR
    text = extract_text(img)
    name, gw, nw = parse_data(text)

    # duplicate check
    for item in db:
        if item["barcode"] == barcode_data:
            return {"error": "Already exists"}

    item = {
        "id": f"I{len(db)+1:02}",
        "name": name,
        "gross_weight": gw,
        "net_weight": nw,
        "barcode": barcode_data
    }

    db.append(item)

    return item
