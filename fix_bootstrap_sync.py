from pathlib import Path
import sys

HTML_FILE = Path(
    r"C:\Users\Samsung\Documents\vessel-finder\vessel-finder-start.html"
)

OLD = "      await syncWatchlist();"

NEW = "      await syncWatchlist(true);"


def main():
    if not HTML_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(
        encoding="utf-8"
    )

    target = (
        '      connectEventStream();\n'
        '      await syncWatchlist();\n'
        '      await refreshLive();'
    )

    replacement = (
        '      connectEventStream();\n'
        '      await syncWatchlist(true);\n'
        '      await refreshLive();'
    )

    if target not in html:
        print(
            "bootstrapLive()의 동기화 부분을 찾지 못했습니다."
        )
        sys.exit(1)

    html = html.replace(
        target,
        replacement,
        1
    )

    HTML_FILE.write_text(
        html,
        encoding="utf-8"
    )

    print(
        "페이지 시작 시 watchlist 강제 동기화 적용 완료"
    )


if __name__ == "__main__":
    main()