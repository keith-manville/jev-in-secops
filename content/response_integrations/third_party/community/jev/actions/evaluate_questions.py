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
from ..core.constants import EVALUATE_QUESTIONS_SCRIPT_NAME
from ..core.exceptions import JevInvalidParameterError
from ..core.utils import parse_questions, parse_state

if TYPE_CHECKING:
    from typing import NoReturn


SUCCESS_MESSAGE: str = "Jev answered {count} question(s): {keys}."
ERROR_MESSAGE: str = 'Error executing action "Evaluate Questions".'


class EvaluateQuestions(JevAction):
    def __init__(self) -> None:
        super().__init__(EVALUATE_QUESTIONS_SCRIPT_NAME)
        self.error_output_message: str = ERROR_MESSAGE

    def _extract_action_parameters(self) -> None:
        self.params.state = extract_action_param(
            self.soar_action, param_name="State", is_mandatory=True, remove_whitespaces=False
        )
        self.params.questions = extract_action_param(
            self.soar_action, param_name="Questions", is_mandatory=True, print_value=True
        )
        self._extract_model_param()

    def _validate_params(self) -> None:
        if not self.params.state.strip():
            raise JevInvalidParameterError('"State" must not be empty.')
        self.params.parsed_questions = parse_questions(self.params.questions)

    def _perform_action(self, _=None) -> None:
        evaluation = self._evaluate(
            parse_state(self.params.state),
            self.params.parsed_questions,
        )
        self.json_results = evaluation.json()
        self.output_message = SUCCESS_MESSAGE.format(
            count=len(evaluation.answers),
            keys=", ".join(evaluation.answers),
        )


def main() -> NoReturn:
    EvaluateQuestions().run()


if __name__ == "__main__":
    main()
