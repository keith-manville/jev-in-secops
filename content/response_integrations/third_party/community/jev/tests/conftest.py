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

import pytest
from integration_testing.common import use_live_api
from soar_sdk.SiemplifyBase import SiemplifyBase
from TIPCommon.base.utils import CreateSession

from jev.tests.core.product import TypeSafe
from jev.tests.core.session import TypeSafeSession

pytest_plugins = ("integration_testing.conftest",)


@pytest.fixture
def typesafe() -> TypeSafe:
    return TypeSafe()


@pytest.fixture(autouse=True)
def script_session(monkeypatch: pytest.MonkeyPatch, typesafe: TypeSafe) -> TypeSafeSession:
    """Mock the scripts' session and get back an object to view request history."""
    session: TypeSafeSession = TypeSafeSession(typesafe)

    if not use_live_api():
        monkeypatch.setattr(CreateSession, "create_session", lambda: session)
        monkeypatch.setattr("requests.Session", lambda: session)
        monkeypatch.setattr("jev.core.api_client.time.sleep", lambda _: None)

    return session


@pytest.fixture(autouse=True)
def sdk_session(monkeypatch: pytest.MonkeyPatch, typesafe: TypeSafe) -> TypeSafeSession:
    """Mock the SDK sessions and get it back to view request and response history."""
    session: TypeSafeSession = TypeSafeSession(typesafe)

    if not use_live_api():
        monkeypatch.setattr(SiemplifyBase, "create_session", lambda *_: session)

    return session
