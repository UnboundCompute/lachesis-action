import unittest

from lifecycle_sarif import apply_lifecycle


class LifecycleSarifTests(unittest.TestCase):
    def test_marks_new_and_unchanged_results(self):
        current = {"runs": [{"results": [
            {"properties": {"lachesisFinding": {"finding_id": "known"}}},
            {"properties": {"lachesisFinding": {"finding_id": "fresh"}}},
        ]}]}
        changed = apply_lifecycle(current, {"finding_lifecycle": {"observed_finding_ids": ["known"]}})
        self.assertEqual(2, changed)
        self.assertEqual("unchanged", current["runs"][0]["results"][0]["baselineState"])
        self.assertEqual("new", current["runs"][0]["results"][1]["baselineState"])
        self.assertEqual("compared", current["runs"][0]["properties"]["lachesis_lifecycle_state"])

    def test_ignores_results_without_stable_identity(self):
        current = {"runs": [{"results": [{"ruleId": "legacy"}]}]}
        self.assertEqual(0, apply_lifecycle(current, {"finding_lifecycle": {}}))
        self.assertNotIn("baselineState", current["runs"][0]["results"][0])


if __name__ == "__main__":
    unittest.main()
