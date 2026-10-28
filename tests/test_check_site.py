import tempfile
import unittest
from pathlib import Path

from scripts.check_site import validate_page


def page(body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <title>Test page</title>
  <meta name="description" content="Test description">
</head>
<body>
  <a href="#main-content">Skip to content</a>
  <main id="main-content">{body}</main>
</body>
</html>
"""


class SiteValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_accepts_existing_same_page_and_cross_page_fragments(self) -> None:
        source = self.write(
            "index.html",
            page('<section id="faq"></section><a href="#faq">FAQ</a>'
                 '<a href="privacy.html#contact">Contact</a>'),
        )
        self.write("privacy.html", page('<section id="contact"></section>'))

        self.assertEqual(validate_page(source), [])

    def test_rejects_missing_same_page_and_cross_page_fragments(self) -> None:
        source = self.write(
            "index.html",
            page('<a href="#missing">Missing</a>'
                 '<a href="privacy.html#also-missing">Also missing</a>'),
        )
        self.write("privacy.html", page('<section id="contact"></section>'))

        self.assertEqual(
            validate_page(source),
            [
                "local link fragment does not exist: #missing",
                "local link fragment does not exist: privacy.html#also-missing",
            ],
        )

    def test_rejects_duplicate_ids(self) -> None:
        source = self.write(
            "index.html",
            page('<section id="faq"></section><aside id="faq"></aside>'),
        )

        self.assertEqual(validate_page(source), ['duplicate id="faq"'])


if __name__ == "__main__":
    unittest.main()
