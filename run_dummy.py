from monosim.player import Player
from monosim.board import get_board, get_roads, get_properties, get_community_chest_cards, get_bank

if __name__ == '__main__':
    bank = get_bank()
    board, roads = get_board(), get_roads()
    props, chests = get_properties(), get_community_chest_cards()
    deck = list(chests.keys())

    p1 = Player('Player1', 1, bank, board, roads, props, deck)
    p2 = Player('Player2', 2, bank, board, roads, props, deck)

    p1.meet_other_players([p2])
    p2.meet_other_players([p1])

    for turn in range(10):  # run 10 turns for testing
        for p in [p1, p2]:
            p.play()

    print("Game finished without errors ✅")
