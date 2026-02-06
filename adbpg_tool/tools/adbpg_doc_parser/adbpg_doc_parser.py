import json
import time
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger, resolve_file_context
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params

# Fixed collection name for dry run parsing
DRY_RUN_COLLECTION_NAME = "dify_doc_parser_dry_run"
# Poll interval in seconds
POLL_INTERVAL = 3
# Timeout in seconds (30 minutes)
TIMEOUT = 30 * 60


class AdbpgDocParser(Tool):

    def _parse_content_to_chunks(self, content: str) -> list[str]:
        """
        Parse the content to chunks
        """
        chunks = []
        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                chunk_json = json.loads(line)
            except json.JSONDecodeError:
                continue
            page_content = chunk_json.get("page_content", "")
            metadata = json.dumps(chunk_json.get("metadata", {}), ensure_ascii=False)
            chunk = f"{page_content}\n{metadata}"
            chunks.append(chunk)
        return chunks

    def _download_chunk_file(self, chunk_url: str) -> list[str]:
        logger.info(f"Downloading chunk file from: {chunk_url}")
        try:
            response = requests.get(chunk_url, timeout=120)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download chunk file: {e}")

        # Explicitly decode as UTF-8 to handle Chinese text correctly
        content = response.content.decode("utf-8")
        return self._parse_content_to_chunks(content)

    def _ensure_collection_exists(self, client: AnalyticDBAPIHelper):
        """
        Ensure the dry run collection exists, ignoring any errors
        """
        try:
            client.create_document_collection(
                knowledgebase=DRY_RUN_COLLECTION_NAME,
                enable_graph=False,
            )
            logger.info(f"Created collection: {DRY_RUN_COLLECTION_NAME}")
        except Exception as e:
            # Ignore any errors (collection may already exist)
            logger.info(
                f"Ignored error creating collection {DRY_RUN_COLLECTION_NAME}: {e}"
            )

    def _upload_document(
        self,
        client: AnalyticDBAPIHelper,
        params: dict,
        local_path: str | None,
        remote_url: str | None,
    ) -> str:
        """
        Upload document for dry run parsing

        Args:
            client: AnalyticDBAPIHelper instance
            params: Tool parameters
            local_path: Local file path (if available)
            remote_url: Remote URL (if no local path)

        Returns:
            Job ID
        """
        # Build upload parameters with dry_run=True
        upload_params = {
            "knowledgebase": DRY_RUN_COLLECTION_NAME,
            "filename": params.get("filename"),
            "dry_run": True,
            "chunksize": params.get("chunksize"),
            "document_loader_name": params.get("document_loader_name"),
            "chunk_overlap": params.get("chunk_overlap"),
            "separators": params.get("separators"),
            "zh_title_enhance": params.get("zh_title_enhance"),
            "text_splitter_name": params.get("text_splitter_name"),
            "vl_enhance": params.get("vl_enhance"),
            "splitter_model": params.get("splitter_model"),
        }
        # Remove None values
        upload_params = {k: v for k, v in upload_params.items() if v is not None}

        if local_path:
            # Use advance API for local/downloaded files
            logger.info(f"Using advance API with local path: {local_path}")
            upload_params["file_path"] = local_path
            response = client.upload_document_async_advance(**upload_params)
        else:
            # Use URL API for remote URLs
            logger.info(f"Using URL API with remote URL: {remote_url}")
            upload_params["fileurl"] = remote_url
            response = client.upload_document_async(**upload_params)

        job_id = response.get("JobId")
        if not job_id:
            raise RuntimeError(f"No JobId in upload response: {response}")

        logger.info(f"Upload job started with JobId: {job_id}")
        return job_id

    def _poll_job(self, client: AnalyticDBAPIHelper, job_id: str) -> dict:
        """
        Poll job status until completion or timeout

        Args:
            client: AnalyticDBAPIHelper instance
            job_id: Job ID to poll

        Returns:
            Final job response
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > TIMEOUT:
                raise RuntimeError(
                    f"Job polling timeout after {TIMEOUT / 60:.1f} minutes"
                )

            response = client.get_upload_document_job(
                knowledgebase=DRY_RUN_COLLECTION_NAME, jobid=job_id
            )

            job = response.get("Job", {})
            completed = job.get("Completed", False)
            status = job.get("Status", "")
            error = job.get("Error", "")

            logger.info(
                f"Job {job_id} status: {status}, completed: {completed}, "
                f"elapsed: {elapsed:.1f}s"
            )

            if completed:
                if error:
                    raise RuntimeError(f"Job failed with error: {error}")
                return response

            time.sleep(POLL_INTERVAL)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"AdbpgDocParser tool_parameters: {params}")

        fileurl = params.get("fileurl", "")

        with resolve_file_context(fileurl) as resolved:
            # Step 1: Ensure collection exists (ignore errors)
            self._ensure_collection_exists(client)

            # Step 2: Upload document with dry_run=True
            job_id = self._upload_document(
                client, params, resolved.local_path, resolved.remote_url
            )

            # Step 3: Poll for job completion
            job_response = self._poll_job(client, job_id)

            # Step 4: Download chunk file and parse
            chunk_result = job_response.get("ChunkResult", {})
            chunk_file_url = chunk_result.get("ChunkFileUrl")

            if not chunk_file_url:
                raise RuntimeError(
                    f"No PlainChunkFileUrl in job response: {job_response}"
                )

            chunks = self._download_chunk_file(chunk_file_url)

            logger.info(f"AdbpgDocParser returning {len(chunks)} chunks")

            # Return result as list[str]
            yield self.create_variable_message("result", chunks)
            yield self.create_text_message("\n".join(chunks))
