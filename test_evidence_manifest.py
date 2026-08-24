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
                "properties": {"lachesis_baseline_removed": 2, "lachesis_baseline_removed_fingerprints": ["f" * 64]},
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
            assert manifest["finding_schema_version"] == "0.1"
            assert manifest["sarif"]["active_results"] == 1
            assert manifest["sarif"]["suppressed_results"] == 1
            assert manifest["sarif"]["baseline_removed"] == 2
            assert manifest["sarif"]["baseline_removed_fingerprints"] == ["f" * 64]
            assert len(manifest["sarif"]["sha256"]) == 64

    def test_manifest_binds_optional_candidate_census_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sarif = root / "report.sarif"
            census = root / "census.json"
            sarif.write_text(json.dumps({"runs": [{"results": []}]}))
            census.write_text(json.dumps({"census": {"unbound": 3}}))
            manifest = build_manifest(
                sarif, engine_sha="e" * 40, catalog_sha="a" * 40,
                toolchain_fingerprint="t" * 64, candidate_census_path=census,
            )
            assert manifest["candidate_census"]["path"] == str(census)
            assert len(manifest["candidate_census"]["sha256"]) == 64


if __name__ == "__main__":
    unittest.main()
