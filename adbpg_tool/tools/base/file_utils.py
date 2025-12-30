"""
File utilities for handling file downloads and uploads.

This module provides common file handling logic for:
- Downloading files from Dify internal API
- Determining file source (local, Dify, remote URL)
- Managing temporary files
"""

import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import requests
from tools.base import logger


class FileSource(Enum):
    """Type of file source"""

    LOCAL = "local"  # Local file path
    DIFY = "dify"  # Downloaded from Dify internal API
    REMOTE = "remote"  # Remote URL (publicly accessible)


@dataclass
class ResolvedFile:
    """Result of file resolution"""

    source: FileSource
    local_path: str | None  # Local file path (for LOCAL and DIFY sources)
    remote_url: str | None  # Remote URL (for REMOTE source)
    temp_file: str | None  # Temporary file path to clean up (for DIFY source)


def download_file_from_dify(file_url: str) -> str:
    """
    Download file from Dify API and save as temporary file.

    Args:
        file_url: Dify file URL (relative path like /files/xxx/file-preview?...)

    Returns:
        Temporary file path

    Raises:
        RuntimeError: If download or save fails
    """
    api_url = (
        os.getenv("INTERNAL_FILES_URL")
        or os.getenv("FILES_URL")
        or os.getenv("DIFY_INNER_API_URL")
        or os.getenv("PLUGIN_DIFY_INNER_API_URL")
        or "http://api:5001"
    )

    if file_url.startswith("/"):
        full_url = f"{api_url.rstrip('/')}{file_url}"
    elif file_url.startswith("http://") or file_url.startswith("https://"):
        full_url = file_url
    else:
        full_url = f"{api_url.rstrip('/')}/{file_url}"

    logger.info(f"Downloading file from Dify API: {full_url}")

    try:
        response = requests.get(full_url, timeout=120, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download file from Dify: {e}")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    try:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
        temp_file.flush()
        temp_file_path = temp_file.name
        logger.info(f"File downloaded to temporary path: {temp_file_path}")
        return temp_file_path
    except Exception as e:
        temp_file.close()
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise RuntimeError(f"Failed to save downloaded file: {e}")
    finally:
        temp_file.close()


def cleanup_temp_file(temp_file_path: str | None):
    """
    Clean up temporary file if it exists.

    Args:
        temp_file_path: Path to temporary file, or None
    """
    if temp_file_path and os.path.exists(temp_file_path):
        try:
            os.unlink(temp_file_path)
            logger.info(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {e}")


def resolve_file(file_url: str) -> ResolvedFile:
    """
    Resolve file URL to determine source and get local path if possible.

    Priority:
    1. If it's a local file path, use it directly
    2. Try to download from Dify internal API
    3. Fall back to treating as remote URL

    Args:
        file_url: File URL or local path

    Returns:
        ResolvedFile with source type and paths
    """
    # Check if it's a local file
    if os.path.isfile(file_url):
        logger.info(f"Resolved as local file: {file_url}")
        return ResolvedFile(
            source=FileSource.LOCAL,
            local_path=file_url,
            remote_url=None,
            temp_file=None,
        )

    # Try to download from Dify
    logger.info(f"Trying to download file from URL: {file_url}")
    try:
        temp_file_path = download_file_from_dify(file_url)
        logger.info(f"Resolved as Dify file, downloaded to: {temp_file_path}")
        return ResolvedFile(
            source=FileSource.DIFY,
            local_path=temp_file_path,
            remote_url=None,
            temp_file=temp_file_path,
        )
    except Exception as download_err:
        logger.warning(f"Download failed, treating as remote URL: {download_err}")
        return ResolvedFile(
            source=FileSource.REMOTE,
            local_path=None,
            remote_url=file_url,
            temp_file=None,
        )


@contextmanager
def resolve_file_context(file_url: str):
    """
    Context manager for file resolution with automatic cleanup.

    Usage:
        with resolve_file_context(file_url) as resolved:
            if resolved.local_path:
                # Use local file
            else:
                # Use remote URL

    Args:
        file_url: File URL or local path

    Yields:
        ResolvedFile with source type and paths
    """
    resolved = resolve_file(file_url)
    try:
        yield resolved
    finally:
        cleanup_temp_file(resolved.temp_file)


def upload_with_file_resolution(
    file_url: str,
    upload_advance_func: Callable[[str], dict],
    upload_url_func: Callable[[str], dict],
) -> dict:
    """
    Upload file using the appropriate method based on file source.

    Priority:
    1. Local file -> use advance API
    2. Dify file (downloaded) -> use advance API
    3. Remote URL -> use URL API

    Args:
        file_url: File URL or local path
        upload_advance_func: Function to call for local file upload, takes file_path
        upload_url_func: Function to call for remote URL upload, takes file_url

    Returns:
        Upload response dict
    """
    with resolve_file_context(file_url) as resolved:
        if resolved.local_path:
            logger.info(f"Using advance API with local path: {resolved.local_path}")
            return upload_advance_func(resolved.local_path)
        else:
            logger.info(f"Using URL API with remote URL: {resolved.remote_url}")
            return upload_url_func(resolved.remote_url)
