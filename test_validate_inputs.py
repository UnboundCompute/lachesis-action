import unittest

from validate_inputs import validate


class ValidateInputsTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        self.assertEqual(
            [],
            validate(
                upload="true",
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
            upload="yes",
            fail_on="fatal",
            buffer_pool_size="0",
            c_jobs="workers",
            analyze_args="--source 'unterminated",
            sarif_file="/path/that/does/not/exist/report.sarif",
            source="/path/that/does/not/exist",
        )
        self.assertEqual(7, len(errors))

    def test_accepts_quoted_analyzer_args(self):
        self.assertEqual(
            [],
            validate(
                upload="false",
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
            upload="true",
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


if __name__ == "__main__":
    unittest.main()
