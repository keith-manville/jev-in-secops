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

from jev.actions import ask_choice_question
from jev.tests.common import CONFIG_PATH
from jev.tests.core.product import TypeSafe

PARAMETERS: dict[str, str] = {
    "State": "Your mailbox is full, log in here to keep receiving email.",
    "Question": "What kind of email is this?",
    "Options": "phishing, spam, benign",
}


@set_metadata(integration_config_file_path=CONFIG_PATH, parameters=PARAMETERS)
def test_ask_choice_question_csv_options(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    ask_choice_question.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value == "phishing"
    assert typesafe.last_payload["questions"]["answer"]["criteria"] == {
        "phishing": None,
        "spam": None,
        "benign": None,
    }


@set_metadata(
    integration_config_file_path=CONFIG_PATH,
    parameters={
        **PARAMETERS,
        "Options": '{"phishing": "Credential theft", "benign": "Legitimate email"}',
    },
)
def test_ask_choice_question_json_options(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    typesafe.choice_overrides = {"answer": "benign"}

    ask_choice_question.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value == "benign"
    assert typesafe.last_payload["questions"]["answer"]["criteria"] == {
        "phishing": "Credential theft",
        "benign": "Legitimate email",
    }
    assert action_output.results.json_output.json_result["decision"]["choice"] == "benign"


@set_metadata(integration_config_file_path=CONFIG_PATH, parameters={**PARAMETERS, "Options": "one"})
def test_ask_choice_question_needs_two_options(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    ask_choice_question.main()

    assert action_output.results.execution_state == ExecutionState.FAILED
    assert typesafe.last_payload is None
