import os
import tempfile
import unittest
from unittest.mock import patch

from config import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_env_accounts_take_precedence_over_config_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as config_file:
            config_file.write(
                '{"accounts":[{"site_url":"https://file.example","username":"file-user",'
                '"password":"file-pass","site_name":"file"}]}'
            )
            config_path = config_file.name

        try:
            env = {
                "ACCOUNT_1": "https://env.example|env-user|env-pass|env",
                "EMAIL_RECEIVERS": "receiver@example.com",
            }
            with patch.dict(os.environ, env, clear=True):
                config = ConfigManager(config_path).config

            self.assertEqual(len(config.accounts), 1)
            self.assertEqual(config.accounts[0].site_url, "https://env.example")
            self.assertEqual(config.accounts[0].username, "env-user")
            self.assertEqual(config.accounts[0].password, "env-pass")
            self.assertEqual(config.accounts[0].site_name, "env")
        finally:
            os.unlink(config_path)

    def test_env_account_value_allows_variable_name_prefix(self):
        env = {
            "ACCOUNT_1": "ACCOUNT_1 = https://ccgfw.top|user@example.com|password|ccgfw",
        }
        with patch.dict(os.environ, env, clear=True):
            config = ConfigManager("missing-config.json").config

        self.assertEqual(config.accounts[0].site_url, "https://www.ccgfw.top")
        self.assertEqual(config.accounts[0].username, "user@example.com")

    def test_clean_account_url_prefixes_www_for_ccgfw_entry_domain(self):
        manager = ConfigManager.__new__(ConfigManager)

        cleaned = manager._clean_account_url("ACCOUNT_1=https://ccgfw.top")

        self.assertEqual(cleaned, "https://www.ccgfw.top")

    def test_clean_account_url_keeps_existing_www_domain(self):
        manager = ConfigManager.__new__(ConfigManager)

        cleaned = manager._clean_account_url("https://www.ccgfw.top")

        self.assertEqual(cleaned, "https://www.ccgfw.top")


if __name__ == "__main__":
    unittest.main()
