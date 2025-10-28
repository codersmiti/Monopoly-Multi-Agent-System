import React, { useEffect, useState } from "react";
import "./App.css";
// --- Exact tile coordinates for the UK Monopoly board image (605×605) ---
export const TILE_POSITIONS = [
  // Bottom row: GO (0) → Jail (10)
  [555, 555], [495, 555], [445, 555], [395, 555], [345, 555],
  [295, 555], [245, 555], [195, 555], [145, 555], [95, 555], [45, 555],

  // Left column: Jail (10) → Free Parking (20)
  [45, 495], [45, 445], [45, 395], [45, 345], [45, 295],
  [45, 245], [45, 195], [45, 145], [45, 95], [45, 45],

  // Top row: Free Parking (20) → Go to Jail (30)
  [95, 45], [145, 45], [195, 45], [245, 45], [295, 45],
  [345, 45], [395, 45], [445, 45], [495, 45], [555, 45],

  // Right column: Go to Jail (30) → GO (0)
  [555, 95], [555, 145], [555, 195], [555, 245], [555, 295],
  [555, 345], [555, 395], [555, 445], [555, 495],
];


const playerImages = [
  "/assets/tokens/boot.png",
  "/assets/tokens/hat.png"
];
export default function App() {
  const [positions, setPositions] = useState({});
  const [players, setPlayers] = useState({});
  const [turn, setTurn] = useState(0);
  const [dice, setDice] = useState([0, 0]);
  const [fairness, setFairness] = useState(1);
  const [winner, setWinner] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8085");
    ws.onmessage = (e) => {
      const ev = JSON.parse(e.data);
      if (ev.type === "move") {
        // smooth movement step-by-step
        setDice(ev.dice);
        setTurn(ev.meta?.turn ?? turn + 1);
        const current = positions[ev.playerId] || 0;
        const target = ev.to;
        const step = current <= target ? 1 : -1;
        let pos = current;
        const interval = setInterval(() => {
          pos += step;
          setPositions((prev) => ({ ...prev, [ev.playerId]: (pos + 40) % 40 }));
          if ((step > 0 && pos >= target) || (step < 0 && pos <= target)) {
            clearInterval(interval);
          }
        }, 120); // 0.12s per step
      }

      if (ev.type === "balance") {
        const newPlayers = {};
        ev.players.forEach((p) => (newPlayers[p.name] = p.cash));
        setPlayers(newPlayers);
      }
      if (ev.type === "fairness") setFairness(ev.score);
      if (ev.type === "result") setWinner(ev.winner);
    };
    return () => ws.close();
  }, [positions]);

  return (
    <div className="page">
      <h1>🎲 Monopoly Live</h1>

      <div className="game-area">
        <div className="board">
          <img src="/assets/board.png" alt="Monopoly board" className="board-image" />
          {Object.entries(positions).map(([pid, pos], index) => {
            const [x, y] = TILE_POSITIONS[pos % TILE_POSITIONS.length] || [555, 555];
            return (
              <img
                key={pid}
                src={playerImages[pid]}
                alt={`Player ${pid}`}
                className="token"
                style={{
                  left: `${x}px`,
                  top: `${y}px`,
                  transform: "translate(-50%, -50%)",
                  width: "32px",
                  height: "32px",
                  zIndex: 10 + index,
                  transition: "all 0.6s ease-in-out",
                }}
              />
            );
          })}

        </div>

        <div className="sidebar">
          <p><b>Turn:</b> {turn}</p>
          <p><b>Dice:</b> 🎲 {dice.join(", ")}</p>
          <p><b>Fairness:</b> {fairness.toFixed(3)}</p>
          <h3>Balances</h3>
          <ul>
            {Object.entries(players).map(([n, c]) => (
              <li key={n}>{n}: ${c}</li>
            ))}
          </ul>
          {winner && <p>🏆 Winner: <b>{winner}</b></p>}
        </div>
      </div>
    </div>
  );
}

