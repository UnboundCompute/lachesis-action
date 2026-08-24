from pathlib import Path
import unittest


class ExampleWorkflowTests(unittest.TestCase):
    def test_engine_pin_is_not_the_action_release_tag(self):
        workflow = Path(__file__).with_name("example-workflow.yml").read_text(encoding="utf-8")
        self.assertNotIn('lachesis-ref: "v1.0.0"', workflow)
        self.assertIn('lachesis-ref: "v0.1.7"', workflow)
        self.assertIn('atropos-ref: "v1.7.1"', workflow)


if __name__ == "__main__":
    unittest.main()
