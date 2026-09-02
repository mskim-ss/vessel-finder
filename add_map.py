from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
HTML_FILE = PROJECT_DIR / "vessel-finder-start.html"

MARKER = "<!-- VESSEL_FINDER_MAP_START -->"

MAP_HTML = r'''
<!-- VESSEL_FINDER_MAP_START -->

<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIINfQ3WkUqYfN5M7QbD0pK9H4qFJ6m3q8E="
  crossorigin=""
/>

<style>
  #vessel-map-section {
    margin-top: 24px;
    padding: 16px;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    background: #0b1b2e;
  }

  #vessel-map-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
  }

  #vessel-map-title h2 {
    margin: 0;
  }

  #vessel-map-status {
    font-size: 13px;
    opacity: 0.75;
  }

  #vessel-map {
    width: 100%;
    height: 480px;
    border-radius: 12px;
    overflow: hidden;
  }

  .vessel-map-popup {
    font-size: 13px;
    line-height: 1.5;
  }

  .vessel-map-popup strong {
    font-size: 15px;
  }
</style>

<section id="vessel-map-section">
  <div id="vessel-map-title">
    <h2>실시간 선박 위치</h2>
    <div id="vessel-map-status">AIS 데이터 대기 중</div>
  </div>

  <div id="vessel-map"></div>
</section>

<script
  src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
  crossorigin=""
></script>

<script>
(function () {
  "use strict";

  let map = null;
  let vesselMarkers = {};
  let trailLines = {};
  let initialized = false;

  const HCMC = [10.7769, 106.7009];

  function formatTime(timestamp) {
    if (!timestamp) return "-";

    const date = new Date(timestamp);

    return date.toLocaleString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  }

  function initMap() {
    if (initialized) return;

    if (typeof L === "undefined") {
      document.getElementById("vessel-map-status").textContent =
        "지도 라이브러리를 불러오지 못했습니다.";
      return;
    }

    map = L.map("vessel-map").setView(HCMC, 4);

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 18,
        attribution: "&copy; OpenStreetMap contributors"
      }
    ).addTo(map);

    L.marker(HCMC)
      .addTo(map)
      .bindPopup("<strong>호치민</strong><br>기준 위치");

    initialized = true;
  }

  function createVesselIcon() {
    return L.divIcon({
      className: "",
      html: `
        <div style="
          width: 22px;
          height: 22px;
          border-radius: 50%;
          background: #46c6b5;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,.45);
        "></div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });
  }

  function updateMap(data) {
    initMap();

    if (!map) return;

    const vessels = data.vessels || {};
    const keys = Object.keys(vessels);

    if (keys.length === 0) {
      document.getElementById("vessel-map-status").textContent =
        data.connected
          ? "AIS 연결됨 · 선박 위치 수신 대기 중"
          : "AIS 연결 대기 중";
      return;
    }

    document.getElementById("vessel-map-status").textContent =
      `실시간 AIS ${keys.length}척 수신 중`;

    const bounds = [];

    for (const mmsi of keys) {
      const vessel = vessels[mmsi];

      if (
        typeof vessel.latitude !== "number" ||
        typeof vessel.longitude !== "number"
      ) {
        continue;
      }

      const lat = vessel.latitude;
      const lon = vessel.longitude;

      bounds.push([lat, lon]);

      const popup = `
        <div class="vessel-map-popup">
          <strong>${escapeHtml(vessel.shipName || "Unknown vessel")}</strong><br>
          MMSI: ${escapeHtml(vessel.mmsi || mmsi)}<br>
          위치: ${lat.toFixed(5)}, ${lon.toFixed(5)}<br>
          속도: ${
            typeof vessel.sog === "number"
              ? vessel.sog.toFixed(1) + " kn"
              : "-"
          }<br>
          방향: ${
            typeof vessel.cog === "number"
              ? vessel.cog.toFixed(0) + "°"
              : "-"
          }<br>
          마지막 수신: ${formatTime(vessel.receivedAt)}
        </div>
      `;

      if (!vesselMarkers[mmsi]) {
        vesselMarkers[mmsi] = L.marker(
          [lat, lon],
          { icon: createVesselIcon() }
        )
          .addTo(map)
          .bindPopup(popup);
      } else {
        vesselMarkers[mmsi].setLatLng([lat, lon]);
        vesselMarkers[mmsi].setPopupContent(popup);
      }
    }

    /*
     * 모든 선박이 보이도록 처음 데이터를 받은 경우에만
     * 지도 범위를 자동 조정합니다.
     */
    if (bounds.length > 0 && !map._vesselFinderFitted) {
      map.fitBounds(bounds, {
        padding: [40, 40],
        maxZoom: 7
      });

      map._vesselFinderFitted = true;
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function refreshLiveMap() {
    try {
      const response = await fetch("/api/live-status", {
        cache: "no-store"
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      updateMap(data);
    } catch (error) {
      console.error("Vessel map update failed:", error);

      const status = document.getElementById("vessel-map-status");

      if (status) {
        status.textContent = "AIS 상태 확인 중";
      }
    }
  }

  function start() {
    initMap();
    refreshLiveMap();

    /*
     * 5초마다 서버의 최신 AIS 데이터를 확인합니다.
     */
    setInterval(refreshLiveMap, 5000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
</script>

<!-- VESSEL_FINDER_MAP_END -->
'''

def main():
    if not HTML_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(encoding="utf-8")

    # 이미 추가된 경우 중복 삽입 방지
    if MARKER in html:
        print("지도 기능이 이미 추가되어 있습니다.")
        return

    insert_position = html.lower().rfind("</body>")

    if insert_position == -1:
        print("</body> 태그를 찾지 못했습니다.")
        sys.exit(1)

    new_html = (
        html[:insert_position]
        + MAP_HTML
        + "\n"
        + html[insert_position:]
    )

    HTML_FILE.write_text(new_html, encoding="utf-8")

    print("지도 기능 추가 완료")
    print(f"수정 파일: {HTML_FILE}")


if __name__ == "__main__":
    main()