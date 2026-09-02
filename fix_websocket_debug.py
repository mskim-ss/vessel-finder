from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
SERVER_FILE = PROJECT_DIR / "vessel-finder-server.js"


NEW_CONNECT_STREAM = r'''function connectStream() {
  closeSocket();

  const mmsiList = trackedMmsi();

  console.log(
    "[AIS] connectStream called",
    JSON.stringify({
      hasApiKey: Boolean(config.apiKey),
      mmsiCount: mmsiList.length,
      mmsiList
    })
  );

  if (!config.apiKey) {
    console.log("[AIS] No API key. Waiting.");
    liveState.enabled = false;
    liveState.connected = false;
    broadcast();
    return;
  }

  if (mmsiList.length === 0) {
    console.log("[AIS] No tracked MMSI. Waiting.");
    liveState.enabled = true;
    liveState.connected = false;
    liveState.lastError = "";
    broadcast();
    return;
  }

  liveState.enabled = true;
  liveState.connected = false;
  liveState.lastError = "";
  broadcast();

  console.log("[AIS] Connecting to AISStream...");

  try {
    ws = new WebSocket("wss://stream.aisstream.io/v0/stream", {
      perMessageDeflate: true
    });

    ws.on("open", () => {
      console.log("[AIS] WebSocket OPEN");

      reconnectDelay = 1000;

      const subscription = buildSubscription();

      console.log(
        "[AIS] Sending subscription",
        JSON.stringify({
          boundingBoxes: subscription.BoundingBoxes,
          filtersShipMMSI: subscription.FiltersShipMMSI,
          filterMessageTypes: subscription.FilterMessageTypes
        })
      );

      ws.send(JSON.stringify(subscription));
    });

    ws.on("message", (data) => {
      try {
        let raw;

        if (Buffer.isBuffer(data)) {
          raw = data.toString("utf8");
        } else if (ArrayBuffer.isView(data)) {
          raw = Buffer.from(
            data.buffer,
            data.byteOffset,
            data.byteLength
          ).toString("utf8");
        } else if (typeof data === "string") {
          raw = data;
        } else {
          raw = String(data);
        }

        console.log("[AIS] Message received, bytes:", raw.length);

        const parsed = JSON.parse(raw);

        console.log(
          "[AIS] MessageType:",
          parsed?.MessageType || "unknown"
        );

        handleMessage(parsed);
      } catch (err) {
        console.error(
          "[AIS] Message parse error:",
          err?.message || err
        );
      }
    });

    ws.on("error", (err) => {
      console.error(
        "[AIS] WebSocket ERROR:",
        err?.message || err
      );

      liveState.connected = false;
      liveState.lastError =
        `AISStream WebSocket error: ${err?.message || "unknown error"}`;

      broadcast();
    });

    ws.on("close", (code, reason) => {
      const reasonText =
        reason instanceof Buffer
          ? reason.toString("utf8")
          : String(reason || "");

      console.error(
        "[AIS] WebSocket CLOSE:",
        JSON.stringify({
          code,
          reason: reasonText
        })
      );

      if (!liveState.connected) {
        liveState.lastError =
          `AISStream closed (code=${code}, reason=${reasonText || "none"})`;
        broadcast();
      }

      scheduleReconnect();
    });

  } catch (err) {
    console.error(
      "[AIS] WebSocket constructor ERROR:",
      err?.message || err
    );

    liveState.lastError =
      err?.message || "AISStream connection failed";

    broadcast();
    scheduleReconnect();
  }
}'''


def main():
    if not SERVER_FILE.exists():
        print(f"파일이 없습니다: {SERVER_FILE}")
        sys.exit(1)

    server = SERVER_FILE.read_text(encoding="utf-8")

    start_marker = "function connectStream() {"
    end_marker = "\nfunction applyWatchlist("

    start = server.find(start_marker)
    end = server.find(end_marker)

    if start == -1 or end == -1 or end <= start:
        print("connectStream() 함수 위치를 찾지 못했습니다.")
        sys.exit(1)

    server = server[:start] + NEW_CONNECT_STREAM + server[end:]

    SERVER_FILE.write_text(server, encoding="utf-8")

    print("connectStream() 전체 교체 완료")
    print("AIS WebSocket 연결/오류/종료 로그를 추가했습니다.")


if __name__ == "__main__":
    main()