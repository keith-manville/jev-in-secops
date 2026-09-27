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

import pytest

from jev.core.exceptions import JevInvalidParameterError
from jev.core.utils import (
    parse_choice_options,
    parse_questions,
    parse_score_levels,
    parse_state,
)


def test_parse_state_plain_text() -> None:
    assert parse_state("hello") == "hello"
    assert parse_state("{not json") == "{not json"


def test_parse_state_json() -> None:
    assert parse_state(' {"a": 1} ') == {"a": 1}
    assert parse_state("[1, 2]") == [1, 2]


def test_parse_choice_options_variants() -> None:
    assert parse_choice_options("a, b ,c") == {"a": None, "b": None, "c": None}
    assert parse_choice_options('["a", "b"]') == {"a": None, "b": None}
    assert parse_choice_options('{"a": "A", "b": null}') == {"a": "A", "b": None}


def test_parse_choice_options_invalid() -> None:
    with pytest.raises(JevInvalidParameterError):
        parse_choice_options("only")
    with pytest.raises(JevInvalidParameterError):
        parse_choice_options("{bad json")


def test_parse_score_levels() -> None:
    assert parse_score_levels("low, high") == ["low", "high"]
    assert parse_score_levels('["low", {"level": "high"}]') == ["low", {"level": "high"}]
    with pytest.raises(JevInvalidParameterError):
        parse_score_levels(",".join(str(i) for i in range(11)))


def test_parse_questions_invalid_type() -> None:
    with pytest.raises(JevInvalidParameterError):
        parse_questions('{"q": {"type": "bogus", "instructions": "x"}}')
    with pytest.raises(JevInvalidParameterError):
        parse_questions("[]")
