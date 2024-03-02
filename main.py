from fastapi import FastAPI, UploadFile, File
from typing import List
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import key_config as keys
import uvicorn
import boto3

app = FastAPI()
BUCKET_NAME = 'soccer-reels-video-upload'
s3= boto3.client('s3',
                 aws_access_key_id=keys.ACCESS_KEY_ID,
                 aws_secret_access_key=keys.SECRET_ACCESS_KEY
                 )
# Set up CORS
origins = [
    "http://localhost:3000",
    
]

# AWS CloudFront settings
cloudfront_key_pair_id = keys.CLOUDFRONT_KEY_ID
cloudfront_distribution_domain = keys.CLOUDFRONT_DOMAIN
cloudfront_resource_path = '/MP4/video.mp4'

def rsa_signer(message):
    with open('./cloudfront_rsa.pem', 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

def generate_signed_url():
    try:
        signer = CloudFrontSigner(cloudfront_key_pair_id, rsa_signer)
        expiration_time = datetime.now() + timedelta(hours=1)
        # epoch_time = int(expiration_time.timestamp())
        url = f"https://{cloudfront_distribution_domain}{cloudfront_resource_path}"
        signed_url = signer.generate_presigned_url(
            url,
            date_less_than=expiration_time
        )
        return signed_url
    except Exception as e:
        print(f"ERROR: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    with open(file.filename, 'rb') as file_data:
        print(file.filename)
        try:
            s3.upload_fileobj(file_data, BUCKET_NAME, file.filename)
            return "file uploaded"
        except:
            return "error in uploading."
    
@app.get("/get-signed-url")
async def get_signed_url():
    print("LOLOLOLO")
    signed_url = generate_signed_url()
    return JSONResponse(content={'signedUrl': signed_url})

@app.get("/")
async def root():
    return {"message": "server working"}
