from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import json
import re

app = FastAPI()

extractor = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

class InvoiceRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(req: InvoiceRequest):

    if not req.text.strip():
        raise HTTPException(status_code=422, detail="Empty input")

    prompt = f"""
Extract invoice information.

Return ONLY JSON.

Fields:
vendor
amount
currency
date

Invoice:

{req.text}
"""

    result = extractor(
        prompt,
        max_new_tokens=128
    )[0]["generated_text"]

    try:
        json_text = re.search(r"\{.*\}", result, re.S).group()
        data = json.loads(json_text)

        return InvoiceResponse(
            vendor=data["vendor"],
            amount=float(data["amount"]),
            currency=data["currency"].upper(),
            date=data["date"]
        )

    except Exception:

        vendor = ""

        amount = 0

        currency = ""

        date = ""

        vendor_match = re.search(
            r"(?:Invoice from|Vendor|From)\s*[:\-]?\s*(.+)",
            req.text,
            re.I,
        )

        if vendor_match:
            vendor = vendor_match.group(1).split("\n")[0].strip()

        amount_match = re.search(
            r"(USD|EUR|GBP)?\s*([0-9]+(?:\.[0-9]{1,2})?)",
            req.text,
        )

        if amount_match:
            amount = float(amount_match.group(2))
            if amount_match.group(1):
                currency = amount_match.group(1)

        date_match = re.search(
            r"(2026-\d{2}-\d{2})",
            req.text,
        )

        if date_match:
            date = date_match.group(1)

        return InvoiceResponse(
            vendor=vendor,
            amount=amount,
            currency=currency,
            date=date,
        )


@app.get("/")
def home():
    return {"status": "running"}
