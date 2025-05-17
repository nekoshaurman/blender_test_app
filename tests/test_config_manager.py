import json
import unittest
from unittest.mock import patch, mock_open, MagicMock
import logging
from managers.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        # Disable logging during tests to avoid clutter
        logging.getLogger('ConfigManager').setLevel(logging.CRITICAL)
        # Reset any singleton state by patching the module
        self.patcher = patch('managers.config_manager.config_manager', None)
        self.patcher.start()

    def tearDown(self):
        # Stop the patcher to clean up
        self.patcher.stop()

    def test_init_valid_file_path(self):
        # Arrange
        file_path = "config.json"
        mock_config = {"work_directory": "C:\\work"}
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data='{"work_directory": "C:\\work"}')), \
                patch("json.load", return_value=mock_config):
            # Act
            config_manager = ConfigManager(file_path)

            # Assert
            self.assertEqual(config_manager.file_path, file_path)
            self.assertEqual(config_manager._variables, mock_config)

    def test_init_invalid_file_path_type(self):
        # Arrange
        file_path = 123

        # Act & Assert
        with self.assertRaises(TypeError) as cm:
            ConfigManager(file_path)
        self.assertEqual(str(cm.exception), f"File path must be a string, got {type(file_path)}")

    def test_init_empty_file_path(self):
        # Arrange
        file_path = ""

        # Act & Assert
        with self.assertRaises(ValueError) as cm:
            ConfigManager(file_path)
        self.assertEqual(str(cm.exception), "File path cannot be empty")

    def test_init_file_not_found(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=False):
            # Act
            config_manager = ConfigManager(file_path)

            # Assert
            self.assertEqual(config_manager.file_path, file_path)
            self.assertEqual(config_manager._variables, {})

    def test_init_invalid_json(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="invalid json")), \
                patch("json.load", side_effect=json.JSONDecodeError("Invalid JSON", "doc", 0)):
            # Act & Assert
            with self.assertRaises(json.JSONDecodeError):
                ConfigManager(file_path)

    def test_init_permission_error(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Act & Assert
            with self.assertRaises(PermissionError) as cm:
                ConfigManager(file_path)
            self.assertEqual(str(cm.exception), "Permission denied")

    def test_set_variable_new_key(self):
        # Arrange
        file_path = "config.json"
        mock_config = {}
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value=mock_config), \
                patch("os.makedirs"), \
                patch("json.dump") as mock_json_dump:
            config_manager = ConfigManager(file_path)
            key = "work_directory"
            value = "C:\\work"

            # Act
            config_manager.set_variable(key, value)

            # Assert
            self.assertEqual(config_manager._variables[key], value)
            mock_json_dump.assert_called_once_with(mock_config, unittest.mock.ANY, indent=4)

    def test_set_variable_update_key(self):
        # Arrange
        file_path = "config.json"
        mock_config = {"work_directory": "C:\\old"}
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data='{"work_directory": "C:\\old"}')), \
                patch("json.load", return_value=mock_config), \
                patch("os.makedirs"), \
                patch("json.dump") as mock_json_dump:
            config_manager = ConfigManager(file_path)
            key = "work_directory"
            value = "C:\\new"

            # Act
            config_manager.set_variable(key, value)

            # Assert
            self.assertEqual(config_manager._variables[key], value)
            mock_json_dump.assert_called_once_with(mock_config, unittest.mock.ANY, indent=4)

    def test_set_variable_invalid_key_type(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = 123
            value = "C:\\work"

            # Act & Assert
            with self.assertRaises(TypeError) as cm:
                config_manager.set_variable(key, value)
            self.assertEqual(str(cm.exception), "Key must be a string")

    def test_set_variable_empty_key(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = ""
            value = "C:\\work"

            # Act & Assert
            with self.assertRaises(ValueError) as cm:
                config_manager.set_variable(key, value)
            self.assertEqual(str(cm.exception), "Key cannot be empty")

    def test_set_variable_permission_error(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}), \
                patch("os.makedirs"), \
                patch("builtins.open", side_effect=[mock_open(read_data="{}").return_value, PermissionError("Permission denied")]):
            config_manager = ConfigManager(file_path)
            key = "work_directory"
            value = "C:\\work"

            # Act & Assert
            with self.assertRaises(PermissionError) as cm:
                config_manager.set_variable(key, value)
            self.assertEqual(str(cm.exception), "Permission denied")

    def test_get_variable_existing_key(self):
        # Arrange
        file_path = "config.json"
        mock_config = {"work_directory": "C:\\work"}
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data='{"work_directory": "C:\\work"}')), \
                patch("json.load", return_value=mock_config):
            config_manager = ConfigManager(file_path)
            key = "work_directory"

            # Act
            result = config_manager.get_variable(key)

            # Assert
            self.assertEqual(result, "C:\\work")

    def test_get_variable_non_existing_key(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = "work_directory"

            # Act
            result = config_manager.get_variable(key)

            # Assert
            self.assertIsNone(result)

    def test_get_variable_invalid_key_type(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = 123

            # Act & Assert
            with self.assertRaises(TypeError) as cm:
                config_manager.get_variable(key)
            self.assertEqual(str(cm.exception), "Key must be a string")

    def test_get_variable_empty_key(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = ""

            # Act & Assert
            with self.assertRaises(ValueError) as cm:
                config_manager.get_variable(key)
            self.assertEqual(str(cm.exception), "Key cannot be empty")

    def test_has_variable_existing_key(self):
        # Arrange
        file_path = "config.json"
        mock_config = {"work_directory": "C:\\work"}
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data='{"work_directory": "C:\\work"}')), \
                patch("json.load", return_value=mock_config):
            config_manager = ConfigManager(file_path)
            key = "work_directory"

            # Act
            result = config_manager.has_variable(key)

            # Assert
            self.assertTrue(result)

    def test_has_variable_non_existing_key(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = "work_directory"

            # Act
            result = config_manager.has_variable(key)

            # Assert
            self.assertFalse(result)

    def test_has_variable_invalid_key_type(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = 123

            # Act & Assert
            with self.assertRaises(TypeError) as cm:
                config_manager.has_variable(key)
            self.assertEqual(str(cm.exception), "Key must be a string")

    def test_has_variable_empty_key(self):
        # Arrange
        file_path = "config.json"
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data="{}")), \
                patch("json.load", return_value={}):
            config_manager = ConfigManager(file_path)
            key = ""

            # Act & Assert
            with self.assertRaises(ValueError) as cm:
                config_manager.has_variable(key)
            self.assertEqual(str(cm.exception), "Key cannot be empty")

    def test_singleton_instance(self):
        # Arrange
        file_path = "config.json"
        mock_config = {"work_directory": "C:\\work"}
        with patch("os.path.exists", return_value=True), \
                patch("builtins.open", mock_open(read_data='{"work_directory": "C:\\work"}')), \
                patch("json.load", return_value=mock_config):
            # Act
            config_manager1 = ConfigManager(file_path)
            config_manager2 = ConfigManager(file_path)

            # Assert
            self.assertIsNot(config_manager1, config_manager2)  # Singleton not enforced in code
            self.assertEqual(config_manager1._variables, config_manager2._variables)


if __name__ == '__main__':
    unittest.main()
