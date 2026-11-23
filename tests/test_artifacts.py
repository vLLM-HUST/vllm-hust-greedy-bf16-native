# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools.build_overlay import build, verify_digest


ROOT = Path(__file__).resolve().parents[1]


class Artifacts(unittest.TestCase):
    def test_patch_and_evidence_bind_the_same_candidate(self):
        manifest = json.loads((ROOT / "mod.json").read_bytes())
        evidence = json.loads((ROOT / "evidence/summary.json").read_bytes())
        verify_digest((ROOT / manifest["patch"]).read_bytes(), manifest["patch_sha256"], "Patch")
        self.assertEqual(evidence["id"], manifest["id"])
        self.assertEqual(evidence["candidate"]["baseline_file_sha256"], manifest["original_sha256"])
        self.assertEqual(evidence["candidate"]["replacement_file_sha256"], manifest["candidate_sha256"])
        self.assertEqual([case["cases_per_arm"] for case in evidence["screens"]], [10, 190])
        self.assertFalse(evidence["candidate"]["included_in_frozen_engine"])

    def test_rejects_an_unverified_base_before_writing(self):
        with TemporaryDirectory() as name:
            folder = Path(name)
            source = folder / "wrong_source.py"
            output = folder / "candidate.py"
            source.write_bytes(b"# different host source\n")
            with self.assertRaisesRegex(ValueError, "Frozen sampler SHA-256 mismatch"):
                build(source, output)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), b"# different host source\n")


if __name__ == "__main__":
    unittest.main()