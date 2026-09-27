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

import copy
from typing import TYPE_CHECKING

from TIPCommon.extraction import extract_action_param
from TIPCommon.validation import ParameterValidator

from ..core.base_action import JevAction
from ..core.constants import (
    DEFAULT_MAX_EVENTS,
    TRIAGE_ACTION_KEY,
    TRIAGE_ALERT_SCRIPT_NAME,
    TRIAGE_MALICIOUS_KEY,
    TRIAGE_QUESTIONS,
    TRIAGE_SEVERITY_KEY,
)
from ..core.exceptions import JevError
from ..core.utils import build_alert_state, parse_questions

if TYPE_CHECKING:
    from typing import NoReturn

    from TIPCommon.types import SingleJson


SUCCESS_MESSAGE: str = (
    'Jev triaged alert "{alert}": malicious probability {malicious:.4f}, '
    'severity "{severity}", recommended action "{action}".'
)
ERROR_MESSAGE: str = 'Error executing action "Triage Alert".'


class TriageAlert(JevAction):
    def __init__(self) -> None:
        super().__init__(TRIAGE_ALERT_SCRIPT_NAME)
        self.error_output_message: str = ERROR_MESSAGE

    def _extract_action_parameters(self) -> None:
        self.params.additional_context = extract_action_param(
            self.soar_action, param_name="Additional Context", remove_whitespaces=False
        )
        self.params.custom_questions = extract_action_param(
            self.soar_action, param_name="Custom Questions", print_value=True
        )
        self.params.max_events = extract_action_param(
            self.soar_action,
            param_name="Max Events",
            default_value=str(DEFAULT_MAX_EVENTS),
            print_value=True,
        )
        self._extract_model_param()

    def _validate_params(self) -> None:
        validator = ParameterValidator(self.soar_action)
        self.params.max_events = validator.validate_non_negative(
            param_name="Max Events",
            value=self.params.max_events,
            print_value=True,
        )
        self.params.questions = copy.deepcopy(dict(TRIAGE_QUESTIONS))
        if self.params.custom_questions:
            self.params.questions.update(parse_questions(self.params.custom_questions))

    def _perform_action(self, _=None) -> None:
        alert = self.soar_action.current_alert
        if alert is None:
            raise JevError("Could not load the current alert. Run this action from an alert.")

        state: SingleJson = build_alert_state(
            alert,
            max_events=self.params.max_events,
            additional_context=self.params.additional_context,
        )
        evaluation = self._evaluate(state, self.params.questions)
        answers = evaluation.answers

        summary: SingleJson = {
            "alert_name": alert.name,
            "alert_identifier": alert.identifier,
        }
        malicious = answers.get(TRIAGE_MALICIOUS_KEY)
        severity = answers.get(TRIAGE_SEVERITY_KEY)
        action = answers.get(TRIAGE_ACTION_KEY)
        if malicious is not None:
            summary["malicious_probability"] = malicious.value
        if severity is not None:
            summary["severity"] = severity.value
            summary["severity_confidence"] = severity.confidence
        if action is not None:
            summary["recommended_action"] = action.value
            summary["recommended_action_confidence"] = action.confidence

        self.json_results = {**evaluation.json(), "triage": summary}
        self.result_value = str(action.value) if action is not None else True
        self.output_message = SUCCESS_MESSAGE.format(
            alert=alert.name,
            malicious=float(malicious.value) if malicious is not None else 0.0,
            severity=severity.value if severity is not None else "N/A",
            action=action.value if action is not None else "N/A",
        )


def main() -> NoReturn:
    TriageAlert().run()


if __name__ == "__main__":
    main()
