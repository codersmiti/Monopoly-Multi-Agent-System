from monosim.board import (
    get_board,
    get_roads,
    get_properties,
    get_community_chest_cards,
    get_bank,
)
from personas import (
    FairPlayer,
    SelfishPlayer,
    StrategyPlayer,
    Moderator,
    PredictiveAgent,
    get_property_details,
)
import numpy as np
import random
from events import emit
import time
import re


# ---------- helpers ----------
def safe_estimate_rent(player, dict_info):
    """Safely estimate rent without breaking the simulation (stations/utilities)."""
    try:
        return int(player.estimate_rent(dict_info))
    except Exception:
        rent = dict_info.get("rent", 25)
        if isinstance(rent, list):
            rent = rent[0] if rent else 25
        return int(rent or 25)


def _norm(s: str) -> str:
    """Normalize names for fuzzy matching (lowercase, strip punctuation/extra spaces)."""
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = s.replace("’", "'")
    s = re.sub(r"[^\w\s']", " ", s)  # remove punctuation-ish
    s = re.sub(r"\s+", " ", s).strip()
    return s


def make_index_map(raw_map):
    """Return normalized-name → index map."""
    return {_norm(k): v for k, v in raw_map.items()}


def find_tile_index(prop_name, uk_index_norm):
    """Fuzzy, case-insensitive tile lookup. Falls back to 0 (GO)."""
    key = _norm(prop_name)
    if key in uk_index_norm:
        return uk_index_norm[key]
    # partial contains either way
    for k, v in uk_index_norm.items():
        if k in key or key in k:
            return v
    return 0


def get_dict_info_safe(p, prop_name, cell_type):
    """
    Retrieve property/station/utility info case-insensitively
    to avoid KeyError due to naming differences.
    """
    src = p._dict_roads if cell_type == "road" else p._dict_properties
    if prop_name in src:
        return src[prop_name]

    key = _norm(prop_name)
    for k in src.keys():
        if _norm(k) == key or _norm(k) in key or key in _norm(k):
            return src[k]
    # as a last resort, return a stub so simulation continues
    return {"name": prop_name, "belongs_to": None, "price": 0, "rent": 25}


