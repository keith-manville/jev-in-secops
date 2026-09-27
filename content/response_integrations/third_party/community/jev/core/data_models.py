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
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from TIPCommon.types import SingleJson


class IntegrationParameters(NamedTuple):
    api_root: str
    api_key: str
    model: str
    verify_ssl: bool


@dataclasses.dataclass(frozen=True, slots=True)
class Answer:
    """A single Jev answer, keyed by the question id chosen by the caller."""

    key: str
    type: str
    raw_data: SingleJson

    @classmethod
    def from_json(cls, key: str, raw_data: SingleJson) -> Answer:
        return cls(key=key, type=raw_data.get("type", ""), raw_data=raw_data)

    @property
    def value(self) -> Any:
        """The headline value: noul probability, chosen option or score."""
        return self.raw_data.get(self.type)

    @property
    def confidence(self) -> float | None:
        return self.raw_data.get("confidence")

    @property
    def probabilities(self) -> SingleJson:
        return self.raw_data.get("probabilities") or {}

    def to_csv_row(self) -> SingleJson:
        value = self.value
        if isinstance(value, float):
            value = round(value, 4)
        confidence = self.confidence
        return {
            "Question": self.key,
            "Type": self.type,
            "Answer": value,
            "Confidence": round(confidence, 4) if confidence is not None else "N/A",
        }


@dataclasses.dataclass(frozen=True, slots=True)
class Evaluation:
    """Response of POST /v1/systemone."""

    model: str
    answers: dict[str, Answer]
    usage: SingleJson
    raw_data: SingleJson

    @classmethod
    def from_json(cls, raw_data: SingleJson) -> Evaluation:
        return cls(
            model=raw_data.get("model", ""),
            answers={key: Answer.from_json(key, answer) for key, answer in (raw_data.get("answers") or {}).items()},
            usage=raw_data.get("usage") or {},
            raw_data=raw_data,
        )

    def json(self) -> SingleJson:
        return self.raw_data

    def to_csv(self) -> list[SingleJson]:
        return [answer.to_csv_row() for answer in self.answers.values()]


@dataclasses.dataclass(frozen=True, slots=True)
class Model:
    """An entry of GET /v1/models."""

    name: str
    description: str
    release_date: str
    raw_data: SingleJson

    @classmethod
    def from_json(cls, raw_data: SingleJson) -> Model:
        return cls(
            name=raw_data.get("name", ""),
            description=raw_data.get("description", ""),
            release_date=raw_data.get("release_date", ""),
            raw_data=raw_data,
        )

    def to_csv(self) -> SingleJson:
        return {
            "Name": self.name,
            "Description": self.description,
            "Release Date": self.release_date,
        }
