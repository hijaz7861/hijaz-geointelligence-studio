import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.publishing.release_bundle import build_release_bundle
from app.research.claim_ledger import add_claim
from app.research.source_ledger import add_source
from app.research.source_snapshots import SourceSnapshotError, verify_source_snapshots

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {
    "title": "Synthetic report",
    "url": "https://example.org/report",
    "published_at": "2026-10-20",
    "source_type": "independent_reporting",
    "claim_status": "independent_reporting",
    "notes": "Synthetic fixture only.",
}
CLAIM = {
    "claim": "Synthetic documentary claim",
    "status": "independent_reporting",
    "source_urls": [SOURCE["url"]],
    "notes": "Fixture only.",
}
PROJECT = {
    "project_id": "snapshot-fixture",
    "title": "Synthetic snapshot fixture",
    "language": "en",
    "target_duration_seconds": 60,
    "script": "[[claim:Synthetic documentary claim]] Synthetic documentary claim.",
    "claim_ids": [CLAIM["claim"]],
    "media_assets": [{
        "asset_id": "asset-fixture",
        "origin_url": SOURCE["url"],
        "rights_status": "unknown",
        "creator": "Fixture",
        "attribution": "Fixture",
        "usage_scope": "Never publish",
        "rights_evidence": "Fixture only",
        "notes": "Synthetic test",
    }],
    "approval": {
        "script_reviewed": False,
        "translation_reviewed": False,
        "media_rights_reviewed": False,
        "final_video_reviewed": False,
        "approved_by": "",
    },
}


class SourceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.snapshot_dir = self.root / "snapshots"
        self.snapshot_dir.mkdir()
        self.snapshot = self.snapshot_dir / "report.html"
        self.snapshot.write_bytes(b"<html>archived fixture</html>")
        self.manifest = self.root / "manifest.json"
        self.entry = {
            "url": SOURCE["url"],
            "snapshot_path": "snapshots/report.html",
            "sha256": hashlib.sha256(self.snapshot.read_bytes()).hexdigest(),
            "captured_at": "2026-11-13T02:00:00Z",
        }
        self.write_manifest([self.entry])

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self, entries):
        self.manifest.write_text(json.dumps(entries), encoding="utf-8")

    def verify(self, *, max_snapshot_bytes=25 * 1024 * 1024, known_urls=None):
        return verify_source_snapshots(
            self.manifest,
            [SOURCE["url"]] if known_urls is None else known_urls,
            max_snapshot_bytes=max_snapshot_bytes,
        )

    def test_verifies_exact_source_url_and_snapshot_digest(self):
        report = self.verify()
        self.assertEqual(report["validation"], "PASS")
        self.assertEqual(report["entry_count"], 1)
        self.assertEqual(report["verified_count"], 1)
        self.assertEqual(report["entries"][0]["integrity"], "PASS")
        self.assertEqual(report["entries"][0]["url_match"], "EXACT_SOURCE_LEDGER_URL")
        self.assertEqual(report["entries"][0]["captured_at"], "2026-11-13T02:00:00Z")

    def test_rejects_changed_snapshot_bytes(self):
        self.snapshot.write_bytes(b"changed after manifest creation")
        with self.assertRaisesRegex(SourceSnapshotError, "SHA-256 mismatch"):
            self.verify()

    def test_rejects_source_url_not_in_ledger(self):
        self.write_manifest([{**self.entry, "url": "https://other.example/report"}])
        with self.assertRaisesRegex(SourceSnapshotError, "absent from the source ledger"):
            self.verify()

    def test_rejects_duplicate_source_urls(self):
        self.write_manifest([self.entry, {**self.entry, "snapshot_path": "snapshots/other.html"}])
        (self.snapshot_dir / "other.html").write_bytes(b"other")
        with self.assertRaisesRegex(SourceSnapshotError, "Duplicate snapshot URL"):
            self.verify()

    def test_rejects_duplicate_snapshot_paths(self):
        second_url = "https://example.org/second-report"
        second = {**self.entry, "url": second_url}
        self.write_manifest([self.entry, second])
        with self.assertRaisesRegex(SourceSnapshotError, "Duplicate snapshot_path"):
            self.verify(known_urls=[SOURCE["url"], second_url])

    def test_rejects_parent_traversal(self):
        self.write_manifest([{**self.entry, "snapshot_path": "../report.html"}])
        with self.assertRaisesRegex(SourceSnapshotError, "parent-traversal"):
            self.verify()

    def test_rejects_absolute_snapshot_path(self):
        self.write_manifest([{**self.entry, "snapshot_path": str(self.snapshot)}])
        with self.assertRaisesRegex(SourceSnapshotError, "relative to the manifest directory"):
            self.verify()

    def test_rejects_symlink_snapshot(self):
        link = self.snapshot_dir / "linked.html"
        try:
            link.symlink_to(self.snapshot)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are unavailable on this runner.")
        self.write_manifest([{**self.entry, "snapshot_path": "snapshots/linked.html"}])
        with self.assertRaisesRegex(SourceSnapshotError, "Symlinks are not allowed"):
            self.verify()

    def test_rejects_symlink_manifest(self):
        target = self.root / "manifest-target.json"
        target.write_text(json.dumps([self.entry]), encoding="utf-8")
        self.manifest.unlink()
        try:
            self.manifest.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are unavailable on this runner.")
        with self.assertRaisesRegex(SourceSnapshotError, "non-symlink"):
            self.verify()

    def test_rejects_timezone_naive_capture_time(self):
        self.write_manifest([{**self.entry, "captured_at": "2026-11-13T02:00:00"}])
        with self.assertRaisesRegex(SourceSnapshotError, "explicit timezone"):
            self.verify()

    def test_rejects_malformed_digest(self):
        self.write_manifest([{**self.entry, "sha256": "not-a-digest"}])
        with self.assertRaisesRegex(SourceSnapshotError, "64 lowercase hexadecimal"):
            self.verify()

    def test_rejects_oversized_snapshot(self):
        with self.assertRaisesRegex(SourceSnapshotError, "size limit"):
            self.verify(max_snapshot_bytes=4)

    def test_rejects_duplicate_json_keys(self):
        self.manifest.write_text(
            '[{"url":"https://example.org/report","url":"https://example.org/report",'
            '"snapshot_path":"snapshots/report.html","sha256":"' + self.entry["sha256"] +
            '","captured_at":"2026-11-13T02:00:00Z"}]',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(SourceSnapshotError, "Duplicate JSON object key"):
            self.verify()

    def test_rejects_nonstandard_json_constant(self):
        self.manifest.write_text("[NaN]", encoding="utf-8")
        with self.assertRaisesRegex(SourceSnapshotError, "Non-standard JSON constant"):
            self.verify()

    def test_rejects_boolean_size_limit(self):
        with self.assertRaisesRegex(SourceSnapshotError, "positive integer"):
            self.verify(max_snapshot_bytes=True)

    def test_cli_help_is_available(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_source_snapshots.py"), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--manifest", result.stdout)
        self.assertIn("--sources-file", result.stdout)

    def test_cli_verifies_manifest_with_explicit_source_ledger(self):
        sources_file = self.root / "sources.json"
        add_source(SOURCE, sources_file)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "verify_source_snapshots.py"),
                "--manifest", str(self.manifest),
                "--sources-file", str(sources_file),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"validation": "PASS"', result.stdout)
        self.assertIn('"verified_count": 1', result.stdout)


class ReleaseBundleSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sources = self.root / "sources.json"
        self.claims = self.root / "claims.json"
        self.project = self.root / "project.json"
        add_source(SOURCE, self.sources)
        add_claim(CLAIM, self.claims, self.sources)
        self.project.write_text(json.dumps(PROJECT), encoding="utf-8")
        self.video = self.root / "final.mp4"
        self.video.write_bytes(b"synthetic video fixture")
        self.srt = self.root / "final.srt"
        self.srt.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nSynthetic caption.\n",
            encoding="utf-8",
        )
        self.metadata = self.root / "metadata.json"
        self.metadata.write_text(
            json.dumps({"publish_ready": False, "release_blockers": ["Human approval missing"]}),
            encoding="utf-8",
        )
        self.snapshot_dir = self.root / "snapshots"
        self.snapshot_dir.mkdir()
        self.snapshot = self.snapshot_dir / "report.html"
        self.snapshot.write_bytes(b"<html>archived fixture</html>")
        self.manifest = self.root / "snapshot-manifest.json"
        self.manifest.write_text(json.dumps([{
            "url": SOURCE["url"],
            "snapshot_path": "snapshots/report.html",
            "sha256": hashlib.sha256(self.snapshot.read_bytes()).hexdigest(),
            "captured_at": "2026-11-13T02:00:00Z",
        }]), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    @patch(
        "app.publishing.release_bundle.inspect_rendered_video",
        return_value={
            "validation": "PASS",
            "duration_seconds": 1.0,
            "width": 1280,
            "height": 720,
            "audio_stream_count": 1,
            "subtitle_stream_count": 1,
        },
    )
    def test_release_bundle_includes_snapshot_integrity_evidence(self, probe):
        bundle = build_release_bundle(
            self.project,
            source_path=self.sources,
            claims_path=self.claims,
            render_path=self.video,
            subtitle_path=self.srt,
            metadata_path=self.metadata,
            snapshot_manifest_path=self.manifest,
        )
        self.assertEqual(bundle["source_snapshot_validation"]["validation"], "PASS")
        self.assertEqual(bundle["source_snapshot_validation"]["verified_count"], 1)
        evidence = bundle["claim_evidence"][0]["sources"][0]["snapshot_evidence"]
        self.assertEqual(evidence["integrity"], "PASS")
        self.assertEqual(evidence["url_match"], "EXACT_SOURCE_LEDGER_URL")
        self.assertFalse(bundle["publish_ready"])
        self.assertTrue(any("local bytes" in item.lower() for item in bundle["limitations"]))
        probe.assert_called_once()

    def test_invalid_snapshot_manifest_adds_release_blocker(self):
        self.manifest.write_text("[NaN]", encoding="utf-8")
        bundle = build_release_bundle(
            self.project,
            source_path=self.sources,
            claims_path=self.claims,
            snapshot_manifest_path=self.manifest,
        )
        self.assertEqual(bundle["source_snapshot_validation"]["validation"], "FAIL")
        self.assertTrue(any("snapshot manifest validation failed" in item.lower() for item in bundle["release_blockers"]))

    def test_missing_snapshot_manifest_is_explicitly_not_provided(self):
        bundle = build_release_bundle(
            self.project,
            source_path=self.sources,
            claims_path=self.claims,
        )
        self.assertEqual(bundle["source_snapshot_validation"]["validation"], "NOT_PROVIDED")
        evidence = bundle["claim_evidence"][0]["sources"][0]["snapshot_evidence"]
        self.assertEqual(evidence["integrity"], "NOT_PROVIDED")


if __name__ == "__main__":
    unittest.main()
