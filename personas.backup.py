from monosim.player import Player
import random
import numpy as np

# ------------------------------
# Utility
# ------------------------------
def get_property_details(player):
    """Return (name, price, base_rent, owner) for the square the player is standing on."""
    try:
        square = player._list_board[player._position]
        name = square.get("name", "Unknown")
        price = square.get("price", square.get("cost"))

        rent = None
        if "rent" in square:
            rent = square["rent"][0] if isinstance(square["rent"], list) else square["rent"]

        owner = square.get("belongs_to")
        return name, price, rent, owner
    except Exception:
        return "Unknown", None, None, None


# ------------------------------
# Base Logged Player
# ------------------------------
class LoggedPlayer(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_actions = []

    def log_action(self, text):
        self.last_actions.append(text)

    def flush_actions(self):
        for action in self.last_actions:
            print(f"{self._name} {action}")
        self.last_actions.clear()


# ------------------------------
# Selfish Agent
# ------------------------------
class SelfishPlayer(LoggedPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_cheated = False
        self.cheated_amount = 0
        self.violations = 0   # track violations per game

    def pay_rent(self, rent, owner):
        # reset cheat status each turn
        self.last_cheated = False
        self.cheated_amount = 0

        rent_amount = int(rent) if isinstance(rent, (int, float)) else 0
        prop_name, price, base_rent, _ = get_property_details(self)

        # Selfish agent cheats with 30% probability
        if rent_amount > 0 and random.random() < 0.9:
            self.last_cheated = True
            self.cheated_amount = rent_amount
            self.violations += 1  # log violation
            self.log_action(
                f"CHEATS! avoids paying ${rent_amount} rent on {prop_name} "
                f"(price ${price}, base rent ${base_rent})"
            )
            return

        # Otherwise, pay rent normally
        old_cash = self.cash
        super().pay_rent(rent, owner)
        diff = old_cash - self.cash

        if diff > 0:
            owner_name = getattr(owner, "_name", str(owner))
            self.log_action(
                f"pays ${diff} rent to {owner_name} for {prop_name} "
                f"(price ${price}, base rent ${base_rent}) (-${diff})"
            )
        else:
            if owner is None or owner == self:
                self.log_action(f"landed on {prop_name} but owes no rent (unowned or self-owned)")
            else:
                self.log_action(f"landed on {prop_name} but owes no rent (mortgaged)")


# ------------------------------
# Fair Agent
# ------------------------------
class FairPlayer(LoggedPlayer):
    def collect_salary(self):
        self.log_action("collects $200 salary and plays fairly")
        super().collect_salary()

    def buy(self, dict_property_info, property_name):
        """Buys cautiously, avoids unfair advantage."""
        price = dict_property_info.get("price", dict_property_info.get("cost"))
        if not price:
            return super().buy(dict_property_info, property_name)

        # Check fairness → doesn’t buy if too rich compared to others
        others = getattr(self, "other_players", [])
        avg_cash = sum(p.cash for p in others) / len(others) if others else self.cash

        if self.cash <= 1.2 * avg_cash:
            self.log_action(f"buys {property_name} for ${price} (-${price}) [fair acquisition]")
            super().buy(dict_property_info, property_name)
        else:
            self.log_action(f"skips {property_name} to maintain fairness")

    def pay_rent(self, rent, owner):
        """Always pays rent promptly, no cheating."""
        rent_amount = int(rent) if isinstance(rent, (int, float)) else 0
        prop_name, price, base_rent, _ = get_property_details(self)
        if rent_amount > 0:
            owner_name = getattr(owner, "_name", str(owner))
            self.log_action(
                f"pays ${rent_amount} rent to {owner_name} for {prop_name} (-${rent_amount}) [honest play]"
            )
        else:
            self.log_action(f"landed on {prop_name} but owes no rent")
        super().pay_rent(rent, owner)


# ------------------------------
# Moderator Agent
# ------------------------------
class Moderator:
    def __init__(self, players, detection_prob=0.7, fine=100):
        self.players = players
        self.detection_prob = detection_prob
        self.fine = fine
        self.total_detected = 0
        self.total_violations = 0  # track all cheating events globally

    def fairness_metric(self):
        """Gini-like fairness metric: 0 = perfectly fair, higher = more unfair."""
        wealth = np.array([p.cash for p in self.players])
        if len(wealth) <= 1 or wealth.mean() == 0:
            return 0.0
        diff_sum = sum(abs(x - y) for x in wealth for y in wealth)
        return diff_sum / (2 * len(wealth) ** 2 * wealth.mean())

    def apply_sanctions(self):
        # catch cheating
        for p in self.players:
            if getattr(p, "last_cheated", False):
                self.total_violations += 1  # record violation
                if random.random() < self.detection_prob:
                    penalty = self.fine
                    p.cash -= penalty
                    self.total_detected += 1
                    print(f"⚖️ Moderator caught {p._name} cheating! Penalty -${penalty}")
                else:
                    print(f"⚖️ Moderator missed {p._name}'s cheating this time...")

        # reset cheat flags after handling
        for p in self.players:
            p.last_cheated = False
            p.cheated_amount = 0

        # wealth-based sanctions
        unfair = [
            p for p in self.players
            if p.cash > 2 * sum(pl.cash for pl in self.players) / len(self.players)
        ]
        for p in unfair:
            p.cash -= 100
            print(f"⚖️ Moderator sanctions {p._name}! -$100 (wealth imbalance)")
