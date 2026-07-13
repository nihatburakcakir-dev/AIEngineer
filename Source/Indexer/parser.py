from pathlib import Path
from bs4 import BeautifulSoup


class UnityDocumentParser:

    def parse(self, html_file: Path):

        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "lxml")

        title = ""

        if soup.title:
            title = soup.title.get_text(strip=True)

        paragraphs = []

        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)

            if len(text) > 20:
                paragraphs.append(text)

        code_blocks = []

        for pre in soup.find_all("pre"):
            code = pre.get_text("\n", strip=True)

            if code:
                code_blocks.append(code)

        return {

            "title": title,

            "paragraphs": paragraphs,

            "code_blocks": code_blocks

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