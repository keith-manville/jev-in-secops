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

from jev.actions import triage_alert
from jev.tests.common import CONFIG_PATH, MOCK_ALERT
from jev.tests.core.product import TypeSafe


@set_metadata(
    integration_config_file_path=CONFIG_PATH,
    parameters={"Additional Context": "WS-042 is a finance workstation.", "Max Events": "1"},
)
def test_triage_alert_success(action_output: MockActionOutput, typesafe: TypeSafe) -> None:
    typesafe.alert = MOCK_ALERT
    typesafe.choice_overrides = {"severity": "high", "recommended_action": "escalate"}

    triage_alert.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert action_output.results.result_value == "escalate"

    state = typesafe.last_payload["state"]
    assert state["alert_name"] == "SUSPICIOUS POWERSHELL EXECUTION"
    assert state["additional_context"] == "WS-042 is a finance workstation."
    assert len(state["events"]) == 1
    assert state["events"][0]["fields"]["CommandLine"] == "powershell.exe -enc SQBFAFgA"
    assert state["entities"] == [
        {"identifier": "WS-042", "type": "HOSTNAME", "is_internal": True, "is_suspicious": False}
    ]
    assert set(typesafe.last_payload["questions"]) == {
        "is_malicious",
        "severity",
        "recommended_action",
    }

    triage = action_output.results.json_output.json_result["triage"]
    assert triage["malicious_probability"] == 0.95
    assert triage["severity"] == "high"
    assert triage["recommended_action"] == "escalate"


@set_metadata(
    integration_config_file_path=CONFIG_PATH,
    parameters={
        "Custom Questions": json.dumps({
            "is_lateral_movement": {
                "type": "noul",
                "instructions": "Does this show lateral movement?",
            }
        }),
    },
)
def test_triage_alert_custom_questions(action_output: MockActionOutput, typesafe: TypeSafe) -> None:
    typesafe.alert = MOCK_ALERT

    triage_alert.main()

    assert action_output.results.execution_state == ExecutionState.COMPLETED
    assert "is_lateral_movement" in typesafe.last_payload["questions"]
    assert len(typesafe.last_payload["state"]["events"]) == 2
    answers = action_output.results.json_output.json_result["answers"]
    assert answers["is_lateral_movement"]["noul"] == 0.95
