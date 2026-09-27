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

import dataclasses
from typing import Any

from TIPCommon.types import SingleJson

VALID_API_KEY: str = "test-api-key"
RESOLVED_MODEL: str = "jev-1.13.0"


class TypeSafeHTTPError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclasses.dataclass(slots=True)
class TypeSafe:
    """A tiny in-memory stand-in for the TypeSafe System One API."""

    api_key: str = VALID_API_KEY
    models: list[SingleJson] = dataclasses.field(
        default_factory=lambda: [
            {
                "name": "jev-latest",
                "description": "The most recent stable, official release.",
                "release_date": "2026-06-01",
            },
            {
                "name": "jev-preview",
                "description": "The most recent release, whether or not it is official.",
                "release_date": "2026-06-01",
            },
        ]
    )
    noul_value: float = 0.95
    choice_overrides: dict[str, str] = dataclasses.field(default_factory=dict)
    score_value: float | None = None
    failures: list[int] = dataclasses.field(default_factory=list)
    last_payload: SingleJson | None = None
    alert: SingleJson | None = None

    def authenticate(self, headers: SingleJson) -> None:
        if headers.get("Authorization") != f"Bearer {self.api_key}":
            raise TypeSafeHTTPError(401, "Invalid API key")

    def pop_failure(self) -> None:
        if self.failures:
            raise TypeSafeHTTPError(self.failures.pop(0), "Too many requests")

    def list_models(self) -> SingleJson:
        return {"models": self.models}

    def evaluate(self, payload: SingleJson) -> SingleJson:
        self.last_payload = payload
        for field in ("state", "model", "questions"):
            if field not in payload:
                raise TypeSafeHTTPError(422, f"Missing field: {field}")

        answers = {key: self._answer(key, question) for key, question in payload["questions"].items()}
        return {
            "model": RESOLVED_MODEL,
            "answers": answers,
            "usage": {"input_tokens": 300, "output_tokens": 20 * len(answers)},
        }

    def _answer(self, key: str, question: SingleJson) -> SingleJson:
        match question["type"]:
            case "noul":
                return {"type": "noul", "noul": self.noul_value}
            case "choice":
                options: list[str] = list(question["criteria"])
                chosen = self.choice_overrides.get(key, options[0])
                rest = (1 - 0.8) / max(len(options) - 1, 1)
                probabilities = {o: (0.8 if o == chosen else rest) for o in options}
                return {
                    "type": "choice",
                    "choice": chosen,
                    "probabilities": probabilities,
                    "confidence": 0.75,
                }
            case "score":
                levels: list[Any] = question["criteria"]
                score = self.score_value if self.score_value is not None else len(levels) / 2
                return {
                    "type": "score",
                    "score": score,
                    "legend": {str(i): str(level) for i, level in enumerate(levels)},
                    "probabilities": {str(i): 1 / len(levels) for i in range(len(levels))},
                    "confidence": 0.6,
                }
            case _:
                raise TypeSafeHTTPError(422, f"Unknown question type for {key}")
