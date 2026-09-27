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

from typing import TYPE_CHECKING
from urllib.parse import urljoin

import requests

from .constants import CONSOLE_URL, ENDPOINTS
from .exceptions import (
    JevAuthenticationError,
    JevHTTPError,
    JevRateLimitError,
    JevValidationError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_full_url(
    api_root: str,
    endpoint_id: str,
    endpoints: Mapping[str, str] | None = None,
    **kwargs,
) -> str:
    """Construct the full URL using a URL identifier and optional variables.

    Args:
        api_root: The root of the API endpoint
        endpoint_id: The identifier for the specific URL
        endpoints: endpoints dictionary object
        kwargs: Variables passed for string formatting

    Returns:
        str: The full URL constructed from API root, endpoint identifier and variables
    """
    endpoints = endpoints or ENDPOINTS
    return urljoin(api_root.rstrip("/") + "/", endpoints[endpoint_id].format(**kwargs).lstrip("/"))


def _error_details(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text or response.reason or ""
    if isinstance(body, dict):
        for key in ("detail", "error", "message"):
            if body.get(key):
                return str(body[key])
    return str(body)


def validate_response(
    response: requests.Response,
    error_msg: str = "An error occurred",
) -> None:
    """Raise a meaningful integration exception if the response is an error.

    Args:
        response: Response to validate
        error_msg: Default message to display on error

    Raises:
        JevAuthenticationError: 401, missing or invalid API key
        JevValidationError: 422, the request body failed validation
        JevRateLimitError: 429 or 529, rate limited or overloaded
        JevHTTPError: Any other HTTP error
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        status_code = response.status_code
        details = _error_details(response)

        if status_code in (401, 403):
            raise JevAuthenticationError(
                f"{error_msg}: the TypeSafe API key is missing or invalid ({status_code}). "
                f"Sign in at {CONSOLE_URL} to create or copy a valid API key. "
                f"Details: {details}",
                status_code=status_code,
            ) from error

        if status_code == 422:
            raise JevValidationError(
                f"{error_msg}: the request was rejected by TypeSafe validation. Details: {details}",
                status_code=status_code,
            ) from error

        if status_code in (429, 529):
            raise JevRateLimitError(
                f"{error_msg}: TypeSafe is rate limiting or overloaded ({status_code}). "
                f"Try again later. Details: {details}",
                status_code=status_code,
            ) from error

        raise JevHTTPError(
            f"{error_msg}: {error}. Details: {details}",
            status_code=status_code,
        ) from error
