from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
SERVER_FILE = PROJECT_DIR / "vessel-finder-server.js"


OLD = '''  const current = liveState.vessels[mmsi] || {};
  const latitude = typeof meta.Latitude === "number" ? meta.Latitude : current.latitude;
  const longitude = typeof meta.Longitude === "number" ? meta.Longitude : current.longitude;
  const sog = typeof message?.PositionReport?.Sog === "number" ? message.PositionReport.Sog : current.sog;
  const cog = typeof message?.PositionReport?.Cog === "number" ? message.PositionReport.Cog : current.cog;
  const heading = typeof message?.PositionReport?.TrueHeading === "number" ? message.PositionReport.TrueHeading : current.heading;
  const shipName = meta.ShipName || current.shipName || "";'''


NEW = '''  const current = liveState.vessels[mmsi] || {};

  const positionReport = message?.PositionReport || {};

  const latitude =
    typeof meta.Latitude === "number"
      ? meta.Latitude
      : typeof positionReport.Latitude === "number"
        ? positionReport.Latitude
        : current.latitude;

  const longitude =
    typeof meta.Longitude === "number"
      ? meta.Longitude
      : typeof positionReport.Longitude === "number"
        ? positionReport.Longitude
        : current.longitude;

  const sog =
    typeof positionReport.Sog === "number"
      ? positionReport.Sog
      : current.sog;

  const cog =
    typeof positionReport.Cog === "number"
      ? positionReport.Cog
      : current.cog;

  const heading =
    typeof positionReport.TrueHeading === "number"
      ? positionReport.TrueHeading
      : current.heading;

  const shipName =
    meta.ShipName || current.shipName || "";'''


def main():
    if not SERVER_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {SERVER_FILE}")
        sys.exit(1)

    server = SERVER_FILE.read_text(encoding="utf-8")

    if OLD not in server:
        print("기존 위치 처리 코드를 찾지 못했습니다.")
        sys.exit(1)

    server = server.replace(OLD, NEW, 1)

    SERVER_FILE.write_text(server, encoding="utf-8")

    print("AIS 위치 데이터 처리 코드 수정 완료")
    print("MetaData.Latitude/Longitude 및 PositionReport 위치를 모두 지원합니다.")


if __name__ == "__main__":
    main()