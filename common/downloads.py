"""
downloads.py — Serve desktop executables from GCS via signed URLs.

Executables are stored in:
  gs://dpi-transient-processing/downloads/<filename>

The frontend calls GET /downloads/<filename> → 302 redirect to a time-limited
signed URL so the user downloads directly from GCS (no VM bandwidth consumed).

If signing is unavailable (ADC without a service account key), falls back to
streaming the file through the API.
"""
import io
import logging
import os
from datetime import timedelta

logger = logging.getLogger(__name__)

GCS_BUCKET = os.getenv("DOWNLOADS_GCS_BUCKET", "dpi-transient-processing")
GCS_PREFIX = os.getenv("DOWNLOADS_GCS_PREFIX", "downloads")
SIGNED_URL_EXPIRY_MINUTES = int(os.getenv("DOWNLOAD_URL_EXPIRY_MINUTES", "60"))

ALLOWED_FILES = {
    # Clinical (ABDM) + Insurance (NHCX)
    "nhcx-extract-linux-x86_64.zip",
    "nhcx-extract-linux-aarch64.zip",
    "nhcx-extract-windows-x86_64.zip",
    "nhcx-extract-macos.zip",
    # Forgensic
    "ForgensicApp-ubuntu-latest.zip",
    "ForgensicApp-ubuntu-24.04-arm.zip",
    "ForgensicApp-windows-latest.zip",
    "ForgensicApp-macos-latest.zip",
    # Privacy Filter
    "pf-redact-linux-x86_64.zip",
    "pf-redact-linux-aarch64.zip",
    "pf-redact-windows-x86_64.zip",
    "pf-redact-macos.zip",
}


def _get_gcs_client():
    from google.cloud import storage as gcs
    return gcs.Client()


def get_download_url(filename: str) -> str | None:
    """Return a signed URL for the given executable, or None if unavailable."""
    if filename not in ALLOWED_FILES:
        return None

    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"{GCS_PREFIX}/{filename}")

        if not blob.exists():
            logger.warning("Download artifact not found: gs://%s/%s/%s", GCS_BUCKET, GCS_PREFIX, filename)
            return None

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=SIGNED_URL_EXPIRY_MINUTES),
            method="GET",
        )
        return url
    except Exception as exc:
        logger.warning("Signed URL generation failed (falling back to stream): %s", exc)
        return None


def stream_download(filename: str):
    """Stream the file from GCS. Returns (bytes_io, content_type) or (None, None)."""
    if filename not in ALLOWED_FILES:
        return None, None

    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"{GCS_PREFIX}/{filename}")

        if not blob.exists():
            return None, None

        data = io.BytesIO(blob.download_as_bytes())
        return data, "application/zip"
    except Exception as exc:
        logger.error("GCS stream download failed: %s", exc)
        return None, None


def list_available_downloads() -> list[dict]:
    """List all available executables in GCS."""
    available = []
    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET)
        for filename in ALLOWED_FILES:
            blob = bucket.blob(f"{GCS_PREFIX}/{filename}")
            if blob.exists():
                blob.reload()
                available.append({
                    "filename": filename,
                    "size_mb": round(blob.size / (1024 * 1024), 1) if blob.size else 0,
                    "url": f"/downloads/{filename}",
                })
    except Exception as exc:
        logger.warning("Failed to list downloads: %s", exc)
    return available
