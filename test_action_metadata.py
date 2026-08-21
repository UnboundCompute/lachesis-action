from pathlib import Path
import unittest


class ActionMetadataTests(unittest.TestCase):
    def test_dependency_checkouts_are_noninteractive(self):
        metadata = Path(__file__).with_name("action.yml").read_text(encoding="utf-8")
        self.assertEqual(2, metadata.count('GIT_TERMINAL_PROMPT: "0"'))


if __name__ == "__main__":
    unittest.main()
