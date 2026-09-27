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

from TIPCommon.base.action.data_models import DataTable
from TIPCommon.transformation import construct_csv

from ..core.base_action import JevAction
from ..core.constants import LIST_MODELS_SCRIPT_NAME

if TYPE_CHECKING:
    from typing import NoReturn

    from ..core.data_models import Model


SUCCESS_MESSAGE: str = "Successfully listed {count} Jev model(s): {names}"
NO_MODELS_MESSAGE: str = "No Jev models are available for this API key."
ERROR_MESSAGE: str = 'Error executing action "List Models".'


class ListModels(JevAction):
    def __init__(self) -> None:
        super().__init__(LIST_MODELS_SCRIPT_NAME)
        self.error_output_message: str = ERROR_MESSAGE

    def _perform_action(self, _=None) -> None:
        models: list[Model] = self.api_client.list_models()
        self.json_results = {"models": [model.raw_data for model in models]}
        if not models:
            self.output_message = NO_MODELS_MESSAGE
            self.result_value = False
            return

        self.data_tables.append(
            DataTable(
                data_table=construct_csv([model.to_csv() for model in models]),
                title="Jev Models",
            )
        )
        self.output_message = SUCCESS_MESSAGE.format(
            count=len(models),
            names=", ".join(model.name for model in models),
        )


def main() -> NoReturn:
    ListModels().run()


if __name__ == "__main__":
    main()
