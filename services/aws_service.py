import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")


def upload_file(file_path, file_name):
    try:
        s3.upload_file(
            file_path,
            BUCKET_NAME,
            file_name
        )
        return True
    except Exception as e:
        print(e)
        return False


def list_files():
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME
    )

    files = []

    if "Contents" in response:

        for obj in response["Contents"]:

            files.append({
                "name": obj["Key"],
                "size": round(obj["Size"] / 1024, 2)
            })

    return files


def delete_file(file_name):

    s3.delete_object(
        Bucket=BUCKET_NAME,
        Key=file_name
    )
    
def generate_download_url(file_name):

    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": file_name,
            "ResponseContentDisposition": f'attachment; filename="{file_name}"'
        },
        ExpiresIn=3600
    )

    return url


def download_file(file_name, download_path):

    s3.download_file(
        BUCKET_NAME,
        file_name,
        download_path
    )