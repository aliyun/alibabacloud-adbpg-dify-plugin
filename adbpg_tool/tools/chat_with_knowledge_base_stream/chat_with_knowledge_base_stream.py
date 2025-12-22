import json
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from tools.base import logger
from tools.base.api_helper import AnalyticDBAPIHelper, normalize_params


class ChatWithKnowledgeBaseStream(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        self.client = AnalyticDBAPIHelper(self.runtime.credentials)
        params = normalize_params(tool_parameters)
        logger.info(f"ChatWithKnowledgeBaseStream tool_parameters: {params}")

        chunks = self.client.chat_with_knowledge_base_stream(**params)
        thinking_started = False
        content_started = False

        for chunk in chunks:
            if (
                chunk.body.chat_completion
                and chunk.body.chat_completion.choices
                and len(chunk.body.chat_completion.choices) > 0
            ):
                choice = chunk.body.chat_completion.choices[0]

                if choice.message.reasoning_content:
                    if not thinking_started:
                        thinking_started = True
                        yield self.create_stream_variable_message(
                            "llm_answer", "\n<think>\n"
                        )

                    yield self.create_stream_variable_message(
                        "llm_answer", choice.message.reasoning_content
                    )

                if choice.message.content and len(choice.message.content) > 0:
                    if thinking_started and not content_started:
                        content_started = True
                        yield self.create_stream_variable_message(
                            "llm_answer", "\n</think>\n\n"
                        )

                    yield self.create_stream_variable_message(
                        "llm_answer", choice.message.content
                    )

        if thinking_started and not content_started:
            yield self.create_stream_variable_message("llm_answer", "\n</think>\n")

        logger.info(f"ChatWithKnowledgeBaseStream completed")