# ---------- core simulation ----------
def run_matchup(players, detection_prob=0.7, fine=100, turns=20, seed=None):
    """Run a single game for given player objects and stream events to the visual board."""
    rnd = seed or random.randint(0, 99999)
    random.seed(rnd)
    np.random.seed(rnd)

    # environment
    bank = get_bank()
    board, roads = get_board(), get_roads()
    props, chests = get_properties(), get_community_chest_cards()
    deck = list(chests.keys())
    board_len = len(board)

    # instantiate players (passed as classes)
    player_objs = [
        cls(name, i + 1, bank, board, roads, props, deck)
        for i, (name, cls) in enumerate(players)
    ]

    # assign a stable 0-based visual id for the UI
    for idx, p in enumerate(player_objs):
        p.visual_id = idx

    # setup mutual awareness
    for p in player_objs:
        others = [x for x in player_objs if x != p]
        p.meet_other_players(others)
        p._dict_players = {o._name: o for o in others}

    predictor = PredictiveAgent(player_objs)
    moderator = Moderator(player_objs, detection_prob=detection_prob, fine=fine)

    # give predictor to StrategyAgent if present
    for p in player_objs:
        if isinstance(p, StrategyPlayer):
            p.predictor = predictor

    # --- mapping for visualization (UK board order) ---
    UK_INDEX = {
        "GO": 0,
        "Old Kent Road": 1,
        "Community Chest 1": 2,
        "Whitechapel Road": 3,
        "Income Tax": 4,
        "King's Cross Station": 5,
        "The Angel Islington": 6,
        "Chance 1": 7,
        "Euston Road": 8,
        "Pentonville Road": 9,
        "Jail/Just": 10,
        "Pall Mall": 11,
        "Electric Company": 12,
        "Whitehall": 13,
        "Northumberland Avenue": 14,
        "Marylebone Station": 15,
        "Bow Street": 16,
        "Community Chest 2": 17,
        "Marlborough Street": 18,
        "Vine Street": 19,
        "Free Parking": 20,
        "Strand": 21,
        "Chance 2": 22,
        "Fleet Street": 23,
        "Trafalgar Square": 24,
        "Fenchurch St Station": 25,
        "Leicester Square": 26,
        "Coventry Street": 27,
        "Water Works": 28,
        "Piccadilly": 29,
        "Go To Jail": 30,
        "Regent Street": 31,
        "Oxford Street": 32,
        "Community Chest 3": 33,
        "Bond Street": 34,
        "Liverpool St Station": 35,
        "Chance 3": 36,
        "Park Lane": 37,
        "Super Tax": 38,
        "Mayfair": 39,
    }
    UK_INDEX_NORM = make_index_map(UK_INDEX)

    print("\nStarting Game Simulation\n" + "-" * 40)
    for turn in range(1, turns + 1):
        print(f"\nTURN {turn}\n" + "-" * 30)

        for p in player_objs:
            # roll two real dice
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            dice_sum = d1 + d2

            # move on board
            p._position = (p._position + dice_sum) % board_len
            prop_name, price, rent_hint, owner = get_property_details(p)
            print(f"{p._name} rolls {d1}+{d2}={dice_sum} → lands on {prop_name}")

            # --- emit move to board (use fuzzy name mapping) ---
            try:
                emit(
                    {
                        "type": "move",
                        "playerId": p.visual_id,  # 0-based
                        "to": find_tile_index(prop_name, UK_INDEX_NORM),
                        "dice": [d1, d2],
                        "meta": {"landedOn": prop_name, "turn": turn, "player": p._name},
                    }
                )
            except Exception as e:
                print("Emit failed:", e)

            cell_type = p._list_board[p._position].get("type", "")

            # --- handle property logic ---
            if cell_type in ("road", "station", "utility"):
                dict_info = get_dict_info_safe(p, prop_name, cell_type)

                # unowned property
                if dict_info.get("belongs_to") is None:
                    try:
                        p.buy(dict_info, prop_name)
                        print(
                            f"{p._name} buys/considers {prop_name} (${dict_info.get('price', '?')})"
                        )
                        emit(
                            {
                                "type": "buy",
                                "playerId": p.visual_id,
                                "property": prop_name,
                                "price": dict_info.get("price"),
                                "success": True,
                            }
                        )
                    except Exception as e:
                        print(f"{p._name} cannot buy {prop_name} ({e})")
                        emit(
                            {
                                "type": "buy",
                                "playerId": p.visual_id,
                                "property": prop_name,
                                "price": dict_info.get("price"),
                                "success": False,
                                "reason": str(e),
                            }
                        )

                # rent payment
                else:
                    owner_name = dict_info.get("belongs_to")
                    if (
                        owner_name
                        and owner_name != p._name
                        and not dict_info.get("is_mortgaged", False)
                    ):
                        amount = safe_estimate_rent(p, dict_info)
                        if isinstance(p, SelfishPlayer):
                            predicted_p = predictor.predict_cheating(p, amount)
                            print(
                                f"[PredictiveAgent] predicts {p._name} cheating chance: {predicted_p*100:.0f}%"
                            )

                        try:
                            p.pay_rent(dict_info, amount)
                            cheated = getattr(p, "last_cheated", False)
                            predictor.observe_turn(p, amount, cheated)
                            if cheated:
                                print(
                                    f"{p._name} cheats on rent (${amount}) for {prop_name}!"
                                )
                            else:
                                print(
                                    f"{p._name} pays ${amount} rent to {owner_name}"
                                )

                            owner_visual_id = next(
                                (pl.visual_id for pl in player_objs if pl._name == owner_name),
                                None,
                            )
                            emit(
                                {
                                    "type": "rent",
                                    "from": p.visual_id,
                                    "to": owner_visual_id,
                                    "property": prop_name,
                                    "amount": amount,
                                    "cheated": cheated,
                                }
                            )
                        except Exception as e:
                            print(f"{p._name} fails to pay rent ({e})")

            else:
                print("No property action required.")

            # keep balances non-negative
            p._cash = max(0, int(getattr(p, "_cash", 0)))

            p.flush_actions()
            print(f"{p._name} balance: ${p.cash}")

        # --- fairness & metrics ---
        fairness = moderator.fairness_metric()
        pred = predictor.analyze_state(moderator)
        print(f"\nFairness score: {fairness:.3f}")
        moderator.apply_sanctions()

        # clamp everyone after sanctions too
        for pl in player_objs:
            pl._cash = max(0, int(getattr(pl, "_cash", 0)))

        print(
            f"Predictions → Bankruptcy Risk: {pred['bankruptcy_risk']}, "
            f"Cheat Likelihood: {pred['cheat_likelihood']}, "
            f"Fairness Drift: {pred['fairness_drift']:+}"
        )

        emit({"type": "fairness", "turn": turn, "score": fairness, "predictions": pred})

        # balances per player (optional but useful for sidebar)
        emit(
            {
                "type": "balance",
                "players": [
                    {"id": pl.visual_id, "name": pl._name, "cash": int(pl.cash)}
                    for pl in player_objs
                ],
            }
        )

        # slow pacing so you can watch it
        time.sleep(1)

    # --- game result summary ---
    winner = max(player_objs, key=lambda pl: pl.cash)._name
    result = {
        "winner": winner,
        "fairness": moderator.fairness_metric(),
        "efficiency": moderator.efficiency_metric(),
        "violations": sum(getattr(p, "violations", 0) for p in player_objs),
        "detected": moderator.total_detected,
        "predictive_accuracy": predictor.prediction_accuracy(),
    }

    print("\nGAME RESULT\n" + "-" * 30)
    print(f"Winner: {winner}")
    print(f"Final Fairness: {result['fairness']:.3f}")
    print(f"Efficiency: {result['efficiency']:.3f}")
    print(f"Total Violations: {result['violations']}")
    print(f"Detected Cheats: {result['detected']}")
    print(f"Predictive Accuracy: {result['predictive_accuracy']*100:.1f}%")
    print("-" * 30)

    # --- emit result event ---
    emit({"type": "result", **result})
    return result


