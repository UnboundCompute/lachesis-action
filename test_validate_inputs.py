import unittest

from validate_inputs import validate


class ValidateInputsTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        self.assertEqual(
            [],
            validate(
                fail_on="none",
                buffer_pool_size="1073741824",
                c_jobs="",
                analyze_args="--prune --incremental",
                sarif_file="lachesis.sarif",
                source=".",
            ),
        )

    def test_rejects_invalid_values(self):
        errors = validate(
            fail_on="fatal",
            buffer_pool_size="0",
            c_jobs="workers",
            analyze_args="--source 'unterminated",
            sarif_file="/path/that/does/not/exist/report.sarif",
            source="/path/that/does/not/exist",
        )
        self.assertEqual(6, len(errors))

    def test_rejects_unknown_candidate_report(self):
        errors = validate(
            fail_on="none", buffer_pool_size="1", c_jobs="", analyze_args="",
            sarif_file="report.sarif", source=".", candidate_report="full",
        )
        self.assertIn("candidate-report must be one of: none, census", errors)

    def test_rejects_invalid_post_comments_mode(self):
        errors = validate(
            fail_on="none", buffer_pool_size="1", c_jobs="", analyze_args="",
            sarif_file="report.sarif", source=".", post_comments="maybe",
        )
        self.assertIn("post-comments must be one of: true, false", errors)

    def test_rejects_missing_baseline(self):
        errors = validate(
            fail_on="none", buffer_pool_size="1", c_jobs="", analyze_args="",
            sarif_file="report.sarif", source=".", baseline_sarif="missing.sarif",
        )
        self.assertTrue(any("baseline-sarif does not exist" in error for error in errors))

    def test_accepts_quoted_analyzer_args(self):
        self.assertEqual(
            [],
            validate(
                fail_on="error",
                buffer_pool_size="4096",
                c_jobs="2",
                analyze_args='--exclude "test fixtures"',
                sarif_file="report.sarif",
                source=".",
            ),
        )

    def test_rejects_empty_dependency_refs(self):
        errors = validate(
            fail_on="none",
            buffer_pool_size="4096",
            c_jobs="",
            analyze_args="",
            sarif_file="report.sarif",
            source=".",
            lachesis_ref=" ",
            atropos_ref="",
        )
        self.assertIn("lachesis-ref must not be empty", errors)
        self.assertIn("atropos-ref must not be empty", errors)

    def test_rejects_option_like_or_whitespace_refs(self):
        errors = validate(
            fail_on="none", buffer_pool_size="4096", c_jobs="",
            analyze_args="", sarif_file="report.sarif", source=".",
            lachesis_ref="--help", atropos_ref="feature branch",
        )
        self.assertEqual(2, len(errors))
        self.assertTrue(all("single Git ref" in error for error in errors))

    def test_rejects_invalid_frontend_timeout(self):
        errors = validate(
            fail_on="none", buffer_pool_size="4096", c_jobs="",
            analyze_args="", sarif_file="report.sarif", source=".",
            frontend_timeout="0",
        )
        self.assertIn("frontend-timeout must be a positive integer", errors)

    def test_rejects_invalid_query_timeout(self):
        errors = validate(
            fail_on="none", buffer_pool_size="4096", c_jobs="",
            analyze_args="", sarif_file="report.sarif", source=".",
            query_timeout="0",
        )
        self.assertIn("query-timeout must be a positive integer", errors)

    def test_rejects_invalid_build_timeout(self):
        errors = validate(
            fail_on="none", buffer_pool_size="4096", c_jobs="",
            analyze_args="", sarif_file="report.sarif", source=".",
            build_timeout="0",
        )
        self.assertIn("build-timeout must be a positive integer", errors)

    def test_rejects_analyzer_timeout_override(self):
        errors = validate(
            fail_on="none", buffer_pool_size="4096", c_jobs="",
            analyze_args="--prune --timeout=999999", sarif_file="report.sarif",
            source=".", frontend_timeout="300",
        )
        self.assertIn(
            "analyze-args must not override frontend-timeout; use the frontend-timeout input",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
