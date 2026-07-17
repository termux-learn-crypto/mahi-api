import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestChatEngine:
    def setup_method(self):
        from chatbot.engine import ChatEngine
        self.engine = ChatEngine()

    def test_greeting(self):
        result = self.engine.chat("test_user", "Namaste")
        assert "response" in result
        assert result["intent"] == "greeting"
        assert len(result["response"]) > 0

    def test_calculator(self):
        result = self.engine.chat("test_user", "5 + 3 calculate karo")
        assert result["intent"] == "calculator"
        assert "8" in result["response"]

    def test_fact(self):
        result = self.engine.chat("test_user", "Fact sunao")
        assert result["intent"] == "daily_fact"
        assert len(result["response"]) > 0

    def test_quote(self):
        result = self.engine.chat("test_user", "Quote batao")
        assert result["intent"] == "quote"

    def test_name_meaning(self):
        result = self.engine.chat("test_user", "Vilas naam ka matlab kya hai?")
        assert result["intent"] == "name_meaning"
        assert "Vilas" in result["response"]

    def test_mobile_command(self):
        result = self.engine.chat("test_user", "YouTube kholo")
        assert result["intent"] == "mobile_command"
        assert "command" in result

    def test_emotion_detection(self):
        result = self.engine.chat("test_user", "Bahut khush hu aaj!")
        assert result["user_mood"] == "happy"

    def test_context_tracking(self):
        self.engine.chat("test_user", "Namaste")
        result = self.engine.chat("test_user", "Fact sunao")
        assert "context" in result

    def test_memory_system(self):
        self.engine.chat("test_user", "Mera naam Test hai")
        memory = self.engine.get_memory("test_user")
        assert "memories" in memory

    def test_unknown_intent(self):
        result = self.engine.chat("test_user", "asdfghjkl")
        assert result["intent"] in ("unknown", "confusion")


class TestMemory:
    def setup_method(self):
        from chatbot.memory import MemorySystem
        self.memory = MemorySystem()

    def test_add_memory(self):
        self.memory.add_memory("test_user", "short_term", "Test memory")
        memories = self.memory.get_memories("test_user")
        assert len(memories) > 0

    def test_preference(self):
        self.memory.set_preference("test_user", "theme", "dark")
        value = self.memory.get_preference("test_user", "theme")
        assert value == "dark"

    def test_personal_fact(self):
        self.memory.add_personal_fact("test_user", "User likes coffee")
        facts = self.memory.get_personal_facts("test_user")
        assert len(facts) > 0


class TestContextEngine:
    def setup_method(self):
        from chatbot.context_engine import ContextEngine
        self.context = ContextEngine()

    def test_update_context(self):
        self.context.update_context("test_user", "Namaste", "greeting")
        ctx = self.context.get_context("test_user")
        assert ctx["turn_count"] == 1

    def test_topic_detection(self):
        self.context.update_context("test_user", "Mujhe gym jaana hai", "health")
        ctx = self.context.get_context("test_user")
        assert ctx["current_topic"] == "health"


class TestPlugins:
    def setup_method(self):
        from chatbot.plugins import PluginManager
        self.manager = PluginManager()

    def test_list_plugins(self):
        from chatbot.plugins.weather import WeatherPlugin
        self.manager.register(WeatherPlugin())
        plugins = self.manager.list_plugins()
        assert len(plugins) == 1

    def test_find_plugin(self):
        from chatbot.plugins.notes import NotesPlugin
        self.manager.register(NotesPlugin())
        plugin = self.manager.find_plugin("notes", "note banao")
        assert plugin is not None


class TestAPI:
    def setup_method(self):
        from app import app
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_root(self):
        resp = self.client.get("/")
        data = json.loads(resp.data)
        assert data["status"] == "running"
        assert data["version"] == "2.0.0"

    def test_health(self):
        resp = self.client.get("/health")
        data = json.loads(resp.data)
        assert data["status"] == "ok"

    def test_chat(self):
        resp = self.client.post("/chat", json={
            "user_id": "test_api",
            "message": "Namaste",
        })
        data = json.loads(resp.data)
        assert "response" in data
        assert data["intent"] == "greeting"

    def test_chat_validation(self):
        resp = self.client.post("/chat", json={"message": "test"})
        assert resp.status_code == 400

    def test_history(self):
        resp = self.client.get("/history/test_api")
        data = json.loads(resp.data)
        assert "messages" in data

    def test_stats(self):
        resp = self.client.get("/stats/test_api")
        data = json.loads(resp.data)
        assert "user_id" in data

    def test_plugins(self):
        resp = self.client.get("/plugins")
        data = json.loads(resp.data)
        assert "plugins" in data

    def test_analytics(self):
        resp = self.client.get("/analytics")
        data = json.loads(resp.data)
        assert "total_events" in data
