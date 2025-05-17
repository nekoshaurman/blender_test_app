import unittest
from unittest.mock import patch
from dto.project import Project


class TestProject(unittest.TestCase):
    def test_project_init(self):
        # Arrange
        file_path = "C:\\projects\\test.blend"
        expected_unique_name_pattern = r"test\.blend_\d{4}"
        expected_preview_path = "C:\\work\\thumbnails\\test.blend_1234.png"

        with patch("dto.project.os.path.basename", return_value="test.blend"), \
                patch("dto.project.utils.path_to_thumbnail", return_value=expected_preview_path), \
                patch("random.randint", return_value=1234):
            # Act
            project = Project(file_path)

            # Assert
            self.assertEqual(project.file_path, file_path)
            self.assertRegex(project.unique_name, expected_unique_name_pattern)
            self.assertEqual(project.preview_path, expected_preview_path)
            self.assertEqual(project.settings, {})

    def test_generate_unique_name(self):
        # Arrange
        file_path = "C:\\projects\\test.blend"
        with patch("dto.project.os.path.basename", return_value="test.blend"), \
                patch("dto.project.utils.path_to_thumbnail", return_value="mocked_path"), \
                patch("random.randint", return_value=5678):
            project = Project(file_path)

            # Act
            unique_name = project.generate_unique_name()

            # Assert
            self.assertEqual(unique_name, "test.blend_5678")

    def test_get_thumbnail_path(self):
        # Arrange
        file_path = "C:\\projects\\test.blend"
        expected_thumbnail = "C:\\work\\thumbnails\\test.blend_1234.png"
        with patch("dto.project.os.path.basename", return_value="test.blend"), \
                patch("random.randint", return_value=1234), \
                patch("dto.project.utils.path_to_thumbnail", return_value=expected_thumbnail) as mock_path_to_thumbnail:
            project = Project(file_path)
            mock_path_to_thumbnail.reset_mock()  # Reset calls from __init__

            # Act
            thumbnail_path = project.get_thumbnail_path()

            # Assert
            self.assertEqual(thumbnail_path, expected_thumbnail)
            mock_path_to_thumbnail.assert_called_once_with(project.unique_name)

    def test_set_settings(self):
        # Arrange
        file_path = "C:\\projects\\test.blend"
        new_settings = {"resolution": "1080p", "format": "png"}
        with patch("dto.project.os.path.basename", return_value="test.blend"), \
                patch("random.randint", return_value=1234), \
                patch("dto.project.utils.path_to_thumbnail", return_value="mocked_path"):
            project = Project(file_path)

            # Act
            project.set_settings(new_settings)

            # Assert
            self.assertEqual(project.settings, new_settings)

    def test_repr(self):
        # Arrange
        file_path = "C:\\projects\\test.blend"
        with patch("dto.project.os.path.basename", return_value="test.blend"), \
                patch("random.randint", return_value=1234), \
                patch("dto.project.utils.path_to_thumbnail", return_value="mocked_path"):
            project = Project(file_path)

            # Act
            repr_string = str(project)

            # Assert
            self.assertEqual(
                repr_string,
                "Project(name=test.blend_1234, unique_name=test.blend_1234, file_path=C:\\projects\\test.blend)"
            )


if __name__ == '__main__':
    unittest.main()