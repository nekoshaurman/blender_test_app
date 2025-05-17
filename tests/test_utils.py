import unittest
from unittest.mock import patch, MagicMock
import logging
import os
import subprocess
from util.utils import (
    transform_path_to_standard,
    path_to_thumbnail,
    set_config_value,
    get_config_value,
    get_file_name_from_path,
    is_path_exists,
    get_cpu_count,
    set_blender_in_path,
    is_blender_bin,
    get_blender_paths,
    get_blender_version
)


class TestUtils(unittest.TestCase):
    def setUp(self):
        # Disable logging during tests to avoid clutter
        logging.getLogger('BlenderUtils').setLevel(logging.CRITICAL)

    def test_transform_path_to_standard_valid_path(self):
        # Arrange
        input_path = "folder/subfolder/file.txt"
        expected = "folder\\subfolder\\file.txt"

        # Act
        result = transform_path_to_standard(input_path)

        # Assert
        self.assertEqual(result, expected)

    def test_transform_path_to_standard_empty_path(self):
        # Arrange
        input_path = ""

        # Act
        result = transform_path_to_standard(input_path)

        # Assert
        self.assertEqual(result, "")

    def test_transform_path_to_standard_invalid_type(self):
        # Arrange
        input_path = 123

        # Act & Assert
        with self.assertRaises(TypeError):
            transform_path_to_standard(input_path)

    @patch('util.utils.config_manager')
    def test_path_to_thumbnail_valid_project(self, mock_config_manager):
        # Arrange
        project_name = "test_project"
        mock_config_manager.get_variable.return_value = "C:\\work"
        expected = "C:\\work\\thumbnails\\test_project.png"

        # Act
        result = path_to_thumbnail(project_name)

        # Assert
        self.assertEqual(result, expected)
        mock_config_manager.get_variable.assert_called_once_with("work_directory")

    @patch('util.utils.config_manager')
    def test_path_to_thumbnail_empty_project(self, mock_config_manager):
        # Arrange
        project_name = ""

        # Act
        result = path_to_thumbnail(project_name)

        # Assert
        self.assertEqual(result, "")
        mock_config_manager.get_variable.assert_not_called()

    @patch('util.utils.config_manager')
    def test_path_to_thumbnail_missing_work_directory(self, mock_config_manager):
        # Arrange
        project_name = "test_project"
        mock_config_manager.get_variable.return_value = ""

        # Act & Assert
        with self.assertRaises(ValueError):
            path_to_thumbnail(project_name)

    @patch('util.utils.config_manager')
    def test_set_config_value_valid(self, mock_config_manager):
        # Arrange
        key = "test_key"
        value = "test_value"
        mock_config_manager.set_variable = MagicMock()

        # Act
        set_config_value(key, value)

        # Assert
        mock_config_manager.set_variable.assert_called_once_with(key, value)

    @patch('util.utils.config_manager')
    def test_set_config_value_empty_key(self, mock_config_manager):
        # Arrange
        key = ""
        value = "test_value"

        # Act & Assert
        with self.assertRaises(ValueError):
            set_config_value(key, value)

    @patch('util.utils.config_manager')
    def test_get_config_value_valid(self, mock_config_manager):
        # Arrange
        key = "test_key"
        expected_value = "test_value"
        mock_config_manager.get_variable.return_value = expected_value

        # Act
        result = get_config_value(key)

        # Assert
        self.assertEqual(result, expected_value)
        mock_config_manager.get_variable.assert_called_once_with(key)

    def test_get_file_name_from_path_valid(self):
        # Arrange
        file_path = "folder/subfolder/file.txt"
        expected = "file.txt"

        # Act
        result = get_file_name_from_path(file_path)

        # Assert
        self.assertEqual(result, expected)

    def test_get_file_name_from_path_empty(self):
        # Arrange
        file_path = ""

        # Act
        result = get_file_name_from_path(file_path)

        # Assert
        self.assertEqual(result, "")

    @patch('os.path.exists')
    def test_is_path_exists_valid(self, mock_exists):
        # Arrange
        file_path = "folder/file.txt"
        mock_exists.return_value = True

        # Act
        result = is_path_exists(file_path)

        # Assert
        self.assertTrue(result)
        mock_exists.assert_called_once_with(file_path)

    def test_is_path_exists_empty(self):
        # Arrange
        file_path = ""

        # Act
        result = is_path_exists(file_path)

        # Assert
        self.assertFalse(result)

    @patch('os.cpu_count')
    def test_get_cpu_count_valid(self, mock_cpu_count):
        # Arrange
        mock_cpu_count.return_value = 4

        # Act
        result = get_cpu_count()

        # Assert
        self.assertEqual(result, 4)
        mock_cpu_count.assert_called_once()

    @patch('os.cpu_count')
    def test_get_cpu_count_none(self, mock_cpu_count):
        # Arrange
        mock_cpu_count.return_value = None

        # Act
        result = get_cpu_count()

        # Assert
        self.assertEqual(result, 1)

    @patch('os.path.exists')
    @patch('os.environ')
    def test_set_blender_in_path_valid(self, mock_environ, mock_exists):
        # Arrange
        blender_path = "C:\\Blender\\blender.exe"
        clean_path = "C:\\Blender"
        mock_exists.return_value = True
        mock_environ.__setitem__ = MagicMock()
        mock_environ.__getitem__.return_value = "existing_path"

        # Act
        set_blender_in_path(blender_path)

        # Assert
        mock_exists.assert_called_once_with(clean_path)
        mock_environ.__setitem__.assert_called_once_with("PATH", clean_path + os.pathsep + "existing_path")

    @patch('os.path.exists')
    def test_set_blender_in_path_invalid_path(self, mock_exists):
        # Arrange
        blender_path = "C:\\Blender\\blender.exe"
        mock_exists.return_value = False

        # Act & Assert
        with self.assertRaises(ValueError):
            set_blender_in_path(blender_path)

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_is_blender_bin_valid(self, mock_subprocess_run, mock_exists):
        # Arrange
        blender_path = "C:\\Blender\\blender.exe"
        mock_exists.return_value = True
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Blender 3.6.0\n")

        # Act
        result = is_blender_bin(blender_path)

        # Assert
        self.assertTrue(result)
        mock_subprocess_run.assert_called_once_with(
            [blender_path, '--version'],
            capture_output=True,
            text=True,
            timeout=1
        )

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_is_blender_bin_invalid(self, mock_subprocess_run, mock_exists):
        # Arrange
        blender_path = "C:\\Blender\\blender.exe"
        mock_exists.return_value = True
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="blender --version", timeout=1)

        # Act
        result = is_blender_bin(blender_path)

        # Assert
        self.assertFalse(result)

    @patch('util.utils.config_manager')
    @patch('util.utils.is_path_exists')
    @patch('util.utils.is_blender_bin')
    @patch('util.utils.get_blender_version')
    @patch('shutil.which')
    def test_get_blender_paths_valid(self, mock_which, mock_get_version, mock_is_blender, mock_is_path_exists, mock_config_manager):
        # Arrange
        mock_config_manager.get_variable.return_value = {
            "C:\\Blender\\blender.exe": "3.6.0"
        }
        mock_is_path_exists.return_value = True
        mock_is_blender.return_value = True
        mock_get_version.return_value = "Blender 3.6.0"
        mock_which.return_value = "C:\\Blender2\\blender.exe"
        expected = {
            "C:\\Blender\\blender.exe": "3.6.0",
            "C:\\Blender2\\blender.exe": "Blender 3.6.0"
        }

        # Act
        result = get_blender_paths()

        # Assert
        self.assertEqual(result, expected)

    @patch('os.path.exists')
    @patch('subprocess.run')
    def test_get_blender_version_valid(self, mock_subprocess_run, mock_exists):
        # Arrange
        blender_path = "C:\\Blender\\blender.exe"
        mock_exists.return_value = True
        mock_subprocess_run.return_value = MagicMock(
            returncode=0,
            stdout="Blender 3.6.0\nOther output",
            stderr=""
        )
        expected = "Blender 3.6.0"

        # Act
        result = get_blender_version(blender_path)

        # Assert
        self.assertEqual(result, expected)
        mock_subprocess_run.assert_called_once_with(
            [blender_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )


if __name__ == '__main__':
    unittest.main()
