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

from jev.actions import ask_yes_no_question
from jev.tests.common import CONFIG_PATH
from jev.tests.core.product import TypeSafe

PARAMETERS: dict[str, str] = {
    "State": "Help! My payouts have been failing for 3 days.",
    "Question": "Does this convey urgency?",
    "Yes Criteria": "Explicitly time-sensitive",
    "Threshold": "0.9",
}


@set_metadata(integration_config_file_path=CONFIG_PATH, parameters=PARAMETERS)
def test_ask_yes_no_question_yes(action_output: MockActionOutput, typesafe: TypeSafe) -> None:
    ask_yes_no_question.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value is True
    payload = typesafe.last_payload
    assert payload["model"] == "jev-latest"
    assert payload["state"] == PARAMETERS["State"]
    assert payload["questions"] == {
        "answer": {
            "type": "noul",
            "instructions": "Does this convey urgency?",
            "criteria": {"true": "Explicitly time-sensitive"},
        }
    }
    decision = action_output.results.json_output.json_result["decision"]
    assert decision == {"probability": 0.95, "threshold": 0.9, "is_yes": True}


@set_metadata(
    integration_config_file_path=CONFIG_PATH,
    parameters={**PARAMETERS, "State": '{"subject": "hi", "body": "lunch?"}', "Model": "jev-1.13.0"},
)
def test_ask_yes_no_question_no_with_json_state(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    typesafe.noul_value = 0.2

    ask_yes_no_question.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value is False
    assert typesafe.last_payload["state"] == {"subject": "hi", "body": "lunch?"}
    assert typesafe.last_payload["model"] == "jev-1.13.0"


@set_metadata(integration_config_file_path=CONFIG_PATH, parameters={**PARAMETERS, "Threshold": "2"})
def test_ask_yes_no_question_invalid_threshold(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    ask_yes_no_question.main()

    assert action_output.results.execution_state == ExecutionState.FAILED
    assert typesafe.last_payload is None
