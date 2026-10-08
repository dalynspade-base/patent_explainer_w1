import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch
import sys
import requests

from patent_core import extract_patent, fetch_patent, generate_explanation, make_manual_patent, normalize_patent_id, to_markdown

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

    def test_manual_patent_requires_source_text(self):
        with self.assertRaisesRegex(ValueError, "标题和摘要不能为空"):
            make_manual_patent("US7654321B2", "A title", "  ")
        record = make_manual_patent("US7654321B2", " A title ", " An abstract. ")
        self.assertEqual(record.abstract, "An abstract.")
        self.assertEqual(record.first_claim, "")

    def test_fetch_retries_503_then_succeeds(self):
        unavailable = requests.Response()
        unavailable.status_code = 503
        unavailable.url = "https://patents.google.com/patent/US7654321B2/en"
        success = requests.Response()
        success.status_code = 200
        success._content = SAMPLE.encode("utf-8")
        with patch("patent_core.requests.get", side_effect=[unavailable, success]) as get, patch("patent_core.time.sleep") as sleep:
            record = fetch_patent("US7654321B2")
        self.assertEqual(record.title, "A toy sensor")
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_fetch_503_offers_manual_fallback(self):
        unavailable = requests.Response()
        unavailable.status_code = 503
        unavailable.url = "https://patents.google.com/patent/US7654321B2/en"
        with patch("patent_core.requests.get", return_value=unavailable) as get, patch("patent_core.time.sleep"):
            with self.assertRaisesRegex(RuntimeError, "手动粘贴原文"):
                fetch_patent("US7654321B2")
        self.assertEqual(get.call_count, 3)

    def test_fetch_404_does_not_retry(self):
        missing = requests.Response()
        missing.status_code = 404
        missing.url = "https://patents.google.com/patent/US7654321B2/en"
        with patch("patent_core.requests.get", return_value=missing) as get, patch("patent_core.time.sleep") as sleep:
            with self.assertRaises(RuntimeError):
                fetch_patent("US7654321B2")
        get.assert_called_once()
        sleep.assert_not_called()

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
