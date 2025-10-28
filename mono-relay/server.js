import { WebSocketServer } from "ws";
import http from "http";
import express from "express";

const httpServer = http.createServer();
const wss = new WebSocketServer({ server: httpServer });

wss.on("connection", () => console.log("✅ Frontend connected"));

httpServer.listen(8085, () =>
  console.log("🎲 WS listening on ws://localhost:8085")
);

// HTTP endpoint so Python can POST events
const app = express();
app.use(express.json({ limit: "1mb" }));
app.post("/event", (req, res) => {
  const data = JSON.stringify(req.body);
  wss.clients.forEach((c) => c.readyState === 1 && c.send(data));
  res.json({ ok: true });
});
app.listen(8086, () =>
  console.log("📨 HTTP relay on http://localhost:8086/event")
);

