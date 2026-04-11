import json
import os
import pytest
from config.config_manager import load_font_config, save_font_config
from config.constants import DEFAULT_FONT_SIZES


class TestConfigManager:
    def test_load_defaults_no_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("config.config_manager.CONFIG_FILE", str(tmp_path / "nonexistent.json"))
        config = load_font_config()
        assert config == DEFAULT_FONT_SIZES

    def test_load_from_file(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "config.json")
        with open(config_path, 'w') as f:
            json.dump({"button_font_size": 50, "table_font_size": 60, "input_font_size": 70}, f)
        monkeypatch.setattr("config.config_manager.CONFIG_FILE", config_path)
        config = load_font_config()
        assert config["button_font_size"] == 50
        assert config["table_font_size"] == 60
        assert config["input_font_size"] == 70

    def test_save_and_load(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "config.json")
        monkeypatch.setattr("config.config_manager.CONFIG_FILE", config_path)
        save_font_config(30, 40, 50)
        config = load_font_config()
        assert config["button_font_size"] == 30
        assert config["table_font_size"] == 40
        assert config["input_font_size"] == 50

    def test_load_corrupt_file(self, tmp_path, monkeypatch):
        config_path = str(tmp_path / "config.json")
        with open(config_path, 'w') as f:
            f.write("not valid json{{{")
        monkeypatch.setattr("config.config_manager.CONFIG_FILE", config_path)
        config = load_font_config()
        assert config == DEFAULT_FONT_SIZES
