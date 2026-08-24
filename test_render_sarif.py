import unittest

from render_sarif import render_html, render_markdown


class RenderSarifTests(unittest.TestCase):
    def report(self):
        return {"runs": [{"results": [{
            "ruleId": "lachesis/unguarded-sink",
            "level": "error",
            "baselineState": "new",
            "message": {"text": "missing guard <review>"},
            "properties": {"lachesis_lifecycle": "new"},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/app.py"}, "region": {"startLine": 12}}}],
            "codeFlows": [{"threadFlows": [{"locations": [{"location": {"physicalLocation": {"artifactLocation": {"uri": "src/input.py"}, "region": {"startLine": 2}}}}]}]}],
        }]}]}

    def test_markdown_keeps_location_flow_and_evidence(self):
        output = render_markdown(self.report(), {"engine_sha": "e" * 40, "catalog_sha": "a" * 40, "sarif": {"sha256": "f" * 64}})
        self.assertIn("src/app.py:12", output)
        self.assertIn("src/input.py:2", output)
        self.assertIn("missing guard <review>", output)
        self.assertIn("Evidence SHA-256", output)

    def test_html_escapes_untrusted_message_text(self):
        output = render_html(self.report())
        self.assertIn("&lt;review&gt;", output)
        self.assertNotIn("missing guard <review>", output)


if __name__ == "__main__":
    unittest.main()
