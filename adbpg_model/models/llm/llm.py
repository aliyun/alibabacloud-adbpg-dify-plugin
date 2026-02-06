"""
AnalyticDB LLM Provider

This module implements the LLM provider for AnalyticDB PostgreSQL,
supporting chat completion with streaming.
"""

import sys
from collections.abc import Generator
from pathlib import Path
from typing import Optional, Union

from dify_plugin.entities.model.llm import (LLMMode, LLMResult, LLMResultChunk,
                                            LLMResultChunkDelta)
from dify_plugin.entities.model.message import (AssistantPromptMessage,
                                                PromptMessage,
                                                PromptMessageRole,
                                                PromptMessageTool,
                                                SystemPromptMessage,
                                                UserPromptMessage)
from dify_plugin.errors.model import (CredentialsValidateFailedError,
                                      InvokeAuthorizationError,
                                      InvokeBadRequestError,
                                      InvokeConnectionError, InvokeError,
                                      InvokeRateLimitError,
                                      InvokeServerUnavailableError)
from dify_plugin.interfaces.model.large_language_model import \
    LargeLanguageModel

# Add models directory to path
models_path = Path(__file__).parent.parent
sys.path.insert(0, str(models_path))

from api_helper import AnalyticDBModelAPIHelper, logger


class AdbpgLargeLanguageModel(LargeLanguageModel):
    """
    Large Language Model implementation for AnalyticDB PostgreSQL
    """

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        """
        Invoke large language model

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        :return: full response or stream response chunk generator result
        """
        return self._generate(
            model,
            credentials,
            prompt_messages,
            model_parameters,
            tools,
            stop,
            stream,
            user,
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        """
        Get number of tokens for given prompt messages

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param tools: tools for tool calling
        :return: number of tokens
        """
        # Use GPT-2 tokenizer for approximate token count
        prompt = self._convert_messages_to_prompt(prompt_messages)
        return self._get_num_tokens_by_gpt2(prompt)

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            self._generate(
                model=model,
                credentials=credentials,
                prompt_messages=[UserPromptMessage(content="ping")],
                model_parameters={"temperature": 0.5, "max_tokens": 10},
                stream=False,
            )
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    def _generate(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        """
        Invoke large language model

        :param model: model name
        :param credentials: credentials
        :param prompt_messages: prompt messages
        :param tools: tools for tool calling
        :param model_parameters: model parameters
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        :return: full response or stream response chunk generator result
        """
        api_helper = AnalyticDBModelAPIHelper(credentials)

        # Convert all prompt messages to API format for multi-turn conversation
        messages = self._convert_prompt_messages_to_api_messages(prompt_messages)

        # Prepare parameters for API
        # Note: repetition_penalty from model config is mapped to presence_penalty in API
        presence_penalty = model_parameters.get("repetition_penalty")

        params = {
            "messages": messages,
            "llm_model": model,
            "max_tokens": model_parameters.get("max_tokens"),
            "temperature": model_parameters.get("temperature"),
            "top_p": model_parameters.get("top_p"),
            "presence_penalty": presence_penalty,  # repetition_penalty -> presence_penalty
            "seed": model_parameters.get("seed"),
            "stop": stop,  # stop is supported by API
        }

        # Get streaming response with sliding window retry mechanism
        # If request is too long and rejected by gateway, gradually remove earlier messages
        # Keep at least the last 2 messages (user and assistant)
        retry_count = 0
        response = None
        last_exception = None
        
        while True:
            try:
                response = api_helper.chat_stream(**params)
                break  # Success, exit retry loop
            except Exception as ex:
                last_exception = ex
                # Check if messages can be reduced (must keep at least 2 messages)
                if len(params["messages"]) <= 2:
                    # Already at minimum, cannot reduce further, re-raise the exception
                    raise ex
                
                # Log the exception and attempt to reduce messages
                logger.warning(
                    f"Chat stream request failed (attempt {retry_count + 1}): {str(ex)}. "
                    f"Current message count: {len(params['messages'])}, "
                    f"attempting to reduce messages using sliding window."
                )
                
                # Remove messages from the beginning, keeping the last 2 messages
                # Calculate how many messages to remove (remove at least 1, but keep last 2)
                messages_to_keep = max(2, len(params["messages"]) - 1)
                params["messages"] = params["messages"][-messages_to_keep:]
                
                logger.info(
                    f"Reduced messages to {len(params['messages'])} (kept last {messages_to_keep} messages)"
                )
                
                retry_count += 1
        
        # If all retries failed and response is still None, raise the last exception
        if response is None and last_exception is not None:
            raise last_exception

        if stream:
            return self._handle_generate_stream_response(
                model, credentials, response, prompt_messages
            )
        else:
            return self._handle_generate_response(
                model, credentials, response, prompt_messages
            )

    def _handle_generate_response(
        self,
        model: str,
        credentials: dict,
        responses,
        prompt_messages: list[PromptMessage],
    ) -> LLMResult:
        """
        Handle llm non-streaming response

        :param model: model name
        :param credentials: credentials
        :param responses: response chunks
        :param prompt_messages: prompt messages
        :return: llm response
        """
        full_content = ""
        input_tokens = 0
        output_tokens = 0

        for chunk in responses:
            if (
                chunk.body.chat_completion
                and chunk.body.chat_completion.choices
                and len(chunk.body.chat_completion.choices) > 0
            ):
                choice = chunk.body.chat_completion.choices[0]
                if choice.message.content:
                    full_content += choice.message.content

                # Get usage info if available
                if chunk.body.chat_completion.usage:
                    usage = chunk.body.chat_completion.usage
                    if hasattr(usage, "input_tokens"):
                        input_tokens = usage.input_tokens or 0
                    if hasattr(usage, "output_tokens"):
                        output_tokens = usage.output_tokens or 0

        assistant_prompt_message = AssistantPromptMessage(content=full_content)
        usage = self._calc_response_usage(
            model, credentials, input_tokens, output_tokens
        )

        result = LLMResult(
            model=model,
            message=assistant_prompt_message,
            prompt_messages=prompt_messages,
            usage=usage,
        )
        return result

    def _handle_generate_stream_response(
        self,
        model: str,
        credentials: dict,
        responses,
        prompt_messages: list[PromptMessage],
    ) -> Generator:
        """
        Handle llm stream response

        :param model: model name
        :param credentials: credentials
        :param responses: response chunks
        :param prompt_messages: prompt messages
        :return: llm response chunk generator result
        """
        index = 0
        thinking_started = False
        content_started = False

        for chunk in responses:
            if (
                chunk.body.chat_completion
                and chunk.body.chat_completion.choices
                and len(chunk.body.chat_completion.choices) > 0
            ):
                choice = chunk.body.chat_completion.choices[0]

                # Handle reasoning content (thinking mode)
                if choice.message.reasoning_content:
                    if not thinking_started:
                        thinking_started = True
                        yield LLMResultChunk(
                            model=model,
                            prompt_messages=prompt_messages,
                            delta=LLMResultChunkDelta(
                                index=index,
                                message=AssistantPromptMessage(content="<think>\n"),
                            ),
                        )
                        index += 1

                    yield LLMResultChunk(
                        model=model,
                        prompt_messages=prompt_messages,
                        delta=LLMResultChunkDelta(
                            index=index,
                            message=AssistantPromptMessage(
                                content=choice.message.reasoning_content
                            ),
                        ),
                    )
                    index += 1

                # Handle regular content
                if choice.message.content and len(choice.message.content) > 0:
                    if thinking_started and not content_started:
                        content_started = True
                        yield LLMResultChunk(
                            model=model,
                            prompt_messages=prompt_messages,
                            delta=LLMResultChunkDelta(
                                index=index,
                                message=AssistantPromptMessage(
                                    content="\n</think>\n\n"
                                ),
                            ),
                        )
                        index += 1

                    yield LLMResultChunk(
                        model=model,
                        prompt_messages=prompt_messages,
                        delta=LLMResultChunkDelta(
                            index=index,
                            message=AssistantPromptMessage(
                                content=choice.message.content
                            ),
                        ),
                    )
                    index += 1

                # Handle finish reason
                if choice.finish_reason and choice.finish_reason != "null":
                    if thinking_started and not content_started:
                        # Close thinking tag if we never started content
                        yield LLMResultChunk(
                            model=model,
                            prompt_messages=prompt_messages,
                            delta=LLMResultChunkDelta(
                                index=index,
                                message=AssistantPromptMessage(content="\n</think>"),
                            ),
                        )
                        index += 1

                    # Get usage info
                    usage = None
                    if chunk.body.chat_completion.usage:
                        usage_data = chunk.body.chat_completion.usage
                        input_tokens = getattr(usage_data, "input_tokens", 0) or 0
                        output_tokens = getattr(usage_data, "output_tokens", 0) or 0
                        usage = self._calc_response_usage(
                            model, credentials, input_tokens, output_tokens
                        )

                    yield LLMResultChunk(
                        model=model,
                        prompt_messages=prompt_messages,
                        delta=LLMResultChunkDelta(
                            index=index,
                            message=AssistantPromptMessage(content=""),
                            finish_reason=choice.finish_reason,
                            usage=usage,
                        ),
                    )

    def _convert_messages_to_prompt(self, messages: list[PromptMessage]) -> str:
        """
        Convert messages to a single prompt string for token counting

        :param messages: List of PromptMessage to combine.
        :return: Combined string prompt
        """
        prompt_parts = []
        for message in messages:
            if isinstance(message, SystemPromptMessage):
                prompt_parts.append(f"System: {message.content}")
            elif isinstance(message, UserPromptMessage):
                if isinstance(message.content, str):
                    prompt_parts.append(f"User: {message.content}")
                else:
                    prompt_parts.append(f"User: {str(message.content)}")
            elif isinstance(message, AssistantPromptMessage):
                prompt_parts.append(f"Assistant: {message.content}")

        return "\n".join(prompt_parts)

    def _convert_prompt_messages_to_api_messages(
        self, prompt_messages: list[PromptMessage]
    ) -> list[dict]:
        """
        Convert prompt messages to API message format for multi-turn conversation

        :param prompt_messages: List of PromptMessage to convert
        :return: List of message dicts with role and content
        """
        api_messages = []
        logger.info(f"Converting prompt messages to API messages: {prompt_messages}")

        for message in prompt_messages:
            if isinstance(message, SystemPromptMessage):
                api_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, UserPromptMessage):
                # Handle both string and complex content
                if isinstance(message.content, str):
                    content = message.content
                else:
                    # For complex content, extract text parts
                    # This is a simplified version - may need enhancement for multimodal
                    content = str(message.content)

                api_messages.append({"role": "user", "content": content})
            elif isinstance(message, AssistantPromptMessage):
                api_messages.append(
                    {"role": "assistant", "content": message.content or ""}
                )

        return api_messages

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        """
        Map model invoke error to unified error
        """
        return {
            InvokeConnectionError: [],
            InvokeServerUnavailableError: [],
            InvokeRateLimitError: [],
            InvokeAuthorizationError: [],
            InvokeBadRequestError: [],
        }
