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

import json

from integration_testing.platform.script_output import MockActionOutput
from integration_testing.set_meta import set_metadata
from TIPCommon.base.action import ExecutionState

from jev.actions import evaluate_questions
from jev.tests.common import CONFIG_PATH
from jev.tests.core.product import TypeSafe

QUESTIONS = {
    "is_phishing": {"type": "noul", "instructions": "Is this a phishing attempt?"},
    "category": {
        "type": "choice",
        "instructions": "What kind of message is this?",
        "criteria": {"phishing": None, "spam": None, "business": None},
    },
    "risk": {
        "type": "score",
        "instructions": "How risky is it?",
        "criteria": ["Low", "Medium", "High"],
    },
}


@set_metadata(
    integration_config_file_path=CONFIG_PATH,
    parameters={"State": "Reset your password now", "Questions": json.dumps(QUESTIONS)},
)
def test_evaluate_questions_success(action_output: MockActionOutput, typesafe: TypeSafe) -> None:
    evaluate_questions.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert typesafe.last_payload["questions"] == QUESTIONS
    json_result = action_output.results.json_output.json_result
    assert set(json_result["answers"]) == {"is_phishing", "category", "risk"}
    assert action_output.results.output_message == ("Jev answered 3 question(s): is_phishing, category, risk.")


@set_metadata(
    integration_config_file_path=CONFIG_PATH,
    parameters={
        "State": "Reset your password now",
        "Questions": json.dumps({"category": {"type": "choice", "instructions": "Kind?"}}),
    },
)
def test_evaluate_questions_choice_requires_criteria(
    action_output: MockActionOutput,
    typesafe: TypeSafe,
) -> None:
    evaluate_questions.main()

    assert action_output.results.execution_state == ExecutionState.FAILED
    assert typesafe.last_payload is None
