from google.cloud import storage
import os
from google.api_core.exceptions import NotFound

# Path to your Google Cloud JSON key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "config/gcp_key.json"

BUCKET_NAME = "multicloud-storage-suruchi-2026"

client = storage.Client()
bucket = client.bucket(BUCKET_NAME)


# -----------------------------
# Upload File
# -----------------------------
def upload_file_gcp(file_path, filename):

    blob = bucket.blob(filename)

    blob.upload_from_filename(file_path)

    return True


# -----------------------------
# Download File
# -----------------------------
def download_file_gcp(filename, destination_path):

    blob = bucket.blob(filename)

    blob.download_to_filename(destination_path)

    return True


# -----------------------------
# Delete File
# -----------------------------


def delete_file_gcp(blob_name):

    blob = bucket.blob(blob_name)

    try:
        blob.delete()

    except NotFound:
        print(f"{blob_name} not found in GCP bucket.")

    return True

# -----------------------------
# List Files
# -----------------------------
def list_files_gcp():

    blobs = bucket.list_blobs()

    return [blob.name for blob in blobs]