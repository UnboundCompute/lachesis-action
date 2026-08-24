import json
import tempfile
import unittest
from pathlib import Path

from baseline_sarif import filter_document


def report(results):
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "test"}}, "results": results}]}


def finding(line, rule="lachesis/unguarded-sink", fingerprint=None):
    result = {"ruleId": rule, "locations": [{"physicalLocation": {
        "artifactLocation": {"uri": "src/app.py"}, "region": {"startLine": line},
    }}]}
    if fingerprint:
        result["partialFingerprints"] = {"lachesisFinding": fingerprint}
    return result


class BaselineSarifTests(unittest.TestCase):
    def test_removes_matching_rule_file_line_and_keeps_new_findings(self):
        current = report([finding(10), finding(20), finding(10, "other/rule")])
        removed = filter_document(current, report([finding(10)]))
        self.assertEqual(1, removed)
        self.assertEqual([20, 10], [r["locations"][0]["physicalLocation"]["region"]["startLine"] for r in current["runs"][0]["results"]])
        self.assertEqual(1, current["runs"][0]["properties"]["lachesis_baseline_removed"])
        self.assertEqual([], current["runs"][0]["properties"]["lachesis_baseline_removed_fingerprints"])

    def test_cli_rewrites_current_report(self):
        from baseline_sarif import main
        with tempfile.TemporaryDirectory() as directory:
            current_path = Path(directory) / "current.sarif"
            baseline_path = Path(directory) / "baseline.sarif"
            current_path.write_text(json.dumps(report([finding(10), finding(20)])))
            baseline_path.write_text(json.dumps(report([finding(10)])))
            self.assertEqual(0, main([str(current_path), "--baseline", str(baseline_path)]))
            self.assertEqual(1, len(json.loads(current_path.read_text())["runs"][0]["results"]))

    def test_stable_fingerprint_removes_finding_after_line_move(self):
        current = report([finding(120, fingerprint="stable-1"), finding(20)])
        removed = filter_document(current, report([finding(12, fingerprint="stable-1")]))
        self.assertEqual(1, removed)
        self.assertEqual([20], [r["locations"][0]["physicalLocation"]["region"]["startLine"] for r in current["runs"][0]["results"]])
        self.assertEqual(["stable-1"], current["runs"][0]["properties"]["lachesis_baseline_removed_fingerprints"])


if __name__ == "__main__":
    unittest.main()
