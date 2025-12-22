import time
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params

# Poll interval in seconds
POLL_INTERVAL = 3
# Timeout in seconds (30 minutes)
TIMEOUT = 30 * 60


class GetUploadDocumentJob(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"GetUploadDocumentJob tool_parameters: {params}")

        wait_until_finish = params.pop("wait_until_finish", False)
        knowledgebase = params.get("knowledgebase")
        jobid = params.get("jobid")

        if wait_until_finish:
            response = self._poll_until_finish(knowledgebase, jobid)
        else:
            response = self.client.get_upload_document_job(**params)

        logger.info(f"GetUploadDocumentJob response: {response}")
        for key, value in response.items():
            yield self.create_variable_message(key, value)
        yield self.create_json_message(response)

    def _poll_until_finish(self, knowledgebase: str, jobid: str) -> dict:
        """
        Poll job status until completion or timeout

        Args:
            knowledgebase: Document collection name
            jobid: Job ID to poll

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

            response = self.client.get_upload_document_job(
                knowledgebase=knowledgebase, jobid=jobid
            )

            job = response.get("Job", {})
            completed = job.get("Completed", False)
            status = job.get("Status", "")
            error = job.get("Error", "")

            logger.info(
                f"Job {jobid} status: {status}, completed: {completed}, "
                f"elapsed: {elapsed:.1f}s"
            )

            if completed or error:
                return response

            time.sleep(POLL_INTERVAL)
