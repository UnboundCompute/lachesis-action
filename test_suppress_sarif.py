import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from suppress_sarif import SuppressionError, _load_rules, apply


def report(results):
    return {"version": "2.1.0", "runs": [{"results": results}]}


def finding(line, rule="lachesis/unguarded-sink"):
    return {"ruleId": rule, "locations": [{"physicalLocation": {
        "artifactLocation": {"uri": "src/app.py"}, "region": {"startLine": line},
    }}]}


class SuppressSarifTests(unittest.TestCase):
    def test_applies_rule_path_line_and_audit_metadata(self):
        expiry = (dt.date.today() + dt.timedelta(days=30)).isoformat()
        rules = [{"ruleId": "lachesis/unguarded-sink", "path": "src/*.py", "line": 10,
                  "reason": "accepted until migration", "expires": expiry}]
        current = report([finding(10), finding(20)])
        self.assertEqual(1, apply(current, rules))
        result = current["runs"][0]["results"][0]
        self.assertEqual("accepted until migration", result["suppressions"][0]["justification"])
        self.assertEqual(expiry, result["properties"]["lachesis_suppression_expires"])
        self.assertNotIn("suppressions", current["runs"][0]["results"][1])

    def test_expired_records_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suppressions.json"
            path.write_text(json.dumps({"version": 1, "suppressions": [{
                "ruleId": "x", "path": "*", "reason": "old", "expires": "2000-01-01"
            }]}))
            with self.assertRaisesRegex(SuppressionError, "expired"):
                _load_rules(path)


if __name__ == "__main__":
    unittest.main()
