import uuid
from typing import Any

import boto3
from boto3.session import Session

from .config import (
    APP_ENV,
    AWS_ACCESS_KEY_ID,
    AWS_ENDPOINT_URL_S3,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
)

# Initialize S3 client only if all required config is available
s3: Any | None = None
TIGRIS_BUCKET: str | None = None

if (
    AWS_ENDPOINT_URL_S3 is not None
    and AWS_ACCESS_KEY_ID is not None
    and AWS_SECRET_ACCESS_KEY is not None
    and BUCKET_NAME is not None
):
    _session: Session = boto3.Session()
    s3 = _session.client(
        "s3",
        endpoint_url=AWS_ENDPOINT_URL_S3,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
    TIGRIS_BUCKET = BUCKET_NAME
elif APP_ENV == "dev":
    # In development mode, allow missing TIGRIS config
    print("WARNING: TIGRIS configuration not set. Photo upload functionality will be disabled.")
    print("To enable photo uploads, set the following environment variables:")
    print("- AWS_ENDPOINT_URL_S3")
    print("- AWS_ACCESS_KEY_ID")
    print("- AWS_SECRET_ACCESS_KEY")
    print("- BUCKET_NAME")
else:
    raise ValueError(
        "Tigris configuration must be set. Use standard AWS S3 environment variables:\n"
        "- AWS_ENDPOINT_URL_S3\n"
        "- AWS_ACCESS_KEY_ID\n"
        "- AWS_SECRET_ACCESS_KEY\n"
        "- BUCKET_NAME"
    )


async def tigris_presign_put(content_type: str) -> tuple[str, str]:
    if s3 is None or TIGRIS_BUCKET is None:
        raise RuntimeError(
            "TIGRIS configuration not available. Photo upload functionality is disabled."
        )

    key = f"photos/{uuid.uuid4()}.jpg"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": TIGRIS_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=900,
        HttpMethod="PUT",
    )
    return key, url


def generate_presigned_url(file_key: str, expiry: int = 3600) -> str:
    """Generate presigned GET URL for photo retrieval.

    Args:
        file_key: S3 object key
        expiry: URL expiration time in seconds (default: 1 hour)

    Returns:
        Presigned URL for downloading the photo
    """
    if s3 is None or TIGRIS_BUCKET is None:
        raise RuntimeError("TIGRIS configuration not available")

    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": TIGRIS_BUCKET, "Key": file_key},
        ExpiresIn=expiry,
    )
    return url
