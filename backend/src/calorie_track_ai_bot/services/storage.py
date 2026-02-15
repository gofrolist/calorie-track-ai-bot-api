import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3

from .config import (
    APP_ENV,
    AWS_ACCESS_KEY_ID,
    AWS_ENDPOINT_URL_S3,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
    logger,
)

# Initialize S3 client only if all required config is available
s3: Any | None = None

if (
    AWS_ENDPOINT_URL_S3 is not None
    and AWS_ACCESS_KEY_ID is not None
    and AWS_SECRET_ACCESS_KEY is not None
    and BUCKET_NAME is not None
):
    s3 = boto3.Session().client(
        "s3",
        endpoint_url=AWS_ENDPOINT_URL_S3,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
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


async def tigris_presign_put(content_type: str, prefix: str = "photos") -> tuple[str, str]:
    if s3 is None or BUCKET_NAME is None:
        raise RuntimeError(
            "TIGRIS configuration not available. Photo upload functionality is disabled."
        )

    safe_prefix = prefix.strip("/ ")
    if not safe_prefix:
        safe_prefix = "photos"
    key = f"{safe_prefix}/{uuid.uuid4()}.jpg"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": BUCKET_NAME, "Key": key, "ContentType": content_type},
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
    if s3 is None or BUCKET_NAME is None:
        raise RuntimeError("TIGRIS configuration not available")

    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": BUCKET_NAME, "Key": file_key},
        ExpiresIn=expiry,
    )
    return url


def purge_transient_media(
    prefixes: list[str] | None = None, retention_hours: int = 24
) -> dict[str, list[str]]:
    """Delete inline transient media older than the configured retention window.

    Args:
        prefixes: S3 key prefixes to scan for transient media.
        retention_hours: Maximum age before deletion.

    Returns:
        Dict mapping prefixes to the list of deleted object keys.
    """
    if s3 is None or BUCKET_NAME is None:
        raise RuntimeError("TIGRIS configuration not available")

    scan_prefixes = prefixes or ["inline/", "inline-temp/", "transient/inline/"]
    cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)
    deleted: dict[str, list[str]] = {}

    for prefix in scan_prefixes:
        paginator = s3.get_paginator("list_objects_v2")
        removed: list[str] = []

        for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj.get("Key")
                last_modified = obj.get("LastModified")
                if not key or not last_modified:
                    continue

                if last_modified.tzinfo is None:
                    last_modified = last_modified.replace(tzinfo=UTC)

                if last_modified <= cutoff:
                    s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                    removed.append(key)
                    logger.info(
                        "inline.media.purged",
                        extra={
                            "key": key,
                            "prefix": prefix,
                            "last_modified": last_modified.isoformat(),
                            "retention_hours": retention_hours,
                        },
                    )

        if removed:
            deleted[prefix] = removed

    if deleted:
        logger.info(
            "inline.media.purge_summary",
            extra={
                "prefixes": list(deleted.keys()),
                "deleted_count": sum(len(keys) for keys in deleted.values()),
                "retention_hours": retention_hours,
            },
        )

    return deleted
