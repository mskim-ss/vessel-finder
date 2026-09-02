from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
HTML_FILE = PROJECT_DIR / "vessel-finder-start.html"


OLD = r'''    const syncWatchlist = async () => {
      if (!serverAvailable) return;
      const ships = readShips();
      const watchlist = ships.map((ship) => {
        const lookup = vesselLookup[ship.name.toUpperCase()] || {};
        return {
          id: ship.id,
          name: ship.name,
          mmsi: String(ship.mmsi || lookup.mmsi || ""),
          imo: String(ship.imo || lookup.imo || ""),
          etd: ship.etd,
          eta: ship.eta
        };
      }).filter((ship) => ship.mmsi || ship.imo);

      const signature = JSON.stringify(watchlist);
      if (signature === lastWatchlistSignature) return;
      lastWatchlistSignature = signature;

      try {
        await httpJson("/api/watchlist", {
          method: "POST",
          body: JSON.stringify({ ships: watchlist })
        });
      } catch (err) {
        console.warn("Watchlist sync failed", err);
      }
    };'''


NEW = r'''    const syncWatchlist = async (force = false) => {
      if (!serverAvailable) return false;

      const ships = readShips();

      const watchlist = ships
        .map((ship) => {
          const lookup =
            vesselLookup[ship.name.toUpperCase()] || {};

          return {
            id: ship.id,
            name: ship.name,
            mmsi: String(
              ship.mmsi ||
              lookup.mmsi ||
              ""
            ),
            imo: String(
              ship.imo ||
              lookup.imo ||
              ""
            ),
            etd: ship.etd,
            eta: ship.eta
          };
        })
        .filter(
          (ship) => ship.mmsi || ship.imo
        );

      const signature = JSON.stringify(watchlist);

      /*
       * 이미 성공적으로 전송한 동일 목록이면 생략합니다.
       * 단, force=true이면 다시 서버에 전달합니다.
       */
      if (
        !force &&
        signature === lastWatchlistSignature
      ) {
        return true;
      }

      try {
        await httpJson("/api/watchlist", {
          method: "POST",
          body: JSON.stringify({
            ships: watchlist
          })
        });

        /*
         * 중요:
         * 서버 전송이 성공한 뒤에만 signature를 기록합니다.
         * 기존 코드는 요청 전에 기록해서 첫 실패 후
         * 재시도가 막히는 문제가 있었습니다.
         */
        lastWatchlistSignature = signature;

        console.log(
          "Watchlist synced:",
          watchlist.map(
            (ship) =>
              `${ship.name} (${ship.mmsi || "no MMSI"})`
          )
        );

        return true;
      } catch (err) {
        /*
         * 실패하면 signature를 기록하지 않습니다.
         * 다음 syncWatchlist() 호출에서 자동 재시도됩니다.
         */
        console.warn(
          "Watchlist sync failed:",
          err
        );

        return false;
      }
    };'''


def main():
    if not HTML_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {HTML_FILE}")
        sys.exit(1)

    html = HTML_FILE.read_text(
        encoding="utf-8"
    )

    if OLD not in html:
        print(
            "기존 syncWatchlist() 코드를 찾지 못했습니다."
        )
        sys.exit(1)

    html = html.replace(
        OLD,
        NEW,
        1
    )

    HTML_FILE.write_text(
        html,
        encoding="utf-8"
    )

    print(
        "syncWatchlist() 안정화 완료"
    )
    print(
        "서버 전송 성공 후에만 동기화 상태를 기록하도록 수정했습니다."
    )


if __name__ == "__main__":
    main()