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

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


# Integration Identifiers
INTEGRATION_IDENTIFIER: str = "Jev"
INTEGRATION_DISPLAY_NAME: str = "Jev"

# Script Identifiers
PING_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - Ping"
LIST_MODELS_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - List Models"
ASK_YES_NO_QUESTION_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - Ask Yes No Question"
ASK_CHOICE_QUESTION_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - Ask Choice Question"
ASK_SCORE_QUESTION_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - Ask Score Question"
EVALUATE_QUESTIONS_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - Evaluate Questions"
TRIAGE_ALERT_SCRIPT_NAME: str = f"{INTEGRATION_IDENTIFIER} - Triage Alert"

# Default Configuration Parameter Values
DEFAULT_API_ROOT: str = "https://api.typesafe.ai"
DEFAULT_MODEL: str = "jev-latest"
DEFAULT_VERIFY_SSL: bool = True

# Where users sign up and create API keys
CONSOLE_URL: str = "https://console.typesafe.ai/"

# API Constants
ENDPOINTS: Mapping[str, str] = {
    "models": "/v1/models",
    "evaluate": "/v1/systemone",
}

# Requests
REQUEST_TIMEOUT: int = 60
RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 529})
MAX_RETRIES: int = 3
RETRY_BACKOFF_BASE_SEC: float = 2.0
MAX_RETRY_AFTER_SEC: float = 30.0

# API limits, see https://docs.typesafe.ai/api
MAX_CHOICE_OPTIONS: int = 255
MIN_SCORE_LEVELS: int = 2
MAX_SCORE_LEVELS: int = 10

# Jev accepts 32k tokens for the state plus the longest question. Keep the
# serialized alert state well under that so the questions still fit.
MAX_ALERT_STATE_CHARS: int = 60_000
DEFAULT_MAX_EVENTS: int = 10

# Default question keys
DEFAULT_QUESTION_KEY: str = "answer"


class QuestionTypeEnum(str, Enum):
    NOUL = "noul"
    CHOICE = "choice"
    SCORE = "score"


# Triage Alert default questions
TRIAGE_MALICIOUS_KEY: str = "is_malicious"
TRIAGE_SEVERITY_KEY: str = "severity"
TRIAGE_ACTION_KEY: str = "recommended_action"

TRIAGE_QUESTIONS: Mapping[str, dict] = {
    TRIAGE_MALICIOUS_KEY: {
        "type": QuestionTypeEnum.NOUL.value,
        "instructions": (
            "Does this security alert describe genuinely malicious or unauthorized "
            "activity (a true positive), rather than benign, expected or test activity?"
        ),
        "criteria": {
            "true": "True positive: real malicious or unauthorized activity",
            "false": "False positive or benign: expected, authorized or test activity",
        },
    },
    TRIAGE_SEVERITY_KEY: {
        "type": QuestionTypeEnum.CHOICE.value,
        "instructions": ("How severe is the potential impact of this alert to the organization?"),
        "criteria": {
            "critical": "Active compromise, data exfiltration or ransomware in progress",
            "high": "Likely compromise of a user, host or credential that needs fast action",
            "medium": "Suspicious activity that needs investigation but no confirmed impact",
            "low": "Minor policy violation or low-risk suspicious activity",
            "informational": "No security impact, informational only",
        },
    },
    TRIAGE_ACTION_KEY: {
        "type": QuestionTypeEnum.CHOICE.value,
        "instructions": "What should the SOC analyst do next with this alert?",
        "criteria": {
            "close": "Close the alert as benign or false positive",
            "investigate": "Investigate further before deciding",
            "escalate": "Escalate to incident response or a senior analyst",
            "contain": "Take containment action immediately (isolate host, disable user)",
        },
    },
}
