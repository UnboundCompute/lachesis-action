import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from gate_sarif import SarifError, findings_at_or_above, main


class GateSarifTests(unittest.TestCase):
    def _write(self, value):
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".sarif", delete=False)
        with handle:
            json.dump(value, handle)
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_threshold_filters_levels(self):
        path = self._write({"runs": [{"results": [
            {"level": "note"}, {"level": "warning"}, {"level": "error"},
        ]}]})
        self.assertEqual(2, len(findings_at_or_above(path, "warning")))
        self.assertEqual(1, len(findings_at_or_above(path, "error")))

    def test_malformed_report_is_actionable(self):
        path = self._write({"version": "2.1.0"})
        with self.assertRaisesRegex(SarifError, "no runs"):
            findings_at_or_above(path, "warning")

    def test_main_returns_configuration_error(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, main(["missing.sarif", "fatal"]))


if __name__ == "__main__":
    unittest.main()
