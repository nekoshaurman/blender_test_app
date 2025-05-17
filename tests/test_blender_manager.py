import subprocess
import unittest
from unittest.mock import patch, MagicMock, call
import logging
from PyQt5.QtCore import QObject
from managers.blender_manager import BlenderManager
from dto.project import Project


class MockQObject(QObject):
    """A mock QObject with a mock signal for testing."""

    def __init__(self):
        super().__init__()
        self.signal = MagicMock()


class TestBlenderManager(unittest.TestCase):
    def setUp(self):
        # Disable logging during tests to avoid clutter
        logging.getLogger('BlenderManager').setLevel(logging.CRITICAL)
        # Create a mock parent as a proper QObject
        self.mock_parent = MockQObject()

    def test_init_with_parent(self):
        # Arrange
        parent = self.mock_parent

        # Act
        manager = BlenderManager(parent)

        # Assert
        self.assertEqual(manager.qt_signal, parent.signal)
        self.assertIsNotNone(manager.qt_signal)

    def test_init_without_parent(self):
        # Arrange
        parent = None

        # Act
        manager = BlenderManager(parent)

        # Assert
        self.assertIsNone(manager.qt_signal)

    def test_render_project_thumbnail_invalid_project(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        invalid_project = None

        # Act
        manager.render_project_thumbnail(invalid_project)

        # Assert
        self.mock_parent.signal.emit.assert_called_once_with("Error: Invalid project object")

    @patch("threading.Thread")
    def test_render_project_thumbnail_valid_project(self, mock_thread):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        project = MagicMock(spec=Project)
        project.file_path = "C:\\project.blend"
        project.unique_name = "project_1234"
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Act
        manager.render_project_thumbnail(project)

        # Assert
        mock_thread.assert_called_once_with(
            target=manager._start_render_thumbnail,
            args=(project, unittest.mock.ANY)
        )
        mock_thread_instance.start.assert_called_once()
        self.mock_parent.signal.emit.assert_called_with(f"Start render thumbnail: {project.file_path}")

    def test_start_render_projects_invalid_type(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = "not_a_list"

        # Act
        manager.start_render_projects(projects, isCreatingThumbnails=True)

        # Assert
        self.mock_parent.signal.emit.assert_called_once_with("Error: Projects must be a list")

    def test_start_render_projects_empty_list(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = []

        # Act
        manager.start_render_projects(projects, isCreatingThumbnails=True)

        # Assert
        self.mock_parent.signal.emit.assert_called_once_with("No projects to render")

    @patch("threading.Thread")
    def test_start_render_projects_thumbnail_mode(self, mock_thread):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = [MagicMock(spec=Project)]
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Act
        manager.start_render_projects(projects, isCreatingThumbnails=True)

        # Assert
        mock_thread.assert_called_once_with(
            target=manager._render_next_thumbnail,
            args=(projects,)
        )
        mock_thread_instance.start.assert_called_once()

    @patch("threading.Thread")
    def test_start_render_projects_render_mode(self, mock_thread):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = [MagicMock(spec=Project)]
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance

        # Act
        manager.start_render_projects(projects, isCreatingThumbnails=False)

        # Assert
        mock_thread.assert_called_once_with(
            target=manager._render_next,
            args=(projects,)
        )
        mock_thread_instance.start.assert_called_once()

    def test_render_next_thumbnail_empty_list(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = []

        # Act
        manager._render_next_thumbnail(projects)

        # Assert
        self.mock_parent.signal.emit.assert_called_once_with("All thumbnail renders completed.\n")

    def test_render_next_thumbnail_invalid_project(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = [MagicMock(spec=[])]  # No attributes to fail hasattr checks
        with patch.object(manager, "_on_render_thumbnails_complete") as mock_complete:
            # Act
            manager._render_next_thumbnail(projects)

            # Assert
            self.mock_parent.signal.emit.assert_called_once_with("Error: Invalid project object")
            mock_complete.assert_called_once_with(projects)

    @patch("managers.blender_manager.utils")
    def test_start_render_thumbnail_file_not_found(self, mock_utils):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        project = MagicMock(spec=Project)
        project.file_path = "C:\\project.blend"
        project.unique_name = "project_1234"
        mock_utils.is_path_exists.return_value = False
        callback = MagicMock()

        # Act
        manager._start_render_thumbnail(project, callback)

        # Assert
        self.mock_parent.signal.emit.assert_called_once_with(f"File {project.file_path} not found.")
        callback.assert_called_once()

    def test_render_next_empty_list(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = []

        # Act
        manager._render_next(projects)

        # Assert
        self.mock_parent.signal.emit.assert_called_once_with("All renders completed.\n")

    def test_render_next_invalid_project(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        projects = [MagicMock(spec=[])]  # No attributes to fail hasattr checks
        with patch.object(manager, "_on_render_complete") as mock_complete:
            # Act
            manager._render_next(projects)

            # Assert
            self.mock_parent.signal.emit.assert_called_once_with("Error: Invalid project object")
            mock_complete.assert_called_once_with(projects)

    def test_get_settings_from_project_invalid_path_type(self):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        file_path = 123

        # Act
        result = manager.get_settings_from_project(file_path)

        # Assert
        self.assertIsNone(result)
        self.mock_parent.signal.emit.assert_called_once_with(f"Error: Invalid file path type: {type(file_path)}")

    @patch("managers.blender_manager.utils.is_path_exists", return_value=False)
    def test_get_settings_from_project_file_not_found(self, mock_is_path_exists):
        # Arrange
        manager = BlenderManager(self.mock_parent)
        file_path = "C:\\project.blend"

        # Act
        result = manager.get_settings_from_project(file_path)

        # Assert
        self.assertIsNone(result)
        self.mock_parent.signal.emit.assert_called_once_with(f"File {file_path} not found.")


if __name__ == '__main__':
    unittest.main()
