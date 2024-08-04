import abc

from flask import request, url_for
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import Optional, List, Dict, Union
from src.model.entity.Variable import Variable
from src.model.enum.VariableType import VariableType
from src.model.enum.VariableUnit import VariableUnit
from src.model.enum.HookType import HookType
from src.model.hook.HookRegistration import HookRegistration
from src.model.hook.StaticHookRegistration import StaticHookRegistration
from src.model.hook.FunctionalHookRegistration import FunctionalHookRegistration
from src.service.ModelStore import ModelStore
from src.service.TemplateRenderer import TemplateRenderer
from src.constant.WebDirConstant import WebDirConstant


class ObPlugin(abc.ABC):

    PLUGIN_PREFIX = "plugin_"

    def __init__(self, kernel, plugin_dir: str, model_store: ModelStore, template_renderer: TemplateRenderer):
        self._kernel = kernel
        self._plugin_dir = plugin_dir
        self._model_store = model_store
        self._template_renderer = template_renderer
        self._rendering_env = template_renderer.init_rendering_env(self._plugin_dir)

    @abc.abstractmethod
    def use_id(self) -> str:
        pass

    @abc.abstractmethod
    def use_title(self) -> str:
        pass

    @abc.abstractmethod
    def use_description(self) -> str:
        pass

    @abc.abstractmethod
    def use_variables(self) -> List[Variable]:
        pass

    @abc.abstractmethod
    def use_hooks_registrations(self) -> List[HookRegistration]:
        pass

    @abc.abstractmethod
    def get_version(self) -> str:
        pass

    def get_directory(self) -> Optional[str]:
        return self._plugin_dir

    def get_rendering_env(self) -> Environment:
        return self._rendering_env

    def get_plugin_variable_prefix(self) -> str:
        return "{}{}".format(self.PLUGIN_PREFIX, self.use_id())

    def get_plugin_variable_name(self, name: str) -> str:
        return "{}_{}".format(self.get_plugin_variable_prefix(), name)

    def get_plugin_static_src_dir(self) -> str:
        return "{}/{}".format(self._plugin_dir, WebDirConstant.FOLDER_PLUGIN_STATIC_SRC)

    def add_variable(self, name: str, value='', section: str = '', type: VariableType = VariableType.STRING, editable: bool = True, description: str = '', description_edition: str = '', selectables: Optional[Dict[str, str]] = None, unit: Optional[VariableUnit] = None, refresh_player: bool = False) -> Variable:
        return self._model_store.variable().set_variable(
            name=self.get_plugin_variable_name(name),
            section=section,
            value=value,
            type=type,
            editable=editable,
            description=description,
            description_edition=description_edition,
            unit=unit,
            refresh_player=refresh_player,
            selectables=selectables if isinstance(selectables, dict) else None,
            plugin=self.use_id(),
        )

    def add_static_hook_registration(self, hook: HookType, priority: int = 0) -> StaticHookRegistration:
        return StaticHookRegistration(plugin=self, hook=hook, priority=priority)

    def add_functional_hook_registration(self, hook: HookType, priority: int = 0, function=None) -> FunctionalHookRegistration:
        return FunctionalHookRegistration(plugin=self, hook=hook, priority=priority, function=function)

    def translate(self, token, resolve=False) -> Union[Dict, str]:
        token = token if token.startswith(self.use_id()) else "{}_{}".format(self.use_id(), token)
        return self._model_store.lang().translate(token) if resolve else token

    def render_view(self, template_file: str, **parameters: dict) -> str:
        return self._template_renderer.render_view(template_file, self, **parameters)
