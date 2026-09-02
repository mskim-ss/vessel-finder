from pathlib import Path
import sys

HTML_FILE = Path(
    r"C:\Users\Samsung\Documents\vessel-finder\vessel-finder-start.html"
)

OLD_HASH = (
    "sha512-gZwIG9x3wUXgVh4X9nFf6aYp7YF5m+zjG+Jc8Y3R4jP2Jq9p6D4q4Jr1eGm7kW8RrWzKzE2F7qJ8Y3Vx9yW5hQ=="
)

NEW_HASH = (
    "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
)


def main():
    if not HTML_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(encoding="utf-8")

    if OLD_HASH not in html:
        print("기존의 잘못된 Leaflet JS 해시를 찾지 못했습니다.")
        sys.exit(1)

    html = html.replace(OLD_HASH, NEW_HASH, 1)

    HTML_FILE.write_text(html, encoding="utf-8")

    print("Leaflet JavaScript SRI 해시 수정 완료")


if __name__ == "__main__":
    main()