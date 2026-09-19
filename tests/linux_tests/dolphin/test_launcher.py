import unittest

from platforms.linux.dolphin import launcher


class DolphinLauncherTests(unittest.TestCase):
    def test_run_rejects_missing_folder(self):
        self.assertEqual(2, launcher.run(""))

    def test_run_rejects_non_file_uri(self):
        self.assertEqual(2, launcher.run("https://example.com"))

    def test_run_reports_missing_gtk_after_normalizing_folder(self):
        if launcher.Gtk is not None:
            self.skipTest("GTK is available; this test targets the headless path")
        self.assertEqual(1, launcher.run("file:///tmp"))


if __name__ == "__main__":
    unittest.main()
