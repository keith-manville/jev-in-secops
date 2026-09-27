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

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from jev.actions import ping
from jev.tests.common import CONFIG, CONFIG_PATH
from jev.tests.core.product import TypeSafe
from jev.tests.core.session import TypeSafeSession


class TestPing:
    @set_metadata(integration_config_file_path=CONFIG_PATH)
    def test_ping_success(
        self,
        script_session: TypeSafeSession,
        action_output: MockActionOutput,
    ) -> None:
        ping.main()

        assert len(script_session.request_history) == 1
        request = script_session.request_history[0].request
        assert request.url.path == "/v1/models"
        assert request.headers["Authorization"] == "Bearer test-api-key"
        assert action_output.results.output_message == (
            "Successfully connected to the TypeSafe API with the provided connection parameters!"
        )
        assert action_output.results.execution_state == ExecutionState.COMPLETED

    @set_metadata(integration_config={**CONFIG, "API Key": "wrong-key"})
    def test_ping_invalid_api_key(
        self,
        action_output: MockActionOutput,
    ) -> None:
        ping.main()

        assert action_output.results.execution_state == ExecutionState.FAILED
        assert action_output.results.result_value is False
        assert "https://console.typesafe.ai/" in action_output.results.output_message

    @set_metadata(integration_config_file_path=CONFIG_PATH)
    def test_ping_retries_when_rate_limited(
        self,
        script_session: TypeSafeSession,
        action_output: MockActionOutput,
        typesafe: TypeSafe,
    ) -> None:
        typesafe.failures = [429, 529]

        ping.main()

        assert len(script_session.request_history) == 3
        assert action_output.results.execution_state == ExecutionState.COMPLETED

    @set_metadata(integration_config_file_path=CONFIG_PATH)
    def test_ping_fails_after_max_retries(
        self,
        script_session: TypeSafeSession,
        action_output: MockActionOutput,
        typesafe: TypeSafe,
    ) -> None:
        typesafe.failures = [429, 429, 429, 429]

        ping.main()

        assert len(script_session.request_history) == 4
        assert action_output.results.execution_state == ExecutionState.FAILED
