from pathlib import Path
import unittest


class ActionMetadataTests(unittest.TestCase):
    def test_dependency_defaults_are_reviewed_releases(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn('lachesis-ref:\n    description:', metadata)
        self.assertIn('    default: "v0.1.7"', metadata)
        self.assertIn('    default: "v1.7.1"', metadata)

    def test_dependency_checkouts_are_noninteractive(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertEqual(2, metadata.count('GIT_TERMINAL_PROMPT: "0"'))

    def test_dependency_installs_have_bounded_noninteractive_pip(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertEqual(2, metadata.count('PIP_NO_INPUT: "1"'))
        self.assertEqual(2, metadata.count('PIP_DISABLE_PIP_VERSION_CHECK: "1"'))
        self.assertEqual(2, metadata.count('PIP_DEFAULT_TIMEOUT: "60"'))

    def test_dependency_checkouts_abort_stalled_http_transfers(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertEqual(2, metadata.count('GIT_HTTP_LOW_SPEED_LIMIT: "1000"'))
        self.assertEqual(2, metadata.count('GIT_HTTP_LOW_SPEED_TIME: "60"'))

    def test_candidate_census_is_explicitly_opt_in(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn("candidate-report:", metadata)
        self.assertIn('default: "none"', metadata)
        self.assertIn("inputs.candidate-report == 'census'", metadata)

    def test_reports_are_exposed_as_action_outputs(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn("sarif-file:", metadata)
        self.assertIn("candidate-report-file:", metadata)
        self.assertIn("id: export-sarif", metadata)
        self.assertIn("id: export-candidates", metadata)

    def test_sarif_export_receives_dependency_provenance(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn("--engine-sha", metadata)
        self.assertIn("--catalog-sha", metadata)
        self.assertIn("--toolchain-fingerprint", metadata)

    def test_hosted_comments_are_opt_out_and_pr_only(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn("post-comments:", metadata)
        self.assertIn('default: "true"', metadata)
        self.assertIn("inputs.post-comments == 'true' && github.event_name == 'pull_request'", metadata)

    def test_baseline_filter_runs_before_gate(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn("baseline-sarif:", metadata)
        self.assertIn("baseline_sarif.py", metadata)
        self.assertLess(metadata.index("baseline_sarif.py"), metadata.index("name: Gate on findings"))

    def test_suppression_filter_runs_before_gate(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertIn("suppression-file:", metadata)
        self.assertIn("suppress_sarif.py", metadata)
        self.assertLess(metadata.index("suppress_sarif.py"), metadata.index("name: Gate on findings"))


if __name__ == "__main__":
    unittest.main()
