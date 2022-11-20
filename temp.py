als hand_score >= gemiddelde_score_winnende_hand(aantal_spelers_niet_bust) + 500:
    fold
als hand_score <= gemiddelde_score_winnende_hand(aantal_spelers_niet_bust) - 500:
    raise met 4
als hand_score < 2000:
    raise met 8
als hand_score < 1000:
    als round = flop of turn:
        ga mee
    als round =river:
        ga all_in
else:
    ga mee