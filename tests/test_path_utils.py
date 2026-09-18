import unittest

from src.path_utils import normalize_folder_path


class PathUtilsTests(unittest.TestCase):
    def test_normalizes_plain_path(self):
        self.assertTrue(normalize_folder_path("/tmp/../tmp").endswith("/tmp"))

    def test_normalizes_file_uri(self):
        normalized = normalize_folder_path("file:///tmp/demo%20folder")
        self.assertTrue(normalized.endswith("/tmp/demo folder"))

    def test_rejects_non_file_uri(self):
        with self.assertRaises(ValueError):
            normalize_folder_path("https://example.com")


if __name__ == "__main__":
    unittest.main()
