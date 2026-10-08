import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch
import sys

from patent_core import extract_patent, generate_explanation, normalize_patent_id, to_markdown

SAMPLE = '''<html><head><meta name="citation_title" content="A toy sensor"/>
<meta name="citation_abstract" content="A sensor includes a sensing unit and a processor."/></head>
<body><div class="claim" num="1"><div class="claim-text">1. A sensor comprising a sensing unit and a processor.</div></div></body></html>'''

class TestPatentCore(unittest.TestCase):
    def test_patent_id(self):
        self.assertEqual(normalize_patent_id("US 7654321 B2"), "US7654321B2")
        self.assertEqual(normalize_patent_id("https://patents.google.com/patent/US7654321B2/en"), "US7654321B2")
        with self.assertRaises(ValueError):
            normalize_patent_id("https://example.com/patent/US7654321B2")

    def test_extract(self):
        patent = extract_patent(SAMPLE, "US7654321B2")
        self.assertEqual(patent.title, "A toy sensor")
        self.assertTrue(patent.first_claim.startswith("1. A sensor"))
        self.assertIn("sensing unit", patent.abstract)
        report = to_markdown(patent, "技术解读")
        self.assertIn("技术解读", report)
        self.assertIn("US7654321B2", report)

    def test_missing_abstract_fails(self):
        with self.assertRaises(ValueError):
            extract_patent("<html><title>Test</title></html>", "US7654321B2")

    def test_deepseek_request(self):
        record = extract_patent(SAMPLE, "US7654321B2")
        sdk = ModuleType("openai")
        sdk.OpenAI = MagicMock()
        client = sdk.OpenAI.return_value
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="  技术解读  "))]
        )

        with patch.dict(sys.modules, {"openai": sdk}):
            self.assertEqual(generate_explanation(record, "test-key"), "技术解读")

        sdk.OpenAI.assert_called_once_with(
            api_key="test-key", base_url="https://api.deepseek.com", timeout=50
        )
        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "deepseek-flash")
        self.assertEqual([item["role"] for item in request["messages"]], ["system", "user"])
        self.assertIn("sensing unit", request["messages"][1]["content"])
        self.assertEqual(request["extra_body"], {"thinking": {"type": "disabled"}})

if __name__ == "__main__":
    unittest.main()
