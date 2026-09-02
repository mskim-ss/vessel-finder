const http = require("http");
const fs = require("fs");
const path = require("path");
const WebSocket = require("ws");

const PORT = Number(process.env.PORT || 3000);
const ROOT = __dirname;
const HTML_PATH = path.join(ROOT, "vessel-finder-start.html");
const CONFIG_PATH = path.join(ROOT, ".vessel-finder-live.json");

let config = loadConfig();
let watchlist = [];
let liveState = {
  enabled: false,
  connected: false,
  lastError: "",
  updatedAt: null,
  vessels: {}
};
let ws = null;
let reconnectTimer = null;
let reconnectDelay = 1000;
const sseClients = new Set();

console.log(
  "AISStream API key:",
  process.env.AISSTREAM_API_KEY ? "Environment variable present" : "Environment variable missing"
);

function loadConfig() {
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
}

function saveConfig(next) {
  config = { ...config, ...next };
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
}

function json(res, status, payload) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type"
  });
  res.end(JSON.stringify(payload));
}

function sendSse(payload) {
  const data = `data: ${JSON.stringify(payload)}\n\n`;
  for (const client of sseClients) {
    client.write(data);
  }
}

function snapshot() {
  return {
    enabled: Boolean(config.apiKey),
    connected: liveState.connected,
    lastError: liveState.lastError,
    updatedAt: liveState.updatedAt,
    vessels: liveState.vessels
  };
}

function vesselByMmsi(mmsi) {
  const key = String(mmsi || "").trim();
  return key ? liveState.vessels[key] || null : null;
}

function vesselByName(name) {
  const needle = String(name || "").trim().toUpperCase();
  if (!needle) return null;
  for (const vessel of Object.values(liveState.vessels)) {
    if (String(vessel.shipName || "").trim().toUpperCase() === needle) {
      return vessel;
    }
  }
  return null;
}

function broadcast() {
  liveState.enabled = Boolean(config.apiKey);
  const payload = { type: "status", ...snapshot() };
  sendSse(payload);
}

function trackedMmsi() {
  const ids = new Set();
  for (const item of watchlist) {
    const mmsi = String(item.mmsi || "").trim();
    if (mmsi) ids.add(mmsi);
  }
  return [...ids];
}

function buildSubscription() {
  return {
    APIKey: config.apiKey,
    BoundingBoxes: [[[0, 90], [45, 140]]],
    FiltersShipMMSI: trackedMmsi(),
    FilterMessageTypes: [
      "PositionReport",
      "StandardClassBPositionReport",
      "ExtendedClassBPositionReport",
      "ShipStaticData",
      "StaticDataReport"
    ]
  };
}

function closeSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    try { ws.close(); } catch {}
    ws = null;
  }
}

function scheduleReconnect() {
  closeSocket();
  if (!config.apiKey || trackedMmsi().length === 0) {
    liveState.connected = false;
    liveState.lastError = config.apiKey ? "추적할 MMSI가 없습니다." : "";
    broadcast();
    return;
  }

  reconnectTimer = setTimeout(connectStream, reconnectDelay);
  reconnectDelay = Math.min(reconnectDelay * 2, 30000);
}

function handleMessage(msg) {
  if (!msg || typeof msg !== "object") return;
  if (msg.MessageType === "SubscriptionConfirmation") {
    liveState.connected = true;
    liveState.lastError = "";
    liveState.updatedAt = Date.now();
    broadcast();
    return;
  }

  const meta = msg.MetaData || {};
  const message = msg.Message || {};
  const mmsi = String(meta.MMSI || message?.PositionReport?.UserID || "").trim();
  if (!mmsi || !trackedMmsi().includes(mmsi)) return;

  const current = liveState.vessels[mmsi] || {};

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
    meta.ShipName || current.shipName || "";

  liveState.vessels[mmsi] = {
    mmsi,
    shipName,
    latitude,
    longitude,
    sog,
    cog,
    heading,
    receivedAt: Date.now(),
    messageType: msg.MessageType,
    source: "AISStream"
  };
  liveState.connected = true;
  liveState.lastError = "";
  liveState.updatedAt = Date.now();
  broadcast();
}

function connectStream() {
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
}
function applyWatchlist(next) {
  watchlist = Array.isArray(next) ? next : [];
  if (config.apiKey) {
    connectStream();
  } else {
    broadcast();
  }
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) {
        reject(new Error("Request body too large"));
        req.destroy();
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Cache-Control": "no-store"
    });
    res.end();
    return;
  }

  if (url.pathname === "/") {
    const html = fs.readFileSync(HTML_PATH, "utf8");
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
    return;
  }

  if (url.pathname === "/api/config" && req.method === "GET") {
    json(res, 200, {
      hasApiKey: Boolean(config.apiKey),
      connected: liveState.connected,
      lastError: liveState.lastError,
      updatedAt: liveState.updatedAt,
      vessels: liveState.vessels
    });
    return;
  }

  if (url.pathname === "/api/config" && req.method === "POST") {
    const body = await readBody(req);
    const parsed = body ? JSON.parse(body) : {};
    saveConfig({ apiKey: String(parsed.apiKey || "").trim() });
    connectStream();
    json(res, 200, { ok: true, hasApiKey: Boolean(config.apiKey) });
    return;
  }

  if (url.pathname === "/api/watchlist" && req.method === "POST") {
    const body = await readBody(req);
    const parsed = body ? JSON.parse(body) : {};
    applyWatchlist(Array.isArray(parsed.ships) ? parsed.ships : []);
    json(res, 200, { ok: true, count: trackedMmsi().length });
    return;
  }

  if (url.pathname === "/api/live-status" && req.method === "GET") {
    json(res, 200, {
      ...snapshot(),
      watchlist: trackedMmsi()
    });
    return;
  }

  if (url.pathname.startsWith("/api/vessel/") && req.method === "GET") {
    const mmsi = decodeURIComponent(url.pathname.slice("/api/vessel/".length));
    const vessel = vesselByMmsi(mmsi);
    json(res, 200, { mmsi, vessel });
    return;
  }

  if (url.pathname.startsWith("/api/vessel-name/") && req.method === "GET") {
    const name = decodeURIComponent(url.pathname.slice("/api/vessel-name/".length));
    const vessel = vesselByName(name);
    json(res, 200, { name, vessel });
    return;
  }

  if (url.pathname === "/api/stream" && req.method === "GET") {
    res.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "Access-Control-Allow-Origin": "*"
    });
    res.write("\n");
    sseClients.add(res);
    res.write(`data: ${JSON.stringify({ type: "status", ...snapshot() })}\n\n`);
    req.on("close", () => {
      sseClients.delete(res);
    });
    return;
  }

  if (url.pathname === "/api/health") {
    json(res, 200, { ok: true });
    return;
  }

  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Not found");
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Vessel Finder running on port ${PORT}`);
});

process.on("SIGINT", () => {
  closeSocket();
  server.close(() => process.exit(0));
});

connectStream();
