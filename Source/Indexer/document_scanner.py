from pathlib import Path

# Unity dokümanlarının bulunduğu klasör
DOCS_PATH = Path(r"C:\AIEngineer\Documents\Unity\UnityDocumentation")

# HTML uzantıları
HTML_EXTENSIONS = {".html", ".htm"}

html_files = []

for file in DOCS_PATH.rglob("*"):
    if file.suffix.lower() in HTML_EXTENSIONS:
        html_files.append(file)

print("=" * 50)
print("Unity Documentation Scanner")
print("=" * 50)

print(f"Toplam HTML dosyası : {len(html_files)}")

print("\nİlk 20 dosya:\n")

for file in html_files[:20]:
    print(file.relative_to(DOCS_PATH))