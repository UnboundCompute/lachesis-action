import importlib.util
import json
from pathlib import Path
import unittest


MODULE = Path(__file__).with_name("sarif_export.py")
SPEC = importlib.util.spec_from_file_location("sarif_export", MODULE)
sarif_export = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sarif_export)


class SarifExportTests(unittest.TestCase):
    def test_classification_preserves_guard_differential(self):
        self.assertEqual(
            "unguarded-differential",
            sarif_export.classify({
                "status": "UNGUARDED", "differential_siblings": ["guarded"],
            }),
        )
        self.assertEqual("guarded", sarif_export.classify({"status": "GUARDED"}))
        self.assertEqual("reachable", sarif_export.classify({"status": "OPAQUE"}))

    def test_path_normalization_and_exclusions(self):
        self.assertEqual("src/app.py", sarif_export.rel_uri(
            "/repo/src/app.py", "/repo",
        ))
        self.assertTrue(sarif_export.is_excluded("src/vendor/lib.c", ["src/vendor"]))
        self.assertTrue(sarif_export.is_excluded("src/generated/a.js", ["**/generated/**"]))
        self.assertFalse(sarif_export.is_excluded("src/app.py", ["src/vendor"]))

    def test_path_normalization_preserves_hidden_components(self):
        self.assertEqual(".github/workflows/scan.yml",
                         sarif_export.normalize_uri("./.github/workflows/scan.yml"))
        self.assertEqual(".env", sarif_export.normalize_uri(".env"))
        self.assertEqual("../outside.py", sarif_export.normalize_uri("../outside.py"))

        args = type("Args", (), {
            "changed_from_file": None,
            "changed_files": ["./.github/workflows/scan.yml"],
        })()
        self.assertEqual({".github/workflows/scan.yml"}, sarif_export.load_changed(args))

    def test_build_result_has_sink_anchor_and_code_flow(self):
        path = {
            "id": "path-1", "label": "request -> query",
        }
        detail = {
            "summary": {"guard": {
                "status": "UNGUARDED", "differential_siblings": ["safe"],
                "handler_label": "handler", "sink_names": ["query"],
                "file": "src/app.py", "line": 12,
            }},
            "sections": {"path": [
                {"kind": "source", "label": "request", "locator": {
                    "location": {"absolute_file": "/repo/src/app.py", "start_line": 8},
                }},
                {"kind": "sink", "label": "query", "locator": {
                    "location": {"absolute_file": "/repo/src/app.py", "start_line": 12},
                }},
            ]},
        }
        result = sarif_export.build_result(path, detail, "/repo")
        self.assertEqual("lachesis/unguarded-sink-differential", result["ruleId"])
        self.assertEqual("src/app.py", result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"])
        self.assertEqual("path-1", result["partialFingerprints"]["lachesisPathId"])
        self.assertEqual(2, len(result["codeFlows"][0]["threadFlows"][0]["locations"]))


if __name__ == "__main__":
    unittest.main()
