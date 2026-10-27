import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_required_directories_exist(self):
        for name in (
            "app/research",
            "app/editorial",
            "app/video",
            "app/voice",
            "app/publishing",
            "config",
            "docs",
            "tests",
        ):
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_dir())

    def test_editorial_policy_exists(self):
        policy = ROOT / "docs" / "editorial-policy.md"
        self.assertTrue(policy.is_file())
        self.assertIn("human", policy.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
