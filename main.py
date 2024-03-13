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
# running on localhost:8000
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# AWS CloudFront settings
cloudfront_key_pair_id = keys.CLOUDFRONT_KEY_ID
cloudfront_distribution_domain = keys.CLOUDFRONT_DOMAIN
def rsa_signer(message):
    with open('./private_cf.pem', 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())

def generate_signed_url(filename):
    try:
        signer = CloudFrontSigner(cloudfront_key_pair_id, rsa_signer)
        expiration_time = datetime.now() + timedelta(hours=24*7)
        url = f"{cloudfront_distribution_domain}/{filename}"
        # print("in generate", url)
        signed_url = signer.generate_presigned_url(
            url,
            date_less_than=expiration_time
        )
        return signed_url
    except Exception as e:
        print(f"ERROR: {e}")
        
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file:
        print(file.filename)
        s3.upload_fileobj(file.file, BUCKET_NAME, file.filename)
        return "file uploaded"
    else:
        return "error in uploading."

def list_objects(bucket_name='reeltimes3', folder_name='demo'):
    paginator = s3.get_paginator('list_objects_v2')    
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=folder_name)
    filenames = set() 

    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents'][1:]:
                if obj['Size'] == 0:
                    continue
                print(f"Key: {obj['Key']}, Size: {obj['Size']}")
                filenames.add(obj['Key'].split('/')[-1])
    
    return list(filenames)

@app.get("/get-signed-url", response_model=List[str])
async def get_signed_url():
    folder_name = 'demo'
    filenames = list_objects('reeltimes3', folder_name)
    print(filenames)
    filenames = sorted(filenames)
    print(filenames)
    signed_urls = []
    # print(filenames)
    for filename in filenames:
        signed_url = generate_signed_url(f"{folder_name}/{filename}")
        # print(signed_url)
        signed_urls.append(signed_url)
    #print("SIGNED_URLS", signed_urls)
    return signed_urls
@app.get("/")
async def root():
    return {"message": "server working"}