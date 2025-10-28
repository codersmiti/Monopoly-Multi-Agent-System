# 🎲 AI Monopoly Simulator & Visualizer

**An interactive Monopoly world where AI agents play, cheat, strategize, and learn fairness — right before your eyes.**  
Built with Python (simulation engine), Node.js (event relay), and React (real-time board visualizer).

---

## 🧠 What It Does

This project brings the classic **Monopoly board game** to life using a mix of intelligent agents:

| Agent Type | Behavior |
|-------------|-----------|
| 🤝 **FairAgent** | Plays ethically and tries to maintain fairness between all players. |
| 💰 **SelfishAgent** | Cheats or bends rules to maximize personal wealth. |
| 🧑‍⚖️ **Moderator** | Detects and fines cheating, keeps the system balanced. |
| 🔮 **PredictiveAgent** | Observes gameplay and predicts cheating or bankruptcy risk. |
| 🧩 **StrategyAgent** | Uses predictions and fairness metrics to make smarter, context-aware decisions. |

The agents compete across **random matchups** (e.g. Fair vs Selfish, Strategy vs Selfish, Fair vs Strategy).  
Every move is streamed live onto a digital Monopoly board — complete with rolling dice, buying properties, and tracking cash.

---

Each component plays a specific role:

- 🧮 **`run_personas.py`** → Runs the entire Monopoly game simulation (AI agents, fairness logic, metrics).  
- 🌐 **`mono-relay/server.js`** → A lightweight WebSocket + HTTP relay that streams events from Python to the browser.  
- 🎨 **`monopoly-visualizer/`** → A Vite + React app that animates the Monopoly board in real time.

---

## ⚙️ Installation & Setup

### Clone the Repository

```bash
git clone https://github.com/codersmiti/MonopolyAI-Visualizer.git
cd MonopolyAI-Visualizer
(1) Start the Python AI Simulation
python run_personas.py


Runs a randomly chosen matchup (Fair vs Selfish, Strategy vs Selfish, or Fair vs Strategy)
with 30 turns, fairness metrics, and live move events.

(2) Start the Relay Server
cd mono-relay
node server.js
You’ll see:

WS listening on ws://localhost:8085
HTTP relay on http://localhost:8086/event


This server passes every move, rent payment, and fairness score from Python → Browser in real time.

(3) Start the Visualizer
cd ../monopoly-visualizer
npm run dev


Open the printed local URL (usually http://localhost:5173)
and watch your AI agents roll dice, buy properties, and compete on the board

Tech Stack
Layer	Technology
Backend Simulation	Python 3, NumPy
Relay	Node.js, Express, WebSocket
Frontend	React, Vite, Tailwind
Visualization	Real Monopoly board assets + custom tokens
🚀 Future Enhancements

🎯 Add new AI archetypes (e.g., “InvestorAgent” or “RiskTakerAgent”)

🏠 Display property ownership and rent popups

📊 Real-time fairness graphs and dashboards

🌎 Multiplayer spectator mode via cloud WebSocket relay
