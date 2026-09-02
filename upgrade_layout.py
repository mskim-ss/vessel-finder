from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
HTML_FILE = PROJECT_DIR / "vessel-finder-start.html"

MARKER = "<!-- VESSEL_WORKSPACE_LAYOUT -->"

INJECT = r'''
<!-- VESSEL_WORKSPACE_LAYOUT -->

<style>
  /*
   * 선박 리스트 + 지도 2단 구성
   */
  .vessel-workspace {
    width: min(1500px, calc(100vw - 32px));
    margin: 24px auto 0;
    display: grid;
    grid-template-columns: minmax(360px, 0.85fr) minmax(620px, 1.7fr);
    gap: 18px;
    align-items: start;
  }

  /*
   * 기존 오늘의 선박 동향 영역
   */
  .vessel-workspace #trendSection {
    width: 100%;
    min-width: 0;
    margin: 0;
    box-sizing: border-box;
  }

  /*
   * 기존 지도 영역
   */
  .vessel-workspace #vessel-map-section {
    width: 100%;
    min-width: 0;
    margin: 0;
    box-sizing: border-box;
  }

  /*
   * 지도 높이
   */
  .vessel-workspace #vessel-map {
    height: 620px;
  }

  /*
   * 선박 리스트가 너무 넓게 퍼지지 않도록 조정
   */
  .vessel-workspace #trendSection table {
    width: 100%;
    table-layout: fixed;
  }

  /*
   * 긴 텍스트는 적당히 줄바꿈
   */
  .vessel-workspace #trendSection td,
  .vessel-workspace #trendSection th {
    word-break: keep-all;
  }

  /*
   * 데스크톱에서는 선박 리스트를 지도와 함께 고정된 영역처럼 보이게
   */
  @media (min-width: 1100px) {
    .vessel-workspace #trendSection {
      position: sticky;
      top: 16px;
    }
  }

  /*
   * 태블릿
   */
  @media (max-width: 1099px) {
    .vessel-workspace {
      grid-template-columns: 1fr;
      width: min(100% - 24px, 900px);
    }

    .vessel-workspace #vessel-map-section {
      order: 1;
    }

    .vessel-workspace #trendSection {
      order: 2;
      position: static;
    }
  }

  /*
   * 모바일
   */
  @media (max-width: 700px) {
    .vessel-workspace {
      width: calc(100vw - 20px);
      gap: 12px;
    }

    .vessel-workspace #vessel-map {
      height: 420px;
    }
  }

  /*
   * 지도 하단 정보 카드
   */
  .vessel-workspace #vessel-map-info {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (min-width: 1400px) {
    .vessel-workspace #vessel-map-info {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }
</style>

<script>
(function () {
  "use strict";

  function arrangeVesselWorkspace() {
    const trendSection =
      document.getElementById("trendSection");

    const mapSection =
      document.getElementById("vessel-map-section");

    if (!trendSection || !mapSection) {
      return;
    }

    /*
     * 이미 배치된 경우 중복 실행 방지
     */
    if (
      trendSection.parentElement?.classList.contains(
        "vessel-workspace"
      )
    ) {
      return;
    }

    /*
     * 두 영역을 담을 새로운 작업 공간
     */
    const workspace =
      document.createElement("div");

    workspace.className =
      "vessel-workspace";

    /*
     * 현재 trendSection 위치에 workspace를 삽입
     */
    trendSection.parentNode.insertBefore(
      workspace,
      trendSection
    );

    /*
     * 선박 리스트와 지도를 workspace로 이동
     */
    workspace.appendChild(trendSection);
    workspace.appendChild(mapSection);

    /*
     * Leaflet은 DOM 크기가 바뀐 뒤 다시 계산해야 합니다.
     */
    window.setTimeout(function () {
      window.dispatchEvent(
        new Event("resize")
      );
    }, 150);
  }

  if (
    document.readyState === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      arrangeVesselWorkspace
    );
  } else {
    arrangeVesselWorkspace();
  }
})();
</script>

<!-- VESSEL_WORKSPACE_LAYOUT_END -->
'''


def main():
    if not HTML_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(encoding="utf-8")

    if MARKER in html:
        print("레이아웃 개선 코드가 이미 추가되어 있습니다.")
        return

    body_end = html.lower().rfind("</body>")

    if body_end == -1:
        print("</body> 태그를 찾지 못했습니다.")
        sys.exit(1)

    html = (
        html[:body_end]
        + INJECT
        + "\n"
        + html[body_end:]
    )

    HTML_FILE.write_text(
        html,
        encoding="utf-8"
    )

    print("선박 리스트 + 지도 2단 레이아웃 추가 완료")


if __name__ == "__main__":
    main()