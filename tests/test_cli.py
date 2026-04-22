import io
import unittest
from contextlib import redirect_stdout

from polymer_rediscover.cli import build_summary, main


class CliTests(unittest.TestCase):
    def test_build_summary_mentions_dailymed(self) -> None:
        summary = build_summary()
        self.assertIn("DailyMed", summary)
        self.assertIn("oral tablet", summary)

    def test_main_prints_summary(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            main()
        output = buffer.getvalue()
        self.assertIn("polymer_rediscover", output)


if __name__ == "__main__":
    unittest.main()
