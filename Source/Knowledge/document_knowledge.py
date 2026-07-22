import re
from pathlib import Path

from Source.Indexer.parser import UnityDocumentParser

DOCS_ROOT = Path(
    r"C:\AIEngineer\Documents\Unity\UnityDocumentation\Documentation\en"
)

HTML_EXTENSIONS = {".html", ".htm"}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")

# Retrieval vocabulary only: these terms do not decide an action or generate a
# plan. They let Turkish requests find the English offline Unity Manual archive
# without spending a second LLM call merely to translate search keywords.
TURKISH_UNITY_TERMS = {
    "buton": "button selectable onclick ui",
    "dugme": "button selectable onclick ui",
    "ekran": "screen canvas recttransform",
    "sigdir": "canvas scaler scale screen size recttransform",
    "sahne": "scene scenemanager loadscene",
    "gorsel": "image sprite texture",
    "resim": "image sprite texture",
    "efekt": "particle system visual effect",
    "parcacik": "particle system",
    "animasyon": "animation animator",
    "ses": "audio audiosource audioclip",
    "fizik": "physics rigidbody collider",
    "yatay": "landscape screen orientation",
    "dikey": "portrait screen orientation",
    "mobil": "mobile safe area canvas scaler",
    "dokunmatik": "touch input system",
}


class DocumentKnowledge:
    """
    Gercek Unity Manual / ScriptReference HTML sayfalarini
    (Documents/Unity/UnityDocumentation/Documentation/en altinda)
    tarayip, kullanici isteklerine gore ilgili dokuman icerigini
    (baslik, paragraf, kod bloklari) dondurur.
    """

    def __init__(self, docs_root=DOCS_ROOT):

        self.docs_root = Path(docs_root)

        self.parser = UnityDocumentParser()

        self._index = None

    def _build_index(self):

        index = []

        if not self.docs_root.exists():
            return index

        for file in self.docs_root.rglob("*"):

            if not file.is_file():
                continue

            if file.suffix.lower() not in HTML_EXTENSIONS:
                continue

            try:
                section = file.relative_to(self.docs_root).parts[0]
            except Exception:
                section = ""

            index.append({
                "name": file.stem,
                "path": file,
                "section": section
            })

        return index

    def _ensure_index(self):

        if self._index is None:
            self._index = self._build_index()

        return self._index

    def index_size(self):

        return len(self._ensure_index())

    def search(self, text, limit=3):

        index = self._ensure_index()

        normalized = self._normalize_search_text(text)
        tokens = set(t.lower() for t in TOKEN_RE.findall(normalized))
        for token in tuple(tokens):
            for turkish_term, unity_terms in TURKISH_UNITY_TERMS.items():
                # Turkish case suffixes commonly attach to the noun (butonu,
                # ekrana, sahneyi). Prefix matching keeps retrieval linguistic,
                # while never selecting or authorising a Unity operation.
                if token.startswith(turkish_term):
                    tokens.update(unity_terms.split())

        if not tokens:
            return []

        scored = []

        for entry in index:

            name_lower = entry["name"].lower()

            score = 0

            for t in tokens:

                if name_lower == t:
                    score += 100

                elif (
                    name_lower.startswith(t + ".")
                    or name_lower.startswith(t + "-")
                ):
                    score += 40

                elif t in name_lower:
                    score += 5

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: -x[0])

        seen = set()

        results = []

        for score, entry in scored:

            key = (
                entry["name"]
                .split(".")[0]
                .split("-")[0]
                .lower()
            )

            if key in seen:
                continue

            seen.add(key)

            results.append(entry)

            if len(results) >= limit:
                break

        return results

    @staticmethod
    def _normalize_search_text(text):
        table = str.maketrans({
            "ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
            "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
        })
        return str(text).translate(table).lower()

    def get_document(self, text, limit=3, max_paragraphs=8, max_code_blocks=4):

        results = []

        for entry in self.search(text, limit=limit):

            try:
                data = self.parser.parse(entry["path"])
            except Exception:
                continue

            results.append({

                "title": data["title"],

                "section": entry["section"],

                "path": str(entry["path"]),

                "paragraphs": data["paragraphs"][:max_paragraphs],

                "code_blocks": data["code_blocks"][:max_code_blocks]

            })

        return results
