from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import key_config as keys
import uvicorn
import boto3

app = FastAPI()
BUCKET_NAME = 'soccer-videos-bucket'
s3= boto3.client('s3',
                 aws_access_key_id=keys.ACCESS_KEY_ID,
                 aws_secret_access_key=keys.SECRET_ACCESS_KEY
                 )
# Set up CORS
origins = [
    "http://localhost:3000",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file:
        print(file.filename)
        s3.upload_fileobj(file.file, BUCKET_NAME, file.filename)
        return "file uploaded"
    else:
        return "error in uploading."

@app.get("/")
async def root():
    return {"message": "server working"}