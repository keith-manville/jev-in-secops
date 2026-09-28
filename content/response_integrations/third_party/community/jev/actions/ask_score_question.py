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
    ASK_SCORE_QUESTION_SCRIPT_NAME,
    DEFAULT_QUESTION_KEY,
    QuestionTypeEnum,
)
from ..core.utils import parse_score_levels, parse_state

if TYPE_CHECKING:
    from typing import NoReturn


SUCCESS_MESSAGE: str = (
    'Jev scored {score:.4f} on a scale of 0 to {max_level} (closest level: "{level}") '
    "with a confidence of {confidence:.4f}."
)
ERROR_MESSAGE: str = 'Error executing action "Ask Score Question".'


class AskScoreQuestion(JevAction):
    def __init__(self) -> None:
        super().__init__(ASK_SCORE_QUESTION_SCRIPT_NAME)
        self.error_output_message: str = ERROR_MESSAGE

    def _extract_action_parameters(self) -> None:
        self.params.state = extract_action_param(self.soar_action, param_name="State", remove_whitespaces=False)
        self.params.question = extract_action_param(self.soar_action, param_name="Question", print_value=True)
        self.params.levels = extract_action_param(self.soar_action, param_name="Levels", print_value=True)
        self._extract_model_param()

    def _validate_params(self) -> None:
        self._require_params(State=self.params.state, Question=self.params.question, Levels=self.params.levels)
        self.params.criteria = parse_score_levels(self.params.levels)

    def _perform_action(self, _=None) -> None:
        evaluation = self._evaluate(
            parse_state(self.params.state),
            {
                DEFAULT_QUESTION_KEY: {
                    "type": QuestionTypeEnum.SCORE.value,
                    "instructions": self.params.question,
                    "criteria": self.params.criteria,
                }
            },
        )
        answer = evaluation.answers[DEFAULT_QUESTION_KEY]
        score = float(answer.value)
        legend = answer.raw_data.get("legend") or {}
        max_level = len(self.params.criteria) - 1
        closest = min(max(round(score), 0), max_level)
        level = legend.get(str(closest), str(self.params.criteria[closest]))

        self.json_results = {
            **evaluation.json(),
            "decision": {
                "score": score,
                "closest_level": closest,
                "closest_level_description": level,
                "confidence": answer.confidence,
            },
        }
        self.result_value = round(score, 4)
        self.output_message = SUCCESS_MESSAGE.format(
            score=score,
            max_level=max_level,
            level=level,
            confidence=answer.confidence or 0.0,
        )


def main() -> NoReturn:
    AskScoreQuestion().run()


if __name__ == "__main__":
    main()
