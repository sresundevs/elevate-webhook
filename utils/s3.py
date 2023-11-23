import io
import os

import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import dotenv_values

config = {
    **dotenv_values(".env"),    # load development variables
    **os.environ,               # override loaded values with environment variables
}

AWS_ACCESS_KEY_ID = config['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = config['AWS_SECRET_ACCESS_KEY']
AWS_BUCKET = config['AWS_BUCKET']

def upload_from_url(file, filename):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        s3.upload_fileobj(io.BytesIO(file), AWS_BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        print("Upload Successful")
        url = f"https://{AWS_BUCKET}.s3.amazonaws.com/{filename}"
        return url
    except FileNotFoundError:
        print("The file was not found")
        return None
    except NoCredentialsError:
        print("Credentials not available")
        return None
    
def upload_from_file(file, filename):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    try:
        s3.upload_fileobj(file, AWS_BUCKET, filename, ExtraArgs={'ACL': 'public-read'})
        print("Upload Successful")
        url = f"https://{AWS_BUCKET}.s3.amazonaws.com/{filename}"
        return url
    except FileNotFoundError:
        print("The file was not found")
        return None
    except NoCredentialsError:
        print("Credentials not available")
        return None