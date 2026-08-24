import json
import tempfile
import unittest
from pathlib import Path

from evidence_manifest import build_manifest


class EvidenceManifestTests(unittest.TestCase):
    def test_manifest_records_digest_and_lifecycle_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.sarif"
            path.write_text(json.dumps({"runs": [{
                "properties": {"lachesis_baseline_removed": 2},
                "results": [
                    {"level": "error"},
                    {"level": "warning", "suppressions": [{"kind": "external"}]},
                ],
            }]}))
            manifest = build_manifest(
                path, engine_sha="e" * 40, catalog_sha="a" * 40,
                toolchain_fingerprint="t" * 64, repository="org/repo", commit_sha="c" * 40,
            )
            assert manifest["format"] == "lachesis-evidence"
            assert manifest["sarif"]["active_results"] == 1
            assert manifest["sarif"]["suppressed_results"] == 1
            assert manifest["sarif"]["baseline_removed"] == 2
            assert len(manifest["sarif"]["sha256"]) == 64


if __name__ == "__main__":
    unittest.main()
