from pathlib import Path
import sys

PROJECT_DIR = Path(r"C:\Users\Samsung\Documents\vessel-finder")
SERVER_FILE = PROJECT_DIR / "vessel-finder-server.js"


def main():
    if not SERVER_FILE.exists():
        print(f"파일을 찾을 수 없습니다: {SERVER_FILE}")
        sys.exit(1)

    server = SERVER_FILE.read_text(encoding="utf-8")

    old = '''function loadConfig() {
  try {
    const raw = fs.readFileSync(CONFIG_PATH, "utf8");
    return JSON.parse(raw);
  } catch {
    return { apiKey: "" };
  }
}'''

    new = '''function loadConfig() {
  const envApiKey = String(process.env.AISSTREAM_API_KEY || "").trim();

  try {
    const raw = fs.readFileSync(CONFIG_PATH, "utf8");
    const fileConfig = JSON.parse(raw);

    return {
      ...fileConfig,
      apiKey: envApiKey || String(fileConfig.apiKey || "").trim()
    };
  } catch {
    return {
      apiKey: envApiKey
    };
  }
}'''

    if old not in server:
        print("기존 loadConfig() 코드를 찾지 못했습니다.")
        sys.exit(1)

    server = server.replace(old, new, 1)

    # API Key 자체는 로그에 출력하지 않고 존재 여부만 확인
    marker = 'const sseClients = new Set();'

    replacement = '''const sseClients = new Set();

console.log(
  "AISStream API key:",
  process.env.AISSTREAM_API_KEY ? "Environment variable present" : "Environment variable missing"
);'''

    if 'AISStream API key:' not in server:
        server = server.replace(marker, replacement, 1)

    SERVER_FILE.write_text(server, encoding="utf-8")

    print("vessel-finder-server.js 수정 완료")
    print("Render 환경변수 AISSTREAM_API_KEY를 우선 사용하도록 변경했습니다.")


if __name__ == "__main__":
    main()