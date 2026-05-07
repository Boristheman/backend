from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os
import requests

app = FastAPI()

# =========================================
# CORS
# =========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================
# R2 SETTINGS
# =========================================

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

PUBLIC_URL = os.getenv("PUBLIC_URL")

BUCKET_NAME = "shopify-uploads"

# =========================================
# PUSHOVER SETTINGS
# =========================================

PUSHOVER_USER_KEY = "u32fvw3vfvn3jr3hdk2oim2az2swfz"

PUSHOVER_API_TOKEN = "aru9oadozx3sod7mie6onuj16cij59"

# =========================================
# R2 CLIENT
# =========================================

s3 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

# =========================================
# PHONE NOTIFICATION
# =========================================

def send_notification(message):

    try:

        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_API_TOKEN,
                "user": PUSHOVER_USER_KEY,
                "message": message
            }
        )

        print("PHONE NOTIFICATION SENT")

    except Exception as e:

        print(f"NOTIFICATION ERROR: {e}")

# =========================================
# ROOT
# =========================================

@app.get("/")
async def root():

    return {
        "status": "Backend running"
    }

# =========================================
# UPLOAD ENDPOINT
# =========================================

@app.post("/upload")
async def upload_files(
    order_id: str = Form(...),
    files: list[UploadFile] = File(...)
):

    uploaded_files = []

    print(f"NEW ORDER RECEIVED: {order_id}")

    for file in files:

        try:

            contents = await file.read()

            # =========================================
            # MAX SIZE
            # =========================================

            if len(contents) > 10_000_000:

                print(f"FILE TOO LARGE: {file.filename}")

                continue

            # =========================================
            # IMAGE ONLY
            # =========================================

            if not file.content_type.startswith("image/"):

                print(f"NOT IMAGE: {file.filename}")

                continue

            # =========================================
            # FOLDER STRUCTURE
            # =========================================

            filename = f"{order_id}/{file.filename}"

            # =========================================
            # UPLOAD TO R2
            # =========================================

            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=filename,
                Body=contents,
                ContentType=file.content_type
            )

            file_url = f"{PUBLIC_URL}/{filename}"

            print(f"UPLOAD SUCCESS: {filename}")

            uploaded_files.append({
                "filename": filename,
                "url": file_url
            })

        except Exception as e:

            print(f"UPLOAD ERROR: {e}")

    # =========================================
    # SEND PHONE NOTIFICATION
    # =========================================

    if len(uploaded_files) > 0:

        send_notification(
            f"""
NEW FIGURINE ORDER

ORDER ID:
{order_id}

FILES:
{len(uploaded_files)}
"""
        )

    # =========================================
    # RESPONSE
    # =========================================

    return {
        "success": True,
        "order_id": order_id,
        "uploaded_count": len(uploaded_files),
        "uploaded": uploaded_files
    }