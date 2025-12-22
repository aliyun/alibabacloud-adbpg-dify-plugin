from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger, resolve_file_context
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params


class UploadDocumentAsync(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"UploadDocumentAsync tool_parameters: {params}")

        fileurl = params.get("fileurl", "")

        with resolve_file_context(fileurl) as resolved:
            if resolved.local_path:
                # Use advance API for local/downloaded files
                local_params = params.copy()
                local_params.pop("fileurl", None)
                local_params["file_path"] = resolved.local_path
                response = self.client.upload_document_async_advance(**local_params)
            else:
                # Use URL API for remote URLs
                response = self.client.upload_document_async(**params)

            logger.info(f"UploadDocumentAsync response: {response}")

            for key, value in response.items():
                yield self.create_variable_message(key, value)
            yield self.create_json_message(response)
