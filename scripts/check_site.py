#!/usr/bin/env python3
"""Validate the small static site without third-party dependencies."""

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang = ""
        self.title_parts: list[str] = []
        self.in_title = False
        self.description = ""
        self.main_ids: list[str] = []
        self.ids: list[str] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta" and values.get("name", "").lower() == "description":
            self.description = values.get("content", "")
        elif tag == "main":
            self.main_ids.append(values.get("id", ""))
        elif tag == "a":
            self.links.append(values)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def validate_page(path: Path) -> list[str]:
    parser = parse_page(path)
    errors: list[str] = []

    if parser.lang != "en":
        errors.append("html element must declare lang=\"en\"")
    if not "".join(parser.title_parts).strip():
        errors.append("page must have a non-empty title")
    if not parser.description.strip():
        errors.append("page must have a meta description")
    if parser.main_ids != ["main-content"]:
        errors.append("page must have one main landmark with id=\"main-content\"")
    if not any(link.get("href") == "#main-content" for link in parser.links):
        errors.append("page must link to #main-content for keyboard navigation")

    for identifier, count in Counter(parser.ids).items():
        if count > 1:
            errors.append(f'duplicate id="{identifier}"')

    for link in parser.links:
        href = link.get("href", "")
        parsed = urlsplit(href)
        if link.get("target") == "_blank" and "noopener" not in link.get("rel", "").split():
            errors.append(f"external link must use rel=\"noopener\": {href}")
        if not href or parsed.scheme or parsed.netloc:
            continue
        target = path if not parsed.path else path.parent / unquote(parsed.path)
        if not target.exists():
            errors.append(f"local link does not exist: {href}")
            continue
        if parsed.fragment and target.suffix.lower() in {".htm", ".html"}:
            target_parser = parser if target.resolve() == path.resolve() else parse_page(target)
            fragment = unquote(parsed.fragment)
            if fragment not in target_parser.ids:
                errors.append(f"local link fragment does not exist: {href}")

    return errors


def main() -> int:
    failures: list[str] = []
    pages = sorted(ROOT.glob("*.html"))
    if not pages:
        failures.append("no HTML pages found")

    for page in pages:
        failures.extend(f"{page.name}: {error}" for error in validate_page(page))

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}")
        return 1

    print(f"Validated {len(pages)} HTML pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
