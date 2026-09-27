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
from typing import TYPE_CHECKING, Any

from .constants import (
    MAX_ALERT_STATE_CHARS,
    MAX_CHOICE_OPTIONS,
    MAX_SCORE_LEVELS,
    MIN_SCORE_LEVELS,
    QuestionTypeEnum,
)
from .exceptions import JevInvalidParameterError

if TYPE_CHECKING:
    from soar_sdk.SiemplifyDataModel import Alert
    from TIPCommon.types import SingleJson


def parse_state(state: str) -> Any:
    """Turn the "State" parameter into a Jev state.

    JSON objects and arrays are sent as structured data, which Jev handles better
    than a flattened string. Anything else is sent as plain text.
    """
    stripped = state.strip()
    if stripped[:1] in ("{", "["):
        try:
            return json.loads(stripped)
        except ValueError:
            pass
    return state


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_choice_options(options: str) -> SingleJson:
    """Parse the "Options" parameter into a Jev choice criteria map.

    Accepts a JSON object of option to description, a JSON array of options,
    or a comma-separated list of options.
    """
    parsed: Any = None
    stripped = options.strip()
    if stripped[:1] in ("{", "["):
        try:
            parsed = json.loads(stripped)
        except ValueError as e:
            raise JevInvalidParameterError(f'"Options" is not valid JSON: {e}') from e

    if isinstance(parsed, dict):
        criteria = {str(key).strip(): value for key, value in parsed.items()}
    elif isinstance(parsed, list):
        criteria = {str(option).strip(): None for option in parsed}
    else:
        criteria = {option: None for option in _split_csv(stripped)}

    criteria.pop("", None)
    if len(criteria) < 2:
        raise JevInvalidParameterError('"Options" must contain at least 2 options.')
    if len(criteria) > MAX_CHOICE_OPTIONS:
        raise JevInvalidParameterError(f'"Options" can contain at most {MAX_CHOICE_OPTIONS} options.')
    return criteria


def parse_score_levels(levels: str) -> list[Any]:
    """Parse the "Levels" parameter into an ordered list of level descriptions.

    Accepts a JSON array or a comma-separated list, lowest level first.
    """
    parsed: Any = None
    stripped = levels.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
        except ValueError as e:
            raise JevInvalidParameterError(f'"Levels" is not valid JSON: {e}') from e

    result = parsed if isinstance(parsed, list) else _split_csv(stripped)
    if not MIN_SCORE_LEVELS <= len(result) <= MAX_SCORE_LEVELS:
        raise JevInvalidParameterError(
            f'"Levels" must contain between {MIN_SCORE_LEVELS} and {MAX_SCORE_LEVELS} levels.'
        )
    return result


def parse_questions(questions: str) -> SingleJson:
    """Parse and sanity check a JSON map of question id to Jev question."""
    try:
        parsed = json.loads(questions)
    except ValueError as e:
        raise JevInvalidParameterError(f'"Questions" is not valid JSON: {e}') from e

    if not isinstance(parsed, dict) or not parsed:
        raise JevInvalidParameterError(
            '"Questions" must be a non-empty JSON object that maps a question id to a question.'
        )

    valid_types = {question_type.value for question_type in QuestionTypeEnum}
    for key, question in parsed.items():
        if not isinstance(question, dict):
            raise JevInvalidParameterError(f'Question "{key}" must be a JSON object.')
        if question.get("type") not in valid_types:
            raise JevInvalidParameterError(
                f'Question "{key}" has an invalid "type". Use one of: {", ".join(sorted(valid_types))}.'
            )
        if not question.get("instructions"):
            raise JevInvalidParameterError(f'Question "{key}" is missing "instructions".')
        if question["type"] != QuestionTypeEnum.NOUL.value and not question.get("criteria"):
            raise JevInvalidParameterError(f'Question "{key}" of type "{question["type"]}" requires "criteria".')
    return parsed


def _compact(data: SingleJson) -> SingleJson:
    """Drop empty values so the state stays small and focused."""
    return {key: value for key, value in data.items() if value not in (None, "", [], {})}


def build_alert_state(
    alert: Alert,
    max_events: int,
    additional_context: str | None = None,
) -> SingleJson:
    """Build a structured Jev state that describes a Google SecOps alert.

    Args:
        alert: The current alert.
        max_events: Maximum number of security events to include.
        additional_context: Optional free text added to the state, such as
            enrichment results from previous playbook steps.

    Returns:
        SingleJson: The alert as a JSON object, truncated to fit Jev's context.
    """
    events = [
        _compact({
            "name": event.name,
            "description": event.description,
            "product": event.device_product,
            "event_type": event.event_type,
            "rule_generator": event.rule_generator,
            "fields": _compact(dict(event.additional_properties or {})),
        })
        for event in (alert.security_events or [])[:max_events]
    ]
    entities = [
        _compact({
            "identifier": entity.identifier,
            "type": entity.entity_type,
            "is_internal": entity.is_internal,
            "is_suspicious": entity.is_suspicious,
        })
        for entity in alert.entities or []
    ]
    state: SingleJson = _compact({
        "alert_name": alert.name,
        "description": alert.description,
        "rule_generator": alert.rule_generator,
        "product": alert.reporting_product,
        "vendor": alert.reporting_vendor,
        "severity": alert.severity,
        "entities": entities,
        "events": events,
        "additional_context": additional_context,
    })

    # Drop events from the end until the state fits in Jev's context window.
    while len(json.dumps(state, default=str)) > MAX_ALERT_STATE_CHARS and state.get("events"):
        state["events"] = state["events"][:-1]
    return json.loads(json.dumps(state, default=str))
