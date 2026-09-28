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

from abc import ABC
from typing import TYPE_CHECKING, Any

from TIPCommon.base.action import Action
from TIPCommon.base.action.data_models import DataTable
from TIPCommon.extraction import extract_action_param
from TIPCommon.transformation import construct_csv

from .api_client import ApiParameters, JevApiClient
from .auth import AuthenticatedSession, SessionAuthenticationParameters, build_auth_params
from .exceptions import JevError, JevInvalidParameterError

if TYPE_CHECKING:
    import requests

    from .data_models import Evaluation


class JevAction(Action, ABC):
    """Base class for Jev actions."""

    def _init_api_clients(self) -> JevApiClient:
        """Prepare the API client."""
        auth_params = build_auth_params(self.soar_action)
        authenticator: AuthenticatedSession = AuthenticatedSession()
        authenticator.authenticate_session(
            SessionAuthenticationParameters(
                api_key=auth_params.api_key,
                verify_ssl=auth_params.verify_ssl,
            )
        )
        authenticated_session: requests.Session = authenticator.session

        return JevApiClient(
            authenticated_session=authenticated_session,
            configuration=ApiParameters(
                api_root=auth_params.api_root,
                model=auth_params.model,
            ),
            logger=self.logger,
        )

    def _extract_model_param(self) -> None:
        """Extract the optional per-action "Model" override."""
        self.params.model = extract_action_param(
            self.soar_action,
            param_name="Model",
            print_value=True,
        )

    @staticmethod
    def _require_params(**values: Any) -> None:
        """Fail cleanly when a required parameter is empty.

        Required parameters are extracted as optional and checked here instead,
        because TIPCommon raises extraction errors before its error handling
        starts, which surfaces in SecOps as an unhelpful script crash. A value
        can also be empty at runtime when a placeholder resolves to nothing.
        """
        for name, value in values.items():
            if value is None or not str(value).strip():
                raise JevInvalidParameterError(
                    f'"{name.replace("_", " ").title()}" is empty. Provide a value, and if you '
                    "used a placeholder, check that it exists in this alert."
                )

    @property
    def result_value(self) -> Any:
        return self._result_value

    @result_value.setter
    def result_value(self, value: Any) -> None:
        # The TIPCommon base only accepts booleans. Jev actions return the decision
        # itself (yes/no, chosen option or score) so playbooks can branch on it.
        self._result_value = value

    def _evaluate(self, state: Any, questions: dict) -> Evaluation:
        """Run a Jev evaluation and render the answers to the case wall."""
        self.logger.info(f"Evaluating {len(questions)} question(s) with Jev")
        evaluation: Evaluation = self.api_client.evaluate(
            state=state,
            questions=questions,
            model=self.params.model,
        )
        self.logger.info(f"Jev model {evaluation.model} returned {len(evaluation.answers)} answer(s)")
        missing = set(questions) - set(evaluation.answers)
        if missing:
            raise JevError(f"Jev did not return answers for: {', '.join(sorted(missing))}")

        self.data_tables.append(
            DataTable(
                data_table=construct_csv(evaluation.to_csv()),
                title="Jev Answers",
            )
        )
        return evaluation
