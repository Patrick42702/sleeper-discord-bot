import os

import boto3

# Base session
session = boto3.session.Session()

# Common kwargs
s3_kwargs = {
    # "endpoint_url": os.environ.get("S3_ENDPOINT"),
    "region_name": os.environ.get("S3_REGION", "us-east-1"),
    "aws_access_key_id": os.environ.get("S3_ACCESS_KEY"),
    "aws_secret_access_key": os.environ.get("S3_SECRET_KEY"),
}

# Create the client
s3 = session.client("s3", **s3_kwargs)
