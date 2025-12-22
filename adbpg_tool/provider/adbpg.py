from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from tools.base.api_helper import AnalyticDBAPIHelper


class AdbpgProvider(ToolProvider):

    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            api_helper = AnalyticDBAPIHelper(credentials)
            api_helper.init()
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
