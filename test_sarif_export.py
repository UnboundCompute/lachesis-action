import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock


MODULE = Path(__file__).with_name("sarif_export.py")
SPEC = importlib.util.spec_from_file_location("sarif_export", MODULE)
sarif_export = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sarif_export)


class SarifExportTests(unittest.TestCase):
    def test_run_query_has_a_wall_clock_bound(self):
        with mock.patch.object(
            sarif_export.subprocess, "run",
            side_effect=subprocess.TimeoutExpired(["lachesis-query"], 7),
        ):
            with self.assertRaises(subprocess.TimeoutExpired):
                sarif_export.run_query(["lachesis-query"], "graph.kuzu", "overview", timeout=7)

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

    def test_build_sarif_dedupes_same_rule_file_and_line(self):
        # One sink reached by two distinct witness paths -> two path slices that
        # anchor to the same (rule, file, line). They must collapse to a single
        # SARIF result so the bot posts one comment, not a stack of identical ones.
        def entry(path_id):
            return {
                "pq": {"id": path_id, "label": "request -> query"},
                "detail": {
                    "summary": {"guard": {
                        "status": "GUARDED", "differential_siblings": [],
                        "handler_label": "audit_lookup", "sink_names": ["execute"],
                        "file": "app/routes/reports.py", "line": 52,
                    }},
                    "sections": {"path": [
                        {"kind": "source", "label": "request", "locator": {
                            "location": {"absolute_file": "/repo/app/routes/reports.py", "start_line": 46},
                        }},
                        {"kind": "sink", "label": "execute", "locator": {
                            "location": {"absolute_file": "/repo/app/routes/reports.py", "start_line": 52},
                        }},
                    ]},
                },
            }
        with mock.patch.object(
            sarif_export, "collect_paths",
            return_value=[entry("path-a"), entry("path-b"), entry("path-c")],
        ):
            sarif = sarif_export.build_sarif("graph.kuzu", ["q"], "/repo", None)
        results = sarif["runs"][0]["results"]
        self.assertEqual(1, len(results))
        loc = results[0]["locations"][0]["physicalLocation"]
        self.assertEqual("app/routes/reports.py", loc["artifactLocation"]["uri"])
        self.assertEqual(52, loc["region"]["startLine"])

    def test_build_sarif_records_analysis_provenance(self):
        with mock.patch.object(sarif_export, "collect_paths", return_value=[]):
            sarif = sarif_export.build_sarif(
                "graph.kuzu", ["q"], "/repo", None,
                provenance={"engine_sha": "engine", "catalog_sha": "catalog"},
            )
        properties = sarif["runs"][0]["tool"]["driver"]["properties"]
        self.assertEqual("security-paths", properties["analysis_projection"])
        self.assertEqual("engine", properties["engine_sha"])
        self.assertEqual("catalog", properties["catalog_sha"])


if __name__ == "__main__":
    unittest.main()
