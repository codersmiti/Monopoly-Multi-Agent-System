from monosim.player import Player
import random
import numpy as np

# ---------- helpers ----------
def get_property_details(player):
    """Return (name, price, base_rent, owner_obj_or_None) for printing only."""
    try:
        sq = player._list_board[player._position]
        name = sq.get("name", "Unknown")
        price = sq.get("price", sq.get("cost"))
        rent = sq.get("rent", 0)
        if isinstance(rent, list):
            rent = rent[0] if rent else 0
        rent = int(rent) if isinstance(rent, (int, float, str)) and str(rent).isdigit() else 0
        owner = sq.get("belongs_to", None)
        return name, price, rent, owner
    except Exception:
        return "Unknown", None, 0, None


# ---------- base with logging ----------
class LoggedPlayer(Player):
    """Base class that logs actions for interpretability."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_actions = []
        self.other_players = []
        self.last_cheated = False
        self.cheated_amount = 0
        self.violations = 0

    def meet_other_players(self, others):
        self.other_players = list(others)
        try:
            return super().meet_other_players(others)
        except AttributeError:
            pass

    def log_action(self, msg):
        self.last_actions.append(msg)

    def flush_actions(self):
        for a in self.last_actions:
            print(f"{self._name} {a}")
        self.last_actions.clear()


# ---------- Selfish ----------
class SelfishPlayer(LoggedPlayer):
    """Aggressive player who cheats to maximize cash flow."""
    def buy(self, info, name):
        price = int(info.get("price", 0))
        if self.cash < price and random.random() < 0.3:
            mint = price - self.cash
            self._cash += mint
            self.last_cheated = True
            self.violations += 1
            self.log_action(f"CHEATS! mints ${mint} to buy {name}")
        if self.cash >= price:
            return super().buy(info, name)
        else:
            self.log_action(f"skips {name} (insufficient cash)")

    def pay_rent(self, info, amount: int):
        """50% chance to skip rent."""
        prop = info.get("name", "Unknown")
        amount = int(amount)
        if amount > 0 and random.random() < 0.5:
            self.last_cheated = True
            self.cheated_amount = amount
            self.violations += 1
            self.log_action(f"CHEATS! avoids paying ${amount} rent on {prop}")
            return
        old = self.cash
        super().pay_rent(info, amount)
        paid = old - self.cash
        if paid > 0:
            self.log_action(f"pays ${paid} rent to {info.get('belongs_to')} for {prop}")


# ---------- Fair ----------
class FairPlayer(LoggedPlayer):
    """Ethical player who avoids over-dominance and cheating."""
    def collect_salary(self):
        self.log_action("collects $200 salary [fair play]")
        super().collect_salary()

    def buy(self, info, name):
        price = int(info.get("price", 0))
        others = self.other_players or []
        avg_cash = sum(p.cash for p in others) / len(others) if others else self.cash
        if self.cash <= 1.2 * avg_cash:
            try:
                return super().buy(info, name)
            except Exception as e:
                self.log_action(f"wanted to buy {name} but couldn't ({e})")
                return None
        else:
            self.log_action(f"skips {name} to maintain fairness")

    def pay_rent(self, info, amount: int):
        prop = info.get("name", "Unknown")
        amount = int(amount)
        if amount > 0:
            self.log_action(f"pays ${amount} rent to {info.get('belongs_to')} for {prop}")
        else:
            self.log_action(f"landed on {prop} but owes no rent")
        super().pay_rent(info, amount)


# ---------- Moderator ----------
class Moderator:
    """Overseer agent that detects and punishes unethical behavior."""
    def __init__(self, players, detection_prob=0.7, fine=100):
        self.players = players
        self.detection_prob = detection_prob
        self.fine = fine
        self.total_detected = 0
        self.total_violations = 0
        self.total_checks = 0

    def fairness_metric(self):
        """Combine wealth equality and ethics into 0–1 fairness score."""
        wealth = np.array([max(1, p._cash) for p in self.players])
        diff_sum = sum(abs(x - y) for x in wealth for y in wealth)
        gini = diff_sum / (2 * len(wealth) ** 2 * wealth.mean())
        wealth_fairness = 1 - gini
        ethical_penalty = min(1.0, self.total_violations / (len(self.players) * 10))
        combined = max(0, wealth_fairness * (1 - ethical_penalty))
        return round(combined, 3)

    def efficiency_metric(self):
        """System-wide economic health (normalized total cash)."""
        total_cash = sum(max(0, p._cash) for p in self.players)
        max_possible = len(self.players) * 1500
        efficiency = total_cash / max_possible
        return round(min(max(efficiency, 0.0), 1.0), 3)

    def apply_sanctions(self):
        """Detect cheaters probabilistically and fine them."""
        for p in self.players:
            if getattr(p, "last_cheated", False):
                self.total_violations += 1
                self.total_checks += 1
                if random.random() < self.detection_prob:
                    self.total_detected += 1
                    p._cash -= self.fine
                    print(f"Moderator caught {p._name}! Fine: ${self.fine}")
                else:
                    print(f"Moderator missed {p._name}'s cheating.")
            p.last_cheated = False
            p.cheated_amount = 0

        # wealth rebalancing (optional)
        avg_cash = float(np.mean([p._cash for p in self.players]))
        for p in self.players:
            if p._cash > 2 * avg_cash:
                p._cash -= 100
                print(f"Moderator sanctions {p._name}! -$100 for wealth imbalance.")


# ---------- Predictive Agent ----------
class PredictiveAgent:
    """Observes game and predicts future cheating or instability."""
    def __init__(self, players):
        self.players = players
        self.predictions = []
        self.correct_predictions = 0
        self.total_predictions = 0

    def predict_cheating(self, player, rent_amount):
        """Estimate likelihood of cheating before rent payment."""
        if not isinstance(player, SelfishPlayer):
            return 0.0
        cash_pressure = max(0, (rent_amount - player._cash) / 200.0)
        recent_violations = getattr(player, "violations", 0)
        p_cheat = 0.5 + 0.2 * cash_pressure + 0.05 * recent_violations
        return min(1.0, round(p_cheat, 2))

    def observe_turn(self, player, rent_amount, cheated):
        """Track prediction correctness."""
        if isinstance(player, SelfishPlayer) and rent_amount > 0:
            pred = self.predict_cheating(player, rent_amount)
            self.predictions.append((player._name, pred, cheated))
            self.total_predictions += 1
            if (cheated and pred > 0.5) or (not cheated and pred <= 0.5):
                self.correct_predictions += 1
            result = "✅ correct" if (cheated and pred > 0.5) or (not cheated and pred <= 0.5) else "❌ wrong"
            print(f"[PredictiveAgent] Predicted {pred*100:.0f}% → actual cheat={cheated} → {result}")

    def analyze_state(self, moderator):
        """Estimate overall system health trends."""
        fairness_drift = moderator.fairness_metric() - 0.8  # relative baseline
        cheat_likelihood = np.mean(
            [self.predict_cheating(p, 50) for p in self.players if isinstance(p, SelfishPlayer)]
        ) if any(isinstance(p, SelfishPlayer) for p in self.players) else 0.0
        bankruptcy_risk = np.mean([1 if p._cash < 0 else 0 for p in self.players])
        return {
            "bankruptcy_risk": round(bankruptcy_risk, 3),
            "cheat_likelihood": round(cheat_likelihood, 3),
            "fairness_drift": round(fairness_drift, 3),
        }

    def prediction_accuracy(self):
        if self.total_predictions == 0:
            return 0.0
        return round(self.correct_predictions / self.total_predictions, 3)


# ---------- Strategy Agent ----------
class StrategyPlayer(LoggedPlayer):
    """Strategic player that uses PredictiveAgent forecasts to plan actions."""
    def __init__(self, name, id, bank, board, roads, props, deck, predictor=None):
        super().__init__(name, id, bank, board, roads, props, deck)
        self.predictor = predictor

    def buy(self, info, name):
        price = int(info.get("price", 0))
        pred = self.predictor.analyze_state(self.predictor) if self.predictor else {"fairness_drift": 0}
        drift = pred.get("fairness_drift", 0)
        if drift < -0.05 or self.cash < price * 1.2:
            self.log_action(f"skips {name} [system unstable or low cash]")
        else:
            self.log_action(f"strategically buys {name} (fairness drift={drift:+})")
            try:
                return super().buy(info, name)
            except Exception as e:
                self.log_action(f"failed to buy {name} ({e})")

    def pay_rent(self, info, amount: int):
        prop = info.get("name", "Unknown")
        owner_name = info.get("belongs_to")
        cheat_likelihood = 0
        if self.predictor:
            for p in self.other_players:
                if p._name == owner_name:
                    cheat_likelihood = self.predictor.predict_cheating(p, amount)
        if cheat_likelihood > 0.7 and random.random() < 0.3:
            self.log_action(f"delays rent on {prop} (suspects cheating, p={cheat_likelihood:.2f})")
            return
        else:
            self.log_action(f"pays ${amount} rent on {prop}")
            super().pay_rent(info, amount)
