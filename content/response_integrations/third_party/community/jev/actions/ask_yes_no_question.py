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

from typing import TYPE_CHECKING

from TIPCommon.extraction import extract_action_param
from TIPCommon.validation import ParameterValidator

from ..core.base_action import JevAction
from ..core.constants import (
    ASK_YES_NO_QUESTION_SCRIPT_NAME,
    DEFAULT_QUESTION_KEY,
    QuestionTypeEnum,
)
from ..core.exceptions import JevInvalidParameterError
from ..core.utils import parse_state

if TYPE_CHECKING:
    from typing import NoReturn

    from TIPCommon.types import SingleJson


DEFAULT_THRESHOLD: float = 0.5

SUCCESS_MESSAGE: str = 'Jev answered "{answer}" with a yes probability of {probability:.4f} (threshold {threshold}).'
ERROR_MESSAGE: str = 'Error executing action "Ask Yes No Question".'


class AskYesNoQuestion(JevAction):
    def __init__(self) -> None:
        super().__init__(ASK_YES_NO_QUESTION_SCRIPT_NAME)
        self.error_output_message: str = ERROR_MESSAGE

    def _extract_action_parameters(self) -> None:
        self.params.state = extract_action_param(self.soar_action, param_name="State", remove_whitespaces=False)
        self.params.question = extract_action_param(self.soar_action, param_name="Question", print_value=True)
        self.params.yes_criteria = extract_action_param(self.soar_action, param_name="Yes Criteria", print_value=True)
        self.params.no_criteria = extract_action_param(self.soar_action, param_name="No Criteria", print_value=True)
        self.params.threshold = extract_action_param(
            self.soar_action,
            param_name="Threshold",
            default_value=str(DEFAULT_THRESHOLD),
            print_value=True,
        )
        self._extract_model_param()

    def _validate_params(self) -> None:
        self._require_params(State=self.params.state, Question=self.params.question)
        validator = ParameterValidator(self.soar_action)
        self.params.threshold = validator.validate_float(
            param_name="Threshold",
            value=self.params.threshold,
            print_value=True,
        )
        if not 0 <= self.params.threshold <= 1:
            raise JevInvalidParameterError('"Threshold" must be a number between 0 and 1.')

    def _perform_action(self, _=None) -> None:
        question: SingleJson = {
            "type": QuestionTypeEnum.NOUL.value,
            "instructions": self.params.question,
        }
        criteria = {
            key: value
            for key, value in (
                ("true", self.params.yes_criteria),
                ("false", self.params.no_criteria),
            )
            if value
        }
        if criteria:
            question["criteria"] = criteria

        evaluation = self._evaluate(
            parse_state(self.params.state),
            {DEFAULT_QUESTION_KEY: question},
        )
        probability = float(evaluation.answers[DEFAULT_QUESTION_KEY].value)
        is_yes = probability >= self.params.threshold

        self.json_results = {
            **evaluation.json(),
            "decision": {
                "probability": probability,
                "threshold": self.params.threshold,
                "is_yes": is_yes,
            },
        }
        self.result_value = is_yes
        self.output_message = SUCCESS_MESSAGE.format(
            answer="yes" if is_yes else "no",
            probability=probability,
            threshold=self.params.threshold,
        )


def main() -> NoReturn:
    AskYesNoQuestion().run()


if __name__ == "__main__":
    main()
