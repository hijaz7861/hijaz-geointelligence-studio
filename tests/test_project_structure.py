import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_required_directories_exist(self):
        for name in (
            "app/research",
            "app/dashboard",
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

    def test_expected_cli_scripts_exist(self):
        for name in (
            "add_source.py",
            "add_claim.py",
            "validate_project.py",
            "validate_srt.py",
            "render_video.py",
            "build_cited_draft.py",
            "build_release_metadata.py",
            "generate_narration.py",
            "validate_translation.py",
            "run_dashboard.py",
            "validate_render.py",
        ):
            with self.subTest(script=name):
                self.assertTrue((ROOT / "scripts" / name).is_file())


if __name__ == "__main__":
    unittest.main()
