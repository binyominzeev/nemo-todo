import unittest

from platforms.linux.common.dock_geometry import Geometry, compute_dock_geometry


class ComputeDockGeometryTests(unittest.TestCase):
    def test_docks_to_the_right_when_space_available(self):
        target = Geometry(x=100, y=50, width=800, height=600)
        result = compute_dock_geometry(target, panel_width=400, screen_width=1920)
        self.assertEqual(Geometry(x=900, y=50, width=400, height=600), result)

    def test_flips_to_the_left_when_right_side_overflows(self):
        target = Geometry(x=1200, y=0, width=800, height=600)
        result = compute_dock_geometry(target, panel_width=400, screen_width=1920)
        self.assertEqual(Geometry(x=800, y=0, width=400, height=600), result)

    def test_preserves_target_height_and_vertical_position(self):
        target = Geometry(x=0, y=75, width=500, height=333)
        result = compute_dock_geometry(target, panel_width=200, screen_width=1920)
        self.assertEqual(75, result.y)
        self.assertEqual(333, result.height)


if __name__ == "__main__":
    unittest.main()
