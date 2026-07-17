from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        self.commands = []
        self.keywords = []

    @abstractmethod
    def can_handle(self, intent: str, message: str) -> bool:
        pass

    @abstractmethod
    def execute(self, user_id: str, message: str, context: dict) -> dict:
        pass

    def get_help(self) -> str:
        return f"{self.name}: {self.description}"

    def get_commands(self) -> list[str]:
        return self.commands

    def get_keywords(self) -> list[str]:
        return self.keywords


class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.intent_map = {}

    def register(self, plugin: Plugin):
        self.plugins[plugin.name] = plugin

    def unregister(self, name: str):
        if name in self.plugins:
            del self.plugins[name]

    def get_plugin(self, name: str) -> Plugin | None:
        return self.plugins.get(name)

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "enabled": p.enabled,
                "commands": p.commands,
            }
            for p in self.plugins.values()
        ]

    def find_plugin(self, intent: str, message: str) -> Plugin | None:
        for plugin in self.plugins.values():
            if plugin.enabled and plugin.can_handle(intent, message):
                return plugin
        return None

    def execute(self, name: str, user_id: str, message: str, context: dict) -> dict | None:
        plugin = self.plugins.get(name)
        if plugin and plugin.enabled:
            return plugin.execute(user_id, message, context)
        return None

    def execute_by_intent(self, intent: str, user_id: str, message: str, context: dict) -> dict | None:
        plugin = self.find_plugin(intent, message)
        if plugin:
            return plugin.execute(user_id, message, context)
        return None
