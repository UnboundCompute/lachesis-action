from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent


class ReleaseMetadataTests(unittest.TestCase):
    def test_version_matches_changelog(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(
            changelog, re.compile(rf"^## \[{re.escape(version)}\]$", re.MULTILINE),
        )


if __name__ == "__main__":
    unittest.main()
