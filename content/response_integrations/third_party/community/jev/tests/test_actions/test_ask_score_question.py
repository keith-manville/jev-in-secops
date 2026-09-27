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

from jev.actions import ask_score_question
from jev.tests.common import CONFIG_PATH
from jev.tests.core.product import TypeSafe

PARAMETERS: dict[str, str] = {
    "State": "Sign-in from a new country 10 minutes after a sign-in from the office.",
    "Question": "How risky is this sign-in?",
    "Levels": "No risk, Low risk, Medium risk, High risk",
}


@set_metadata(integration_config_file_path=CONFIG_PATH, parameters=PARAMETERS)
def test_ask_score_question_success(action_output: MockActionOutput, typesafe: TypeSafe) -> None:
    typesafe.score_value = 2.6

    ask_score_question.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value == 2.6
    assert typesafe.last_payload["questions"]["answer"]["criteria"] == [
        "No risk",
        "Low risk",
        "Medium risk",
        "High risk",
    ]
    decision = action_output.results.json_output.json_result["decision"]
    assert decision["closest_level"] == 3
    assert decision["closest_level_description"] == "High risk"


@set_metadata(integration_config_file_path=CONFIG_PATH, parameters={**PARAMETERS, "Levels": "Only"})
def test_ask_score_question_needs_two_levels(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    ask_score_question.main()

    assert action_output.results.execution_state == ExecutionState.FAILED
    assert typesafe.last_payload is None
