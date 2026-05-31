import unittest

from config import EmailConfig
from email_notify import CheckinResult, EmailNotifier


class EmailNotifierTests(unittest.TestCase):
    def test_html_report_links_to_current_project(self):
        notifier = EmailNotifier(EmailConfig())
        result = CheckinResult("ccgfw", "user@example.com", "https://www.ccgfw.top")

        html = notifier._build_html_body([result])

        self.assertIn("https://github.com/jiayaogege/word-checkin", html)
        self.assertIn("word-checkin", html)
        self.assertNotIn("https://github.com/runoober/jichang_checkin", html)
        self.assertNotIn(">jichang_checkin</a>", html)


if __name__ == "__main__":
    unittest.main()
