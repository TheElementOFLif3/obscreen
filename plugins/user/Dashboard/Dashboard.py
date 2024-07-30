from src.interface.ObPlugin import ObPlugin

from typing import List, Dict
from src.model.entity.Variable import Variable
from src.model.enum.HookType import HookType
from src.model.hook.HookRegistration import HookRegistration


class Dashboard(ObPlugin):

    def use_id(self):
        return 'dashboard'

    def use_title(self):
        return self.translate('plugin_title')

    def use_description(self):
        return self.translate('plugin_description')

    def use_variables(self) -> List[Variable]:
        return []

    def use_hooks_registrations(self) -> List[HookRegistration]:
        return [
            super().add_functional_hook_registration(hook=HookType.H_ROOT_NAV_ELEMENT_START, priority=10, function=self.hook_navigation),
        ]

    def hook_navigation(self) -> str:
        return self.render_view('@hook_navigation.jinja.html')
