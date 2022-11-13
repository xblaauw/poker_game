import random
from poker import Card

deck = list(Card)
random.shuffle(deck)

flop = [deck.pop() for __ in range(3)]
turn = deck.pop()
river = deck.pop()

from poker.hand import Hand, Combo, Range

list_of_hands = list(Hand)
hand1_grth_hand2 = Hand('AAd') > Hand('KK')
combo1_grth_combo2 = Combo('7s6s') > Combo('6d5d')
sorted_hands = sorted([Hand('22'), Hand('66'), Hand('76o')])
random_hand = Hand.make_random()

hand = Hand('KK')

print(Range('22+ A2+ KT+ QJ+ 32 42 52 62 72').to_ascii())
print(Range('22+ A2+ KT+ QJ+ 32 42 52 62').to_ascii())