# ---------- master experiment ----------
if __name__ == "__main__":
    # possible matchups
    matchups = {
        "Fair vs Selfish": [("FairAgent", FairPlayer), ("SelfishAgent", SelfishPlayer)],
        "Strategy vs Selfish": [("StrategyAgent", StrategyPlayer), ("SelfishAgent", SelfishPlayer)],
        "Fair vs Strategy": [("FairAgent", FairPlayer), ("StrategyAgent", StrategyPlayer)],
    }

    # randomly choose one matchup
    matchup_name, players = random.choice(list(matchups.items()))
    print(f"\n\n================= RANDOM MATCHUP: {matchup_name} =================")

    # run exactly one game with a random seed and 30 turns
    seed = random.randint(0, 999999)
    print(f"\n----- SINGLE GAME | seed={seed} -----")
    result = run_matchup(players, detection_prob=0.7, fine=100, turns=30, seed=seed)

    # print summary
    print("\n\nFINAL SUMMARY")
    print("=" * 60)
    print(f"Matchup: {matchup_name}")
    print(f"Winner: {result['winner']}")
    print(f"Fairness: {result['fairness']:.3f}")
    print(f"Efficiency: {result['efficiency']:.3f}")
    print(f"Total Violations: {result['violations']}")
    print(f"Detected Cheats: {result['detected']}")
    print(f"Predictive Accuracy: {result['predictive_accuracy']*100:.1f}%")
    print("=" * 60)

    emit({"type": "summary", "matchup": matchup_name, "result": result})
