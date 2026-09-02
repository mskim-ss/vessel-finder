from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
HTML_FILE = PROJECT_DIR / "vessel-finder-start.html"

START_MARKER = "<!-- VESSEL_FINDER_MAP_START -->"
END_MARKER = "<!-- VESSEL_FINDER_MAP_END -->"

NEW_MAP = r'''
<!-- VESSEL_FINDER_MAP_START -->

<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
  crossorigin=""
/>

<style>
  #vessel-map-section {
    margin-top: 24px;
    padding: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
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
    opacity: 0.8;
  }

  #vessel-map {
    width: 100%;
    height: 520px;
    border-radius: 12px;
    overflow: hidden;
  }

  #vessel-map-info {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
  }

  .vessel-map-card {
    padding: 12px 14px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.07);
  }

  .vessel-map-card-label {
    font-size: 11px;
    opacity: 0.65;
    margin-bottom: 5px;
  }

  .vessel-map-card-value {
    font-size: 15px;
    font-weight: 700;
  }

  .vessel-ship-icon {
    width: 38px;
    height: 38px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .vessel-ship-arrow {
    width: 0;
    height: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-bottom: 30px solid #46c6b5;
    filter: drop-shadow(0 2px 5px rgba(0,0,0,0.45));
  }

  .vessel-map-popup {
    font-size: 13px;
    line-height: 1.55;
  }

  .vessel-map-popup strong {
    font-size: 15px;
  }

  @media (max-width: 900px) {
    #vessel-map-info {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }
</style>

<section id="vessel-map-section">
  <div id="vessel-map-title">
    <h2>실시간 선박 위치</h2>
    <div id="vessel-map-status">AIS 데이터 대기 중</div>
  </div>

  <div id="vessel-map"></div>

  <div id="vessel-map-info">
    <div class="vessel-map-card">
      <div class="vessel-map-card-label">현재 속도</div>
      <div class="vessel-map-card-value" id="map-speed">-</div>
    </div>

    <div class="vessel-map-card">
      <div class="vessel-map-card-label">진행 방향</div>
      <div class="vessel-map-card-value" id="map-course">-</div>
    </div>

    <div class="vessel-map-card">
      <div class="vessel-map-card-label">호치민까지</div>
      <div class="vessel-map-card-value" id="map-distance">-</div>
    </div>

    <div class="vessel-map-card">
      <div class="vessel-map-card-label">단순 예상 ETA</div>
      <div class="vessel-map-card-value" id="map-eta">-</div>
    </div>
  </div>
</section>

<script
  src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
  integrity="sha512-gZwIG9x3wUXgVh4X9nFf6aYp7YF5m+zjG+Jc8Y3R4jP2Jq9p6D4q4Jr1eGm7kW8RrWzKzE2F7qJ8Y3Vx9yW5hQ=="
  crossorigin=""
></script>

<script>
(function () {
  "use strict";

  let map = null;
  let initialized = false;

  const vesselMarkers = {};
  const routeLines = {};

  /*
   * 호치민 기준점.
   * 현재는 호치민 시내 기준 좌표를 사용합니다.
   * 향후 실제 입항 선석/항만 기준으로 조정할 수 있습니다.
   */
  const HCMC = [10.7769, 106.7009];

  function byId(id) {
    return document.getElementById(id);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

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

  function formatEta(timestamp) {
    if (!timestamp || !Number.isFinite(timestamp)) {
      return "-";
    }

    const date = new Date(timestamp);

    return date.toLocaleString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371;

    const toRad = (value) => value * Math.PI / 180;

    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);

    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) ** 2;

    return R * 2 * Math.atan2(
      Math.sqrt(a),
      Math.sqrt(1 - a)
    );
  }

  function createShipIcon(course) {
    const angle = Number.isFinite(course) ? course : 0;

    return L.divIcon({
      className: "",
      html: `
        <div
          class="vessel-ship-icon"
          style="transform: rotate(${angle}deg);"
        >
          <div class="vessel-ship-arrow"></div>
        </div>
      `,
      iconSize: [38, 38],
      iconAnchor: [19, 19]
    });
  }

  function initMap() {
    if (initialized) return;

    if (typeof L === "undefined") {
      byId("vessel-map-status").textContent =
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
      .bindPopup(`
        <div class="vessel-map-popup">
          <strong>HO CHI MINH</strong><br>
          도착 기준점
        </div>
      `);

    initialized = true;
  }

  function updateInfo(vessel) {
    const speed = Number(vessel.sog);

    byId("map-speed").textContent =
      Number.isFinite(speed)
        ? `${speed.toFixed(1)} kn`
        : "-";

    const course = Number(vessel.cog);

    byId("map-course").textContent =
      Number.isFinite(course)
        ? `${course.toFixed(0)}°`
        : "-";

    if (
      Number.isFinite(vessel.latitude) &&
      Number.isFinite(vessel.longitude)
    ) {
      const distance = haversineKm(
        vessel.latitude,
        vessel.longitude,
        HCMC[0],
        HCMC[1]
      );

      byId("map-distance").textContent =
        `${Math.round(distance).toLocaleString("ko-KR")} km`;

      /*
       * 1 kn = 1.852 km/h
       *
       * 현재 속도가 0이거나 없는 경우 ETA를 계산하지 않습니다.
       */
      if (speed > 0) {
        const hours = distance / (speed * 1.852);
        const eta = Date.now() + hours * 60 * 60 * 1000;

        byId("map-eta").textContent = formatEta(eta);
      } else {
        byId("map-eta").textContent = "-";
      }
    } else {
      byId("map-distance").textContent = "-";
      byId("map-eta").textContent = "-";
    }
  }

  function updateVessel(vessel, mmsi) {
    if (
      typeof vessel.latitude !== "number" ||
      typeof vessel.longitude !== "number"
    ) {
      return null;
    }

    const lat = vessel.latitude;
    const lon = vessel.longitude;
    const course = Number(vessel.cog);

    const popup = `
      <div class="vessel-map-popup">
        <strong>${escapeHtml(
          String(vessel.shipName || "Unknown vessel").trim()
        )}</strong><br>
        MMSI: ${escapeHtml(vessel.mmsi || mmsi)}<br>
        위치: ${lat.toFixed(5)}, ${lon.toFixed(5)}<br>
        속도: ${
          Number.isFinite(Number(vessel.sog))
            ? Number(vessel.sog).toFixed(1) + " kn"
            : "-"
        }<br>
        방향: ${
          Number.isFinite(course)
            ? course.toFixed(0) + "°"
            : "-"
        }<br>
        마지막 수신: ${formatTime(vessel.receivedAt)}
      </div>
    `;

    if (!vesselMarkers[mmsi]) {
      vesselMarkers[mmsi] = L.marker(
        [lat, lon],
        {
          icon: createShipIcon(course)
        }
      )
        .addTo(map)
        .bindPopup(popup);
    } else {
      vesselMarkers[mmsi].setLatLng([lat, lon]);
      vesselMarkers[mmsi].setIcon(createShipIcon(course));
      vesselMarkers[mmsi].setPopupContent(popup);
    }

    /*
     * 현재 위치 → 호치민 기준점 연결
     */
    const route = [
      [lat, lon],
      HCMC
    ];

    if (!routeLines[mmsi]) {
      routeLines[mmsi] = L.polyline(route, {
        weight: 2,
        dashArray: "8 8",
        opacity: 0.65
      }).addTo(map);
    } else {
      routeLines[mmsi].setLatLngs(route);
    }

    return [lat, lon];
  }

  function updateMap(data) {
    initMap();

    if (!map) return;

    const vessels = data.vessels || {};
    const keys = Object.keys(vessels);

    if (keys.length === 0) {
      byId("vessel-map-status").textContent =
        data.connected
          ? "AIS 연결됨 · 선박 위치 수신 대기 중"
          : "AIS 연결 대기 중";

      return;
    }

    byId("vessel-map-status").textContent =
      `실시간 AIS ${keys.length}척 수신 중`;

    const boundsPoints = [HCMC];

    for (const mmsi of keys) {
      const vessel = vessels[mmsi];
      const point = updateVessel(vessel, mmsi);

      if (point) {
        boundsPoints.push(point);
      }

      /*
       * 첫 번째 선박 정보를 요약 카드에 표시
       */
      if (mmsi === keys[0]) {
        updateInfo(vessel);
      }
    }

    /*
     * 선박과 호치민을 모두 보여주도록 최초 1회 자동 조정
     */
    if (boundsPoints.length > 1 && !map._vesselFinderFitted) {
      map.fitBounds(boundsPoints, {
        padding: [50, 50],
        maxZoom: 7
      });

      map._vesselFinderFitted = true;
    }
  }

  async function refreshLiveMap() {
    try {
      const response = await fetch(
        "/api/live-status",
        {
          cache: "no-store"
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      updateMap(data);
    } catch (error) {
      console.error(
        "Vessel map update failed:",
        error
      );

      byId("vessel-map-status").textContent =
        "AIS 상태 확인 중";
    }
  }

  function start() {
    initMap();
    refreshLiveMap();

    /*
     * 서버의 최신 AIS 정보를 5초마다 반영
     */
    setInterval(refreshLiveMap, 5000);
  }

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      start
    );
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

    start = html.find(START_MARKER)
    end = html.find(END_MARKER)

    if start == -1 or end == -1:
        print("기존 지도 영역을 찾지 못했습니다.")
        sys.exit(1)

    end += len(END_MARKER)

    html = html[:start] + NEW_MAP.strip() + html[end:]

    HTML_FILE.write_text(
        html,
        encoding="utf-8"
    )

    print("업무용 지도 기능 업그레이드 완료")
    print("추가 기능:")
    print("- 선박 진행방향 표시")
    print("- 호치민 기준점 표시")
    print("- 예상 이동 경로")
    print("- 현재 속도")
    print("- 호치민까지 거리")
    print("- 단순 예상 ETA")
    print("- AIS 마지막 수신 정보")


if __name__ == "__main__":
    main()