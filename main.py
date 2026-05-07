from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import boto3
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ACCOUNT_ID = os.getenv("ACCOUNT_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

BUCKET_NAME = "shopify-uploads"

PUBLIC_URL = os.getenv("PUBLIC_URL")

s3 = boto3.client(
    service_name="s3",
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto"
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    contents = await file.read()

    # Max 10MB
    if len(contents) > 10_000_000:
        return {"error": "File too large"}

    # Images only
    if not file.content_type.startswith("image/"):
        return {"error": "Images only"}

    filename = f"{uuid.uuid4()}-{file.filename}"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=filename,
        Body=contents,
        ContentType=file.content_type
    )

    file_url = f"{PUBLIC_URL}/{filename}"

    return {
        "success": True,
        "url": file_url
    }