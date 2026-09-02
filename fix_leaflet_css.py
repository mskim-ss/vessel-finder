from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
HTML_FILE = PROJECT_DIR / "vessel-finder-start.html"

OLD_HASH = "sha256-p4NxAoJBhIINfQ3WkUqYfN5M7QbD0pK9H4qFJ6m3q8E="
NEW_HASH = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="


def main():
    if not HTML_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(encoding="utf-8")

    if OLD_HASH not in html:
        print("잘못된 Leaflet CSS 해시를 찾지 못했습니다.")
        sys.exit(1)

    html = html.replace(OLD_HASH, NEW_HASH, 1)

    HTML_FILE.write_text(html, encoding="utf-8")

    print("Leaflet CSS SRI 해시 수정 완료")


if __name__ == "__main__":
    main()