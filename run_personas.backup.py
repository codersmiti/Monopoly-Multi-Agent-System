from monosim.board import get_board, get_roads, get_properties, get_community_chest_cards, get_bank
from personas import FairPlayer, SelfishPlayer, Moderator, get_property_details
import numpy as np

def run_game(turns=20, detection_prob=0.7):
    bank = get_bank()
    board, roads = get_board(), get_roads()
    props, chests = get_properties(), get_community_chest_cards()
    deck = list(chests.keys())

    p1 = FairPlayer('FairAgent', 1, bank, board, roads, props, deck)
    p2 = SelfishPlayer('SelfishAgent', 2, bank, board, roads, props, deck)

    p1.meet_other_players([p2])
    p2.meet_other_players([p1])

    # reset violation counters
    p1.violations, p2.violations = 0, 0
    moderator = Moderator([p1, p2], detection_prob=detection_prob)

    players = [p1, p2]

    for turn in range(turns):
        for p in players:
            old_pos = p._position
            old_cash = p.cash
            p.play()
            new_pos = p._position
            prop_name, price, rent, owner = get_property_details(p)

            print(f"\n--- {p._name}'s turn ---")
            print(f"{p._name} moved from {old_pos} → {new_pos}")
            if price is None and rent is None:
                print(f"{p._name} landed on {prop_name}")
            else:
                print(f"{p._name} landed on {prop_name} (price ${price}, base rent ${rent}, owner={owner})")

            pre_log_count = len(p.last_actions)
            p.flush_actions()

            if p.cash != old_cash and pre_log_count == 0:
                diff = p.cash - old_cash
                if diff > 0:
                    print(f"{p._name} gains ${diff} (bonus, card, or effect)")
                else:
                    print(f"{p._name} loses ${-diff} (penalty, card, or effect)")

            print(f"{p._name} now has ${p.cash}")

        print(f"Turn {turn} Fairness: {moderator.fairness_metric():.3f}")
        moderator.apply_sanctions()

    # winner
    winner = max(players, key=lambda p: p.cash)._name
    return {
        "winner": winner,
        "fairness": moderator.fairness_metric(),
        "efficiency": sum(p.cash for p in players),
        "violations": sum(p.violations for p in players),
        "detected": moderator.total_detected
    }


if __name__ == '__main__':
    # Run batch of games
    batch_results = []
    for g in range(5):
        print(f"\n===== Starting Game {g+1} =====")
        result = run_game(turns=20, detection_prob=0.7)
        batch_results.append(result)

    games_played = len(batch_results)
    fair_wins = sum(1 for r in batch_results if r["winner"] == "FairAgent")
    selfish_wins = sum(1 for r in batch_results if r["winner"] == "SelfishAgent")
    avg_fairness = np.mean([r["fairness"] for r in batch_results])
    avg_efficiency = np.mean([r["efficiency"] for r in batch_results])
    total_violations = sum(r["violations"] for r in batch_results)
    total_detected = sum(r["detected"] for r in batch_results)

    print("\n=== Batch Summary ===")
    print(f"games_played: {games_played}")
    print(f"FairAgent_wins: {fair_wins}")
    print(f"SelfishAgent_wins: {selfish_wins}")
    print(f"avg_fairness: {avg_fairness}")
    print(f"avg_efficiency: {avg_efficiency}")
    print(f"total_violations: {total_violations}")
    print(f"total_detected: {total_detected}")
