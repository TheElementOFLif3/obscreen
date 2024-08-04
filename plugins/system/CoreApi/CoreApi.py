from src.interface.ObPlugin import ObPlugin

from typing import List, Dict
from src.model.entity.Variable import Variable
from src.model.enum.HookType import HookType
from src.model.hook.HookRegistration import HookRegistration


class CoreApi(ObPlugin):

    def get_version(self) -> str:
        return '1.0'

    def use_id(self):
        return 'core_api'

    def use_title(self):
        return self.translate('plugin_title')

    def use_description(self):
        return self.translate('plugin_description')

    def use_variables(self) -> List[Variable]:
        return []

    def use_hooks_registrations(self) -> List[HookRegistration]:
        return []
