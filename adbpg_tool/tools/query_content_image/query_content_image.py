import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger, resolve_file_context
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params


class QueryContentImage(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"QueryContentImage tool_parameters: {params}")

        file_url = params.get("file_url", "")

        with resolve_file_context(file_url) as resolved:
            if resolved.local_path:
                # Use advance API for local/downloaded files
                local_params = params.copy()
                local_params.pop("file_url", None)
                local_params["file_path"] = resolved.local_path
                response = self.client.query_content_image_advance(**local_params)
            else:
                # Use URL API for remote URLs
                response = self.client.query_content_image(**params)

            logger.info(f"QueryContentImage response: {response}")

            for key, value in response.items():
                yield self.create_variable_message(key, value)
            yield self.create_json_message(response)
