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
  <link rel="canonical" href="https://example.com/">
  <meta property="og:title" content="Test page">
  <meta property="og:description" content="Test description">
  <meta property="og:url" content="https://example.com/">
</head>
<body>
  <a href="#main-content">Skip to content</a>
  <main id="main-content"><h1>Test page</h1>{body}</main>
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

    def test_rejects_missing_multiple_or_empty_primary_headings(self) -> None:
        cases = {
            "missing": (
                page("").replace("<h1>Test page</h1>", ""),
                "page must have exactly one h1 heading",
            ),
            "multiple": (
                page("<h1>Another heading</h1>"),
                "page must have exactly one h1 heading",
            ),
            "empty": (
                page("").replace("<h1>Test page</h1>", "<h1> </h1>"),
                "page h1 heading must not be empty",
            ),
        }

        for name, (content, expected) in cases.items():
            with self.subTest(name=name):
                source = self.write(f"{name}.html", content)
                self.assertIn(expected, validate_page(source))

    def test_rejects_incomplete_or_inconsistent_share_metadata(self) -> None:
        source = self.write(
            "index.html",
            page("")
            .replace('<meta property="og:title" content="Test page">', "")
            .replace(
                '<meta property="og:url" content="https://example.com/">',
                '<meta property="og:url" content="https://example.com/other">',
            ),
        )

        self.assertEqual(
            validate_page(source),
            ["page must define og:title", "og:url must match the canonical URL"],
        )


if __name__ == "__main__":
    unittest.main()
