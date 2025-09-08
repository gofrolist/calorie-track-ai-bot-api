import uuid

import boto3
from boto3.session import Session

from .config import (
    TIGRIS_ACCESS_KEY,
    TIGRIS_BUCKET,
    TIGRIS_ENDPOINT,
    TIGRIS_REGION,
    TIGRIS_SECRET_KEY,
)

if (
    TIGRIS_ENDPOINT is None
    or TIGRIS_ACCESS_KEY is None
    or TIGRIS_SECRET_KEY is None
    or TIGRIS_BUCKET is None
):
    raise ValueError("TIGRIS configuration must be set")

_session: Session = boto3.Session()
s3 = _session.client(
    "s3",
    endpoint_url=TIGRIS_ENDPOINT,
    aws_access_key_id=TIGRIS_ACCESS_KEY,
    aws_secret_access_key=TIGRIS_SECRET_KEY,
    region_name=TIGRIS_REGION,
)


async def tigris_presign_put(content_type: str) -> tuple[str, str]:
    key = f"photos/{uuid.uuid4()}.jpg"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": TIGRIS_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=900,
        HttpMethod="PUT",
    )
    return key, url
