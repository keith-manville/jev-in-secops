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

from typing import Iterable

from integration_testing import router
from integration_testing.common import get_request_payload
from integration_testing.request import MockRequest
from integration_testing.requests.response import MockResponse
from integration_testing.requests.session import MockSession, Response, RouteFunction

from jev.tests.core.product import TypeSafe, TypeSafeHTTPError


class TypeSafeSession(MockSession[MockRequest, MockResponse, TypeSafe]):
    def get_routed_functions(self) -> Iterable[RouteFunction[Response]]:
        return [
            self.list_models,
            self.evaluate,
            self.get_alert_full_details,
        ]

    @router.get(r"/v1/models")
    def list_models(self, request: MockRequest) -> MockResponse:
        try:
            self._product.authenticate(request.headers)
            self._product.pop_failure()
            return MockResponse(content=self._product.list_models())
        except TypeSafeHTTPError as e:
            return MockResponse(content={"detail": e.detail}, status_code=e.status_code)

    @router.post(r"/v1/systemone")
    def evaluate(self, request: MockRequest) -> MockResponse:
        try:
            self._product.authenticate(request.headers)
            self._product.pop_failure()
            return MockResponse(content=self._product.evaluate(get_request_payload(request)))
        except TypeSafeHTTPError as e:
            return MockResponse(content={"detail": e.detail}, status_code=e.status_code)

    @router.post(r".*AlertFullDetails.*")
    def get_alert_full_details(self, _: MockRequest) -> MockResponse:
        return MockResponse(content=self._product.alert or {})
