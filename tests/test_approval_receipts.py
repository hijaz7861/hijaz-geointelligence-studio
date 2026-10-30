import json
import os
import tempfile
import unittest
from pathlib import Path
from app.publishing.approval_receipts import (
    APPROVAL_STAGES,
    ApprovalReceiptError,
    create_approval_key,
    record_approval,
    verify_approval_receipts,
)

PROJECT = {
    "project_id": "approval-fixture",
    "approval": {
        "script_reviewed": True,
        "translation_reviewed": True,
        "media_rights_reviewed": True,
        "final_video_reviewed": True,
        "approved_by": "Fixture reviewer",
    },
}

class ApprovalReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "project.json"
        self.project.write_text(json.dumps(PROJECT, sort_keys=True), encoding="utf-8")
        self.render = self.root / "review.mp4"
        self.render.write_bytes(b"synthetic MP4 fixture")
        self.key = create_approval_key(self.root / "private" / "approval.key")
        self.receipts = self.root / "approvals.json"

    def tearDown(self):
        self.temp.cleanup()

    def record_all(self):
        for stage in APPROVAL_STAGES:
            record_approval(
                self.project, self.receipts, self.key,
                stage=stage, decision="approved", reviewer="Human reviewer",
                reason="Reviewed the relevant project materials.",
                artifact_path=self.render if stage == "final_video_reviewed" else None,
                reviewed_at="2026-10-30T03:00:00Z",
            )

    def test_key_is_owner_only_and_not_overwritten(self):
        if os.name == "posix":
            self.assertEqual(self.key.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(ApprovalReceiptError, "Refusing to overwrite"):
            create_approval_key(self.key)

    def test_all_four_project_bound_receipts_verify(self):
        self.record_all()
        report = verify_approval_receipts(self.project, self.receipts, self.key, render_path=self.render)
        self.assertEqual(report["validation"], "PASS")
        self.assertEqual([item["stage"] for item in report["verified_stages"]], list(APPROVAL_STAGES))
        self.assertIn("self-asserted", report["identity_assurance"])

    def test_modified_receipt_is_rejected(self):
        self.record_all()
        document = json.loads(self.receipts.read_text(encoding="utf-8"))
        document["receipts"][0]["payload"]["reviewer"] = "Changed reviewer"
        self.receipts.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(ApprovalReceiptError, "signature is invalid"):
            verify_approval_receipts(self.project, self.receipts, self.key, render_path=self.render)

    def test_project_change_invalidates_receipts(self):
        self.record_all()
        changed = {**PROJECT, "title": "Changed after review"}
        self.project.write_text(json.dumps(changed, sort_keys=True), encoding="utf-8")
        with self.assertRaisesRegex(ApprovalReceiptError, "Project changed"):
            verify_approval_receipts(self.project, self.receipts, self.key, render_path=self.render)

    def test_render_change_invalidates_final_video_receipt(self):
        self.record_all()
        self.render.write_bytes(b"replacement MP4 fixture")
        with self.assertRaisesRegex(ApprovalReceiptError, "MP4 changed"):
            verify_approval_receipts(self.project, self.receipts, self.key, render_path=self.render)

    def test_missing_stage_fails_closed(self):
        record_approval(
            self.project, self.receipts, self.key, stage="script_reviewed",
            decision="approved", reviewer="Human reviewer",
            reason="Reviewed the script text.",
        )
        with self.assertRaisesRegex(ApprovalReceiptError, "Missing approved receipt stages"):
            verify_approval_receipts(self.project, self.receipts, self.key, render_path=self.render)

    def test_rejection_fails_closed(self):
        record_approval(
            self.project, self.receipts, self.key, stage="script_reviewed",
            decision="rejected", reviewer="Human reviewer",
            reason="The factual citations need correction.",
        )
        with self.assertRaisesRegex(ApprovalReceiptError, "rejected stage"):
            verify_approval_receipts(self.project, self.receipts, self.key, render_path=self.render)

    def test_duplicate_stage_cannot_be_appended(self):
        record_approval(
            self.project, self.receipts, self.key, stage="script_reviewed",
            decision="approved", reviewer="Human reviewer",
            reason="Reviewed the script text.",
        )
        with self.assertRaisesRegex(ApprovalReceiptError, "already exists"):
            record_approval(
                self.project, self.receipts, self.key, stage="script_reviewed",
                decision="approved", reviewer="Human reviewer",
                reason="Reviewed the script again.",
            )

    def test_final_video_receipt_requires_exact_artifact(self):
        with self.assertRaisesRegex(ApprovalReceiptError, "requires --artifact"):
            record_approval(
                self.project, self.receipts, self.key, stage="final_video_reviewed",
                decision="approved", reviewer="Human reviewer",
                reason="Reviewed the final MP4.",
            )

    def test_insecure_key_permissions_are_rejected(self):
        if os.name != "posix":
            self.skipTest("POSIX permission semantics are unavailable")
        insecure = self.root / "insecure.key"
        insecure.write_bytes(b"x" * 32)
        insecure.chmod(0o644)
        with self.assertRaisesRegex(ApprovalReceiptError, "permissions are too broad"):
            record_approval(
                self.project, self.receipts, insecure, stage="script_reviewed",
                decision="approved", reviewer="Human reviewer",
                reason="Reviewed the script text.",
            )

if __name__ == "__main__":
    unittest.main()
