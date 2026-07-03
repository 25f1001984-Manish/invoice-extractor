from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dateutil import parser
import re

app = FastAPI(title="Invoice Extractor")


class InvoiceRequest(BaseModel):
    text: str


class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.get("/")
def home():
    return {"message": "Invoice Extractor Running"}


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):

    text = req.text.strip()

    if not text:
        raise HTTPException(status_code=422, detail="Empty input")

    # -------------------------
    # Currency
    # -------------------------

    currency = ""

    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)

    if currency_match:
        currency = currency_match.group(1).upper()

    # -------------------------
    # Amount
    # -------------------------

    amount = 0.0

    amount_patterns = [
        r"(?:Total Due|Amount Due|Total|Balance Due|Grand Total)\D*([0-9]+(?:\.[0-9]{1,2})?)",
        r"\b(?:USD|EUR|GBP)\s*([0-9]+(?:\.[0-9]{1,2})?)",
        r"([0-9]+(?:\.[0-9]{1,2})?)"
    ]

    for pattern in amount_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            amount = float(m.group(1))
            break

    # -------------------------
    # Date
    # -------------------------

    date = ""

    date_patterns = [
        r"\b20\d{2}-\d{2}-\d{2}\b",
        r"\b\d{2}/\d{2}/20\d{2}\b",
        r"\b\d{2}-\d{2}-20\d{2}\b",
        r"\b[A-Za-z]+\s+\d{1,2},\s*20\d{2}\b"
    ]

    for pattern in date_patterns:
        m = re.search(pattern, text)
        if m:
            try:
                date = parser.parse(m.group()).strftime("%Y-%m-%d")
                break
            except:
                pass

    # -------------------------
    # Vendor
    # -------------------------

    vendor = ""

    vendor_patterns = [
        r"Invoice from\s*:?(.+)",
        r"Vendor\s*:?(.+)",
        r"From\s*:?(.+)"
    ]

    for pattern in vendor_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            vendor = m.group(1).split("\n")[0].strip(" .,:")
            break

    if vendor == "":
        lines = [i.strip() for i in text.split("\n") if i.strip()]
        if lines:
            vendor = lines[0]

    return InvoiceResponse(
        vendor=vendor,
        amount=amount,
        currency=currency,
        date=date
    )
