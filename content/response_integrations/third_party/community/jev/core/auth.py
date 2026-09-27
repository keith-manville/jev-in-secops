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

from requests import Session
from soar_sdk.SiemplifyAction import SiemplifyAction
from soar_sdk.SiemplifyConnectors import SiemplifyConnectorExecution
from soar_sdk.SiemplifyJob import SiemplifyJob
from TIPCommon.base.interfaces import Authable
from TIPCommon.base.utils import CreateSession
from TIPCommon.extraction import extract_script_param
from TIPCommon.types import ChronicleSOAR

from .constants import DEFAULT_API_ROOT, DEFAULT_MODEL, DEFAULT_VERIFY_SSL, INTEGRATION_IDENTIFIER
from .data_models import IntegrationParameters
from .exceptions import JevError


@dataclasses.dataclass(slots=True)
class SessionAuthenticationParameters:
    api_key: str
    verify_ssl: bool


def build_auth_params(soar_sdk_object: ChronicleSOAR) -> IntegrationParameters:
    """Extract the integration configuration parameters.

    Args:
        soar_sdk_object: ChronicleSOAR SDK object

    Returns:
        IntegrationParameters: The integration configuration.
    """
    sdk_class = type(soar_sdk_object).__name__
    if sdk_class == SiemplifyAction.__name__:
        input_dictionary = soar_sdk_object.get_configuration(INTEGRATION_IDENTIFIER)
    elif sdk_class in (
        SiemplifyConnectorExecution.__name__,
        SiemplifyJob.__name__,
    ):
        input_dictionary = soar_sdk_object.parameters
    else:
        raise JevError(f"Provided SOAR instance is not supported! type: {sdk_class}.")

    api_root = extract_script_param(
        soar_sdk_object,
        input_dictionary=input_dictionary,
        param_name="API Root",
        default_value=DEFAULT_API_ROOT,
        is_mandatory=True,
        print_value=True,
    )
    api_key = extract_script_param(
        soar_sdk_object,
        input_dictionary=input_dictionary,
        param_name="API Key",
        is_mandatory=True,
        remove_whitespaces=True,
    )
    model = extract_script_param(
        soar_sdk_object,
        input_dictionary=input_dictionary,
        param_name="Default Model",
        default_value=DEFAULT_MODEL,
        print_value=True,
    )
    verify_ssl = extract_script_param(
        soar_sdk_object,
        input_dictionary=input_dictionary,
        param_name="Verify SSL",
        default_value=DEFAULT_VERIFY_SSL,
        input_type=bool,
        print_value=True,
    )

    return IntegrationParameters(
        api_root=api_root,
        api_key=api_key,
        model=model or DEFAULT_MODEL,
        verify_ssl=verify_ssl,
    )


class AuthenticatedSession(Authable):
    def authenticate_session(self, params: SessionAuthenticationParameters) -> None:
        self.session = get_authenticated_session(session_parameters=params)


def get_authenticated_session(session_parameters: SessionAuthenticationParameters) -> Session:
    """Get a session authenticated with the TypeSafe API key.

    Args:
        session_parameters: Session parameters.

    Returns:
        Session: Authenticated session object.
    """
    session: Session = CreateSession.create_session()
    session.verify = session_parameters.verify_ssl
    session.headers.update({
        "Authorization": f"Bearer {session_parameters.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return session
