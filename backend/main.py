import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io
import google.generativeai as genai
import json
import re

# Load API key
load_dotenv()
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)

# Choose model
model = genai.GenerativeModel("gemini-1.5-flash")

# FastAPI app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat endpoint
class Query(BaseModel):
    message: str

@app.post("/chat")
def chat_with_ai(query: Query):
    user_input = query.message.strip().lower()

    # Intent Mapping
    mode_mapping = {
        "csv": "You selected CSV upload. Please upload your CSV file below.",
        "details": "You selected manual input. Please provide transaction details like amount, recipient, time, etc.",
    }

    if user_input in mode_mapping:
        return {"response": f"<b>Mode Selected:</b> {user_input.title()}<br>{mode_mapping[user_input]}"}

    elif user_input not in ("csv", "details") and any(k in user_input for k in ["csv", "details"]):
        # If it's not an exact match but seems similar
        return {
            "response": (
                "<b>Invalid choice.</b><br>Please choose either <b>csv</b> or <b>details</b> to proceed."
            )
        }

    # Proceed with details if user entered actual transaction text
    if len(user_input.split()) < 4:
        return {
            "response": (
                "<b>The input seems too short for fraud analysis.</b><br>"
                "Please provide more transaction info like:<ul>"
                "<li><b>Amount</b></li>"
                "<li><b>Merchant</b></li>"
                "<li><b>Location</b></li>"
                "<li><b>Time</b></li></ul>"
                "Then ask again."
            )
        }

    # AI Fraud analysis prompt
    prompt = (
        "You are a fraud detection expert. Analyze the following transaction and reply in HTML.\n"
        f"Transaction: {query.message}\n\n"
        "Return response in this format:\n"
        "<ul>"
        "<li><b>Suspicious:</b> Yes/No</li>"
        "<li><b>Reason:</b> explain briefly</li>"
        "<li><b>Recommendation:</b> What should be done next?</li>"
        "</ul>"
    )

    response = model.generate_content(prompt)
    return {"response": response.text}

# CSV fraud detection
@app.post("/check_csv")
async def check_csv(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))

    # Limit max rows for performance (optional)
    df = df.head(20)  # You can increase or remove this limit

    # Convert dataframe to a list of transactions
    all_data = df.to_dict(orient='records')

    # Create the prompt
    prompt = (
        "You are a fraud detection expert.\n"
        "Analyze the following transactions and identify ONLY the suspicious ones. "
        "Return the suspicious transactions as a list in JSON format, where each item includes the transaction and a short reason why it's suspicious.\n\n"
        f"{all_data}"
    )

    try:
        res = model.generate_content(prompt)
        response_text = res.text.strip()

        # Optional: try to find a JSON-looking chunk
        match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if match:
            suspicious = json.loads(match.group(0))
        else:
            # If no JSON found, return raw text for debug
            return {
                "message": "Could not extract suspicious transactions as JSON.",
                "raw_response": response_text
            }

        if suspicious:
            return {
                "message": f"{len(suspicious)} suspicious transactions found!",
                "suspicious": suspicious
            }
        else:
            return {"message": "No suspicious transactions detected."}

    except Exception as e:
        return {
            "message": "Error during fraud detection.",
            "error": str(e)
        }
