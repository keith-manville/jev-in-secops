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

from ..core.base_action import JevAction
from ..core.constants import (
    ASK_CHOICE_QUESTION_SCRIPT_NAME,
    DEFAULT_QUESTION_KEY,
    QuestionTypeEnum,
)
from ..core.exceptions import JevInvalidParameterError
from ..core.utils import parse_choice_options, parse_state

if TYPE_CHECKING:
    from typing import NoReturn


SUCCESS_MESSAGE: str = 'Jev chose "{choice}" with a confidence of {confidence:.4f}.'
ERROR_MESSAGE: str = 'Error executing action "Ask Choice Question".'


class AskChoiceQuestion(JevAction):
    def __init__(self) -> None:
        super().__init__(ASK_CHOICE_QUESTION_SCRIPT_NAME)
        self.error_output_message: str = ERROR_MESSAGE

    def _extract_action_parameters(self) -> None:
        self.params.state = extract_action_param(
            self.soar_action, param_name="State", is_mandatory=True, remove_whitespaces=False
        )
        self.params.question = extract_action_param(
            self.soar_action, param_name="Question", is_mandatory=True, print_value=True
        )
        self.params.options = extract_action_param(
            self.soar_action, param_name="Options", is_mandatory=True, print_value=True
        )
        self._extract_model_param()

    def _validate_params(self) -> None:
        if not self.params.state.strip():
            raise JevInvalidParameterError('"State" must not be empty.')
        self.params.criteria = parse_choice_options(self.params.options)

    def _perform_action(self, _=None) -> None:
        evaluation = self._evaluate(
            parse_state(self.params.state),
            {
                DEFAULT_QUESTION_KEY: {
                    "type": QuestionTypeEnum.CHOICE.value,
                    "instructions": self.params.question,
                    "criteria": self.params.criteria,
                }
            },
        )
        answer = evaluation.answers[DEFAULT_QUESTION_KEY]
        choice = str(answer.value)

        self.json_results = {
            **evaluation.json(),
            "decision": {
                "choice": choice,
                "confidence": answer.confidence,
                "probabilities": answer.probabilities,
            },
        }
        self.result_value = choice
        self.output_message = SUCCESS_MESSAGE.format(
            choice=choice,
            confidence=answer.confidence or 0.0,
        )


def main() -> NoReturn:
    AskChoiceQuestion().run()


if __name__ == "__main__":
    main()
