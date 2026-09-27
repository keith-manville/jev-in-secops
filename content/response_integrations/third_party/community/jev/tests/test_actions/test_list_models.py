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

from jev.actions import list_models
from jev.tests.common import CONFIG_PATH
from jev.tests.core.product import TypeSafe


@set_metadata(integration_config_file_path=CONFIG_PATH)
def test_list_models_success(action_output: MockActionOutput) -> None:
    list_models.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.output_message == ("Successfully listed 2 Jev model(s): jev-latest, jev-preview")
    assert [m["name"] for m in action_output.results.json_output.json_result["models"]] == [
        "jev-latest",
        "jev-preview",
    ]


@set_metadata(integration_config_file_path=CONFIG_PATH)
def test_list_models_empty(action_output: MockActionOutput, typesafe: TypeSafe) -> None:
    typesafe.models = []

    list_models.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value is False
