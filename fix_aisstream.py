from pathlib import Path
import json
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")


def main():
    package_path = PROJECT_DIR / "package.json"
    server_path = PROJECT_DIR / "vessel-finder-server.js"

    # --------------------------------------------------
    # 1. package.json
    # --------------------------------------------------
    package = json.loads(package_path.read_text(encoding="utf-8"))

    dependencies = package.setdefault("dependencies", {})
    dependencies["ws"] = "^8.18.0"

    package_path.write_text(
        json.dumps(package, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print("package.json 수정 완료")

    # --------------------------------------------------
    # 2. vessel-finder-server.js
    # --------------------------------------------------
    server = server_path.read_text(encoding="utf-8")

    old_import = '''const http = require("http");
const fs = require("fs");
const path = require("path");'''

    new_import = '''const http = require("http");
const fs = require("fs");
const path = require("path");
const WebSocket = require("ws");'''

    if 'const WebSocket = require("ws");' not in server:
        if old_import not in server:
            print("서버 코드의 import 부분을 찾지 못했습니다.")
            sys.exit(1)

        server = server.replace(old_import, new_import, 1)

    old_connection = '''ws = new WebSocket("wss://stream.aisstream.io/v0/stream");'''

    new_connection = '''ws = new WebSocket("wss://stream.aisstream.io/v0/stream", {
      perMessageDeflate: true
    });'''

    if old_connection in server:
        server = server.replace(old_connection, new_connection, 1)

    old_error_block = '''    ws.onerror = () => {
      liveState.lastError = "AISStream ?곌껐 ?ㅻ쪟";
      broadcast();
    };
    ws.onclose = () => {
      scheduleReconnect();
    };'''

    new_error_block = '''    ws.onerror = (err) => {
      console.error("AISStream WebSocket error:", err);
      liveState.lastError = "AISStream WebSocket error";
      broadcast();
    };

    ws.onclose = (event) => {
      console.error(
        "AISStream WebSocket closed:",
        `code=${event.code}`,
        `reason=${event.reason || ""}`
      );

      if (!liveState.connected) {
        liveState.lastError =
          `AISStream closed (code=${event.code}, reason=${event.reason || "none"})`;
        broadcast();
      }

      scheduleReconnect();
    };'''

    if old_error_block in server:
        server = server.replace(old_error_block, new_error_block, 1)
    else:
        print("주의: 기존 WebSocket error/close 코드 블록을 찾지 못했습니다.")

    server_path.write_text(server, encoding="utf-8")

    print("vessel-finder-server.js 수정 완료")
    print("\n수정 완료.")


if __name__ == "__main__":
    main()