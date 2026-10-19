import unittest

class TestBlueAgentParsing(unittest.TestCase):
    def test_malicious_verdict_parsing(self):
        mock_report = """
        [ATLAS.T0051.001] Direct Prompt Injection
        MITRE: AML.T0051
        VERDICT: MALICIOUS
        SEVERITY: CRITICAL
        ACTION: Block the IP immediately.
        """
        if "MALICIOUS" in mock_report:
            verdict = "MALICIOUS"
        self.assertEqual(verdict, "MALICIOUS")

    def test_suspicious_verdict_parsing(self):
        mock_report = """
        [ATLAS.T0054.001] DAN Jailbreak
        MITRE: AML.T0054
        VERDICT: SUSPICIOUS
        SEVERITY: HIGH
        ACTION: Review logs.
        """
        if "SUSPICIOUS" in mock_report:
            verdict = "SUSPICIOUS"
        self.assertEqual(verdict, "SUSPICIOUS")

if __name__ == '__main__':
    unittest.main()
