# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, NamedTuple

from TIPCommon.base.interfaces import Apiable

from .api_utils import get_full_url, validate_response
from .constants import (
    MAX_RETRIES,
    MAX_RETRY_AFTER_SEC,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF_BASE_SEC,
    RETRYABLE_STATUS_CODES,
)
from .data_models import Evaluation, Model

if TYPE_CHECKING:
    from requests import Response, Session
    from TIPCommon.base.interfaces.logger import ScriptLogger
    from TIPCommon.types import SingleJson


class ApiParameters(NamedTuple):
    api_root: str
    model: str


class JevApiClient(Apiable):
    """Client for the TypeSafe System One API that serves the Jev models."""

    def __init__(
        self,
        authenticated_session: Session,
        configuration: ApiParameters,
        logger: ScriptLogger,
    ) -> None:
        super().__init__(
            authenticated_session=authenticated_session,
            configuration=configuration,
        )
        self.logger: ScriptLogger = logger
        self.api_root: str = configuration.api_root
        self.model: str = configuration.model

    def test_connectivity(self) -> None:
        """Test connectivity and API key validity by listing the account's models."""
        self.list_models()

    def list_models(self) -> list[Model]:
        """List the model names and aliases the account can use.

        Returns:
            list[Model]: The available models.
        """
        response: Response = self._request("GET", get_full_url(self.api_root, "models"))
        validate_response(response, "Failed to list Jev models")
        return [Model.from_json(model) for model in response.json().get("models", [])]

    def evaluate(
        self,
        state: Any,
        questions: SingleJson,
        model: str | None = None,
    ) -> Evaluation:
        """Evaluate a state against a map of typed questions.

        Args:
            state: The content to evaluate. A string, object or array.
            questions: Map of question id to a noul, choice or score question.
            model: Model name. Defaults to the integration's default model.

        Returns:
            Evaluation: One answer per question, keyed by the question ids.
        """
        payload: SingleJson = {
            "state": state,
            "model": model or self.model,
            "questions": questions,
        }
        response: Response = self._request(
            "POST",
            get_full_url(self.api_root, "evaluate"),
            json=payload,
        )
        validate_response(response, "Failed to evaluate questions with Jev")
        return Evaluation.from_json(response.json())

    def _request(self, method: str, url: str, **kwargs) -> Response:
        """Send a request, retrying with exponential backoff on 429 and 529.

        The TypeSafe API asks clients to back off and retry when rate limited
        (429) or overloaded (529), honoring the `retry-after` header when present.
        """
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        attempt = 0
        while True:
            response: Response = self.session.request(method, url, **kwargs)
            if response.status_code not in RETRYABLE_STATUS_CODES or attempt >= MAX_RETRIES:
                return response

            delay = self._retry_delay(response, attempt)
            attempt += 1
            self.logger.info(
                f"TypeSafe returned {response.status_code}, retrying in {delay:.1f}s (attempt {attempt}/{MAX_RETRIES})"
            )
            time.sleep(delay)

    @staticmethod
    def _retry_delay(response: Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return min(float(retry_after), MAX_RETRY_AFTER_SEC)
            except ValueError:
                pass
        return min(RETRY_BACKOFF_BASE_SEC * (2**attempt), MAX_RETRY_AFTER_SEC)
