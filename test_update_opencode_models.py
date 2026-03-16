import unittest
from unittest.mock import patch

import update_opencode_models


class UpdateOpencodeConfigTest(unittest.TestCase):
    def test_existing_model_parameters_are_preserved_when_models_are_refreshed(self):
        existing_config = {
            "provider": {
                update_opencode_models.PROVIDER_ID: {
                    "name": "LM Studio",
                    "npm": "@ai-sdk/openai-compatible",
                    "models": {
                        "model-a": {
                            "name": "Old Name",
                            "tool_call": False,
                            "temperature": 0.2,
                            "cost": {"input": 123, "output": 456},
                            "limit": {"context": 1111, "output": 2222},
                            "custom_parameter": "keep"
                        }
                    },
                    "options": {
                        "baseURL": "http://old"
                    },
                    "env": ["OLD_ENV"]
                }
            }
        }
        models_data = [
            {
                "id": "model-a",
                "name": "New Name",
                "context_length": 9999,
                "max_tokens": 8888,
                "tool_call": True,
                "temperature": True
            },
            {
                "id": "model-b",
                "name": "Model B"
            }
        ]

        with patch("update_opencode_models.load_opencode_config", return_value=existing_config), \
             patch("update_opencode_models.os.makedirs"), \
             patch("builtins.open"), \
             patch("update_opencode_models.json.dump") as dump_mock:
            result = update_opencode_models.update_opencode_config(models_data, "http://new")

        self.assertTrue(result)
        written_config = dump_mock.call_args[0][0]
        provider = written_config["provider"][update_opencode_models.PROVIDER_ID]

        self.assertEqual(provider["models"]["model-a"]["name"], "New Name")
        self.assertFalse(provider["models"]["model-a"]["tool_call"])
        self.assertEqual(provider["models"]["model-a"]["temperature"], 0.2)
        self.assertEqual(provider["models"]["model-a"]["cost"], {"input": 123, "output": 456})
        self.assertEqual(provider["models"]["model-a"]["limit"], {"context": 1111, "output": 2222})
        self.assertEqual(provider["models"]["model-a"]["custom_parameter"], "keep")
        self.assertIn("model-b", provider["models"])


if __name__ == "__main__":
    unittest.main()
