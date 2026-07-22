from pathlib import Path
from html.parser import HTMLParser
import re


class _UnityHTMLParser(HTMLParser):
    """Extract the document fields we need without third-party dependencies."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.paragraphs = []
        self.code_blocks = []
        self._capture = None
        self._depth = 0
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        tag = tag.casefold()
        if self._capture is not None:
            self._depth += 1
            return
        if tag in {"title", "p", "pre"}:
            self._capture = tag
            self._depth = 0
            self._buffer = []

    def handle_endtag(self, tag):
        if self._capture is None:
            return
        if self._depth > 0:
            self._depth -= 1
            return
        if tag.casefold() != self._capture:
            return
        raw = "".join(self._buffer)
        if self._capture == "pre":
            text = raw.strip()
            if text:
                self.code_blocks.append(text)
        else:
            text = re.sub(r"\s+", " ", raw).strip()
            if self._capture == "title" and not self.title:
                self.title = text
            elif self._capture == "p" and len(text) > 20:
                self.paragraphs.append(text)
        self._capture = None
        self._depth = 0
        self._buffer = []

    def handle_data(self, data):
        if self._capture is not None:
            self._buffer.append(data)


class UnityDocumentParser:

    def parse(self, html_file: Path):

        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            parser = _UnityHTMLParser()
            parser.feed(f.read())
            parser.close()

        return {

            "title": parser.title,

            "paragraphs": parser.paragraphs,

            "code_blocks": parser.code_blocks

        }


if __name__ == "__main__":

    test_file = Path(
        r"C:\AIEngineer\Documents\Unity\UnityDocumentation\Documentation\en\Manual\2DFeature.html"
    )

    parser = UnityDocumentParser()

    data = parser.parse(test_file)

    print("=" * 60)

    print("TITLE")
    print(data["title"])

    print("=" * 60)

    print("PARAGRAPH SAYISI :", len(data["paragraphs"]))

    print("KOD BLOĞU SAYISI :", len(data["code_blocks"]))

    print("=" * 60)

    if data["paragraphs"]:
        print(data["paragraphs"][0])